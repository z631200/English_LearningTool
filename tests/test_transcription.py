import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import wave

import httpx
from openai import AuthenticationError, OpenAI

from transcription_maker import transcription_ctrl
from transcription_maker.audio_processing import prepare_audio
from transcription_maker.transcription import openai_transcriber


class TranscriptionTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.wav"
        with wave.open(str(self.source), "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(16000)
            audio.writeframes(b"\x00\x00" * 40000)  # 2.5 seconds
        self.original_audio = self.source.read_bytes()
        self.output = self.root / "output" / "transcription.txt"
        self.output_patch = patch.object(openai_transcriber, "TRANSCRIPT_PATH", self.output)
        self.output_patch.start()
        self.addCleanup(self.output_patch.stop)
        self.requests = []

    def client(self, handler):
        def record(request):
            self.requests.append(request)
            return handler(request)

        client = OpenAI(
            api_key="test-key", max_retries=0,
            http_client=httpx.Client(transport=httpx.MockTransport(record)),
        )
        self.addCleanup(client.close)
        return client

    def test_real_audio_chunks_preserve_source_and_cleanup(self):
        with patch.object(prepare_audio, "TRANSCRIPTION_CHUNK_SECONDS", 1):
            with prepare_audio.prepare_audio_chunks(str(self.source)) as chunks:
                self.assertEqual(len(chunks), 3)
                total_duration = 0
                for chunk in chunks:
                    self.assertLess(chunk.stat().st_size, 25_000_000)
                    probe = subprocess.run(
                        [str(prepare_audio.FFMPEG_PATH.with_name("ffprobe.exe")),
                         "-v", "error", "-show_entries", "format=duration",
                         "-of", "default=noprint_wrappers=1:nokey=1", str(chunk)],
                        check=True, capture_output=True, text=True,
                    )
                    total_duration += float(probe.stdout)
                self.assertAlmostEqual(total_duration, 2.5, delta=0.2)
                temp_dir = chunks[0].parent
        self.assertFalse(temp_dir.exists())
        self.assertEqual(self.source.read_bytes(), self.original_audio)

    def test_sdk_uploads_in_order_and_writes_plain_text(self):
        texts = ["First part.", "第二段。", "Final part."]
        client = self.client(lambda request: httpx.Response(
            200, json={"text": texts[len(self.requests) - 1], "languages": [{"code": "en"}]},
        ))
        with patch.object(prepare_audio, "TRANSCRIPTION_CHUNK_SECONDS", 1):
            path = openai_transcriber.transcribe_audio(str(self.source), client=client)
        self.assertEqual(path, self.output)
        self.assertEqual(path.read_text(encoding="utf-8"), "\n\n".join(texts) + "\n")
        self.assertEqual(len(self.requests), 3)
        for index, request in enumerate(self.requests):
            self.assertEqual(request.url.path, "/v1/audio/transcriptions")
            body = request.content
            self.assertIn(b'name="model"\r\n\r\ngpt-transcribe', body)
            self.assertIn(f'filename="chunk_{index:06d}.mp3"'.encode(), body)
            self.assertIn(b'name="languages[]"\r\n\r\nen', body)
            self.assertNotIn(b"timestamp_granularities", body)
        self.assertEqual(list(self.output.parent.glob("*.tmp")), [])
        self.assertEqual(self.source.read_bytes(), self.original_audio)

    def test_api_failure_does_not_publish_partial_transcript(self):
        self.output.parent.mkdir()
        self.output.write_text("Previous complete transcript", encoding="utf-8")

        def respond(request):
            if len(self.requests) == 1:
                return httpx.Response(200, json={"text": "Partial result"})
            return httpx.Response(401, json={"error": {"message": "Invalid key"}})

        client = self.client(respond)
        actual_prepare = prepare_audio.prepare_audio_chunks
        chunk_paths = []

        from contextlib import contextmanager

        @contextmanager
        def tracked_prepare(path):
            with actual_prepare(path) as chunks:
                chunk_paths.extend(chunks)
                yield chunks

        with patch.object(prepare_audio, "TRANSCRIPTION_CHUNK_SECONDS", 1), \
             patch.object(openai_transcriber, "prepare_audio_chunks", tracked_prepare):
            with self.assertRaises(AuthenticationError):
                openai_transcriber.transcribe_audio(str(self.source), client=client)
        self.assertEqual(self.output.read_text(encoding="utf-8"), "Previous complete transcript")
        self.assertTrue(chunk_paths)
        self.assertTrue(all(not path.exists() for path in chunk_paths))

    def test_empty_transcript_is_not_success(self):
        client = self.client(lambda request: httpx.Response(200, json={"text": "  "}))
        with self.assertRaises(ValueError):
            openai_transcriber.transcribe_audio(str(self.source), client=client)
        self.assertFalse(self.output.exists())

    def test_invalid_response_is_not_success(self):
        client = self.client(lambda request: httpx.Response(200, json={"text": None}))
        with self.assertRaises(RuntimeError):
            openai_transcriber.transcribe_audio(str(self.source), client=client)
        self.assertFalse(self.output.exists())

    def test_missing_file_never_calls_api(self):
        client = self.client(lambda request: self.fail("Unexpected API request"))
        with self.assertRaises(FileNotFoundError):
            openai_transcriber.transcribe_audio(str(self.root / "missing.mp4"), client=client)
        self.assertFalse(self.requests)

    def test_corrupt_media_never_calls_api(self):
        self.source.write_bytes(b"not an audio file")
        client = self.client(lambda request: self.fail("Unexpected API request"))
        with self.assertRaises(RuntimeError):
            openai_transcriber.transcribe_audio(str(self.source), client=client)
        self.assertFalse(self.requests)

    def test_oversized_chunk_never_calls_api(self):
        client = self.client(lambda request: self.fail("Unexpected API request"))
        with patch.object(prepare_audio, "TRANSCRIPTION_MAX_FILE_BYTES", 10):
            with self.assertRaises(ValueError):
                openai_transcriber.transcribe_audio(str(self.source), client=client)
        self.assertFalse(self.requests)

    def test_missing_key_stops_before_youtube_download(self):
        with patch.object(openai_transcriber, "load_dotenv"), \
             patch.dict(os.environ, {"OPENAI_API_KEY": ""}), \
             patch.object(transcription_ctrl, "download_audio") as download:
            with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY"):
                transcription_ctrl.process_youtube_video("https://www.youtube.com/watch?v=example")
        download.assert_not_called()

    def test_youtube_and_local_entry_points(self):
        for is_youtube in (True, False):
            with self.subTest(is_youtube=is_youtube):
                client = self.client(lambda request: httpx.Response(200, json={"text": "Hello."}))
                with patch.object(transcription_ctrl, "create_client", return_value=client), \
                     patch.object(transcription_ctrl, "download_audio", return_value=str(self.source)) as download:
                    if is_youtube:
                        self.assertTrue(transcription_ctrl.process_youtube_video(" https://example.com/video "))
                        download.assert_called_once_with("https://example.com/video")
                    else:
                        self.assertTrue(transcription_ctrl.process_local_audio(str(self.source)))
                        download.assert_not_called()
                self.assertEqual(self.output.read_text(encoding="utf-8"), "Hello.\n")

    def test_blank_youtube_url_stops_before_client_creation(self):
        with patch.object(transcription_ctrl, "create_client") as create:
            with self.assertRaises(ValueError):
                transcription_ctrl.process_youtube_video("  ")
        create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
