"""Prepare bounded audio uploads without modifying the source file."""

from contextlib import contextmanager
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from config import TRANSCRIPTION_CHUNK_SECONDS, TRANSCRIPTION_MAX_FILE_BYTES

FFMPEG_PATH = Path(__file__).resolve().parents[1] / "tool" / "ffmpeg.exe"


@contextmanager
def prepare_audio_chunks(input_path: str):
    source = Path(input_path).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"找不到音訊檔案：{source}")
    if not FFMPEG_PATH.is_file():
        raise FileNotFoundError(f"找不到 FFmpeg：{FFMPEG_PATH}")

    # Ten minutes of mono 64 kbps MP3 is about 4.8 MB, below the API limit.
    with TemporaryDirectory(prefix="transcription-") as temp_dir:
        command = [
            str(FFMPEG_PATH), "-hide_banner", "-loglevel", "error", "-nostdin",
            "-i", str(source), "-map", "0:a:0", "-vn",
            "-ac", "1", "-ar", "16000", "-codec:a", "libmp3lame", "-b:a", "64k",
            "-f", "segment", "-segment_time", str(TRANSCRIPTION_CHUNK_SECONDS),
            str(Path(temp_dir) / "chunk_%06d.mp3"),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True)
        except subprocess.CalledProcessError as exc:
            detail = exc.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"音訊轉檔失敗：{detail}") from exc

        chunks = sorted(Path(temp_dir).glob("chunk_*.mp3"))
        if not chunks:
            raise ValueError("檔案中沒有可轉錄的音訊。")
        for chunk in chunks:
            if not 0 < chunk.stat().st_size < TRANSCRIPTION_MAX_FILE_BYTES:
                raise ValueError("音訊片段為空或超過 API 的 25 MB 上傳限制。")
        yield chunks
