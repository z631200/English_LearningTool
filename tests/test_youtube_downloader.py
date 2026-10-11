import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import yt_dlp

from transcription_maker.downloader import audio_downloader


class YouTubeDownloaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / "output"
        self.tool = self.root / "tool"
        self.tool.mkdir()
        for name in ("ffmpeg.exe", "ffprobe.exe"):
            (self.tool / name).touch()
        patches = [
            patch.object(audio_downloader, "OUTPUT_DIR", self.output),
            patch.object(audio_downloader, "TOOL_DIR", self.tool),
            patch.object(audio_downloader, "BASE_DIR", self.root),
            patch.object(audio_downloader, "load_dotenv"),
            patch.dict(os.environ, {"YOUTUBE_COOKIES_FILE": "", "YOUTUBE_DENO_PATH": "", "YOUTUBE_NODE_PATH": ""}),
        ]
        for setting in patches:
            setting.start()
            self.addCleanup(setting.stop)
        self.runtime = {"deno": {"path": str(self.tool / "deno.exe")}}

    def fake_downloader(self, outcomes):
        calls = []

        class FakeDownloader:
            def __init__(inner, options):
                inner.options = options
                calls.append(options)

            def __enter__(inner):
                return inner

            def __exit__(inner, *args):
                return False

            def download(inner, urls):
                self.assertEqual(urls, ["https://www.youtube.com/watch?v=example"])
                outcome = outcomes[len(calls) - 1]
                if isinstance(outcome, Exception):
                    # Leave a partial file to verify cleanup on success/failure.
                    Path(inner.options["outtmpl"].replace("%(ext)s", "webm.part")).write_bytes(b"partial")
                    raise outcome
                if outcome:
                    Path(inner.options["outtmpl"].replace("%(ext)s", "mp3")).write_bytes(b"new audio")
                return 0

        return FakeDownloader, calls

    def download_with(self, outcomes):
        fake, calls = self.fake_downloader(outcomes)
        with patch.object(audio_downloader, "find_js_runtime", return_value=self.runtime), \
             patch.object(audio_downloader.importlib.util, "find_spec", return_value=object()), \
             patch.object(audio_downloader.yt_dlp, "YoutubeDL", fake):
            result = audio_downloader.download_audio(" https://www.youtube.com/watch?v=example ")
        return result, calls

    def test_success_enables_js_and_removes_temp_files(self):
        result, calls = self.download_with([True])
        self.assertEqual(Path(result).read_bytes(), b"new audio")
        self.assertEqual(calls[0]["js_runtimes"], self.runtime)
        self.assertTrue(calls[0]["noplaylist"])
        self.assertEqual(calls[0]["check_formats"], "selected")
        self.assertEqual(list(self.output.iterdir()), [Path(result)])

    def test_403_reextracts_with_bounded_http_requests(self):
        result, calls = self.download_with([yt_dlp.utils.DownloadError("HTTP Error 403"), True])
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1]["http_chunk_size"], 1024 * 1024)
        self.assertEqual(Path(result).read_bytes(), b"new audio")
        self.assertEqual(list(self.output.iterdir()), [Path(result)])

    def test_hls_fallback_keeps_default_clients(self):
        error = yt_dlp.utils.DownloadError("Requested format is not available")
        _, calls = self.download_with([error, error, True])
        self.assertEqual(len(calls), 3)
        self.assertIn("m3u8", calls[2]["format"])
        self.assertEqual(calls[2]["extractor_args"]["youtube"]["player_client"], ["default", "web_safari"])

    def test_failed_download_keeps_old_audio_and_cleans_partial_files(self):
        self.output.mkdir()
        previous = self.output / "audio.mp3"
        previous.write_bytes(b"old audio")
        error = yt_dlp.utils.DownloadError("HTTP Error 403")
        with self.assertRaisesRegex(RuntimeError, "PO Token"):
            self.download_with([error, error, error])
        self.assertEqual(previous.read_bytes(), b"old audio")
        self.assertEqual(list(self.output.iterdir()), [previous])

    def test_other_errors_are_not_retried(self):
        fake, calls = self.fake_downloader([yt_dlp.utils.DownloadError("Video unavailable")])
        with patch.object(audio_downloader, "find_js_runtime", return_value=self.runtime), \
             patch.object(audio_downloader.importlib.util, "find_spec", return_value=object()), \
             patch.object(audio_downloader.yt_dlp, "YoutubeDL", fake):
            with self.assertRaises(RuntimeError):
                audio_downloader.download_audio("https://www.youtube.com/watch?v=example")
        self.assertEqual(len(calls), 1)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_missing_mp3_is_not_success(self):
        with self.assertRaises(RuntimeError):
            self.download_with([False])
        self.assertEqual(list(self.output.iterdir()), [])

    def test_missing_ejs_fails_before_network(self):
        with patch.object(audio_downloader, "find_js_runtime", return_value=self.runtime), \
             patch.object(audio_downloader.importlib.util, "find_spec", return_value=None), \
             patch.object(audio_downloader.yt_dlp, "YoutubeDL") as downloader:
            with self.assertRaisesRegex(RuntimeError, "setup_youtube.py"):
                audio_downloader.download_audio("https://www.youtube.com/watch?v=example")
        downloader.assert_not_called()

    def test_runtime_version_validation_and_node_fallback(self):
        (self.tool / "deno.exe").touch()
        node = self.tool / "node.exe"
        node.touch()
        with patch.object(audio_downloader.shutil, "which", side_effect=lambda name: str(node) if name == "node" else None), \
             patch.object(audio_downloader.subprocess, "run", side_effect=[
                 SimpleNamespace(stdout="deno 2.2.0 (stable)"),
                 SimpleNamespace(stdout="v22.12.0\n"),
             ]):
            self.assertEqual(audio_downloader.find_js_runtime(), {"node": {"path": str(node.resolve())}})

    def test_missing_or_broken_runtime_has_setup_instruction(self):
        (self.tool / "deno.exe").touch()
        with patch.object(audio_downloader.shutil, "which", return_value=None), \
             patch.object(audio_downloader.subprocess, "run", side_effect=subprocess.TimeoutExpired("deno", 10)):
            with self.assertRaisesRegex(RuntimeError, "setup_youtube.py"):
                audio_downloader.find_js_runtime()

    def test_optional_cookie_file_resolves_relative_to_project(self):
        cookie_file = self.root / "cookies.txt"
        cookie_file.touch()
        with patch.dict(os.environ, {"YOUTUBE_COOKIES_FILE": "cookies.txt"}):
            _, calls = self.download_with([True])
        self.assertEqual(calls[0]["cookiefile"], str(cookie_file))


if __name__ == "__main__":
    unittest.main()
