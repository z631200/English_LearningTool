"""Download YouTube audio with an explicit JS runtime and an HLS fallback."""

import importlib.util
import os
from pathlib import Path
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory

from dotenv import load_dotenv
import yt_dlp

from config import OUTPUT_AUDIO_FILE

BASE_DIR = Path(__file__).resolve().parents[2]
TOOL_DIR = BASE_DIR / "transcription_maker" / "tool"
OUTPUT_DIR = BASE_DIR / "output_file"
SETUP_HINT = "請使用執行 app.py 的 Python 執行：python scripts/setup_youtube.py，完成後重新啟動程式。"


def find_js_runtime() -> dict:
    """Use bundled Deno first, then supported Deno/Node installations on PATH."""
    candidates = [
        ("deno", os.getenv("YOUTUBE_DENO_PATH"), (2, 3, 0)),
        ("node", os.getenv("YOUTUBE_NODE_PATH"), (22, 0, 0)),
        ("deno", str(TOOL_DIR / "deno.exe"), (2, 3, 0)),
        ("deno", shutil.which("deno"), (2, 3, 0)),
        ("node", shutil.which("node"), (22, 0, 0)),
    ]
    for name, executable, minimum in candidates:
        if not executable or not Path(executable).is_file():
            continue
        try:
            result = subprocess.run(
                [executable, "--version"], check=True, capture_output=True,
                text=True, timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        version = re.search(r"(?:deno\s+|v)(\d+)\.(\d+)\.(\d+)", result.stdout)
        if version and tuple(map(int, version.groups())) >= minimum:
            return {name: {"path": str(Path(executable).resolve())}}
    raise RuntimeError(f"找不到受支援的 JavaScript runtime（Deno >= 2.3 或 Node >= 22）。{SETUP_HINT}")


def download_audio(youtube_url: str) -> str:
    if not youtube_url or not youtube_url.strip():
        raise ValueError("請先輸入 YouTube 連結。")
    load_dotenv(BASE_DIR / ".env")
    runtime = find_js_runtime()
    if importlib.util.find_spec("yt_dlp_ejs") is None:
        raise RuntimeError(f"缺少 yt-dlp 的 EJS JavaScript 驗證套件。{SETUP_HINT}")
    if not all((TOOL_DIR / name).is_file() for name in ("ffmpeg.exe", "ffprobe.exe")):
        raise FileNotFoundError("找不到 ffmpeg.exe 或 ffprobe.exe，請確認專案的 tool 資料夾。")

    cookie_file = os.getenv("YOUTUBE_COOKIES_FILE", "").strip()
    if cookie_file:
        cookie_path = Path(cookie_file).expanduser()
        if not cookie_path.is_absolute():
            cookie_path = BASE_DIR / cookie_path
        if not cookie_path.is_file():
            raise FileNotFoundError("YOUTUBE_COOKIES_FILE 指定的 cookies 檔案不存在。")
    else:
        cookie_path = None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    final_file = OUTPUT_DIR / f"{OUTPUT_AUDIO_FILE}.mp3"
    print(f"YouTube JavaScript runtime：{next(iter(runtime))}")
    with TemporaryDirectory(prefix="youtube-", dir=OUTPUT_DIR) as directory:
        options = {
            "format": "bestaudio/best",
            "outtmpl": str(Path(directory) / f"{OUTPUT_AUDIO_FILE}.%(ext)s"),
            "ffmpeg_location": str(TOOL_DIR),
            "js_runtimes": runtime,
            "noplaylist": True,
            "check_formats": "selected",
            "socket_timeout": 30,
            "retries": 3,
            "fragment_retries": 3,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
        if cookie_path is not None:
            options["cookiefile"] = str(cookie_path)

        attempts = [
            options,
            {**options, "http_chunk_size": 1024 * 1024},
            {
                **options,
                "format": "bestaudio[protocol^=m3u8]/best[protocol^=m3u8]",
                "extractor_args": {"youtube": {"player_client": ["default", "web_safari"]}},
            },
        ]
        for index, attempt in enumerate(attempts):
            if index == 1:
                print("音訊格式無法下載，重新取得下載網址並改用分段 HTTP 請求...")
            elif index == 2:
                print("正在嘗試 YouTube HLS 格式...")
            try:
                # A new instance re-extracts short-lived media URLs on retry.
                with yt_dlp.YoutubeDL(attempt) as downloader:
                    downloader.download([youtube_url.strip()])
                break
            except yt_dlp.utils.DownloadError as exc:
                if not any(message in str(exc) for message in ("403", "Requested format is not available")):
                    raise RuntimeError("YouTube 下載失敗，請確認影片可公開播放及網路連線。") from exc
                if index == len(attempts) - 1:
                    raise RuntimeError(
                        "YouTube 仍拒絕下載。請確認影片與網路存取權限；若影片需登入，"
                        "可設定 YOUTUBE_COOKIES_FILE；若日誌指出缺少 PO Token，"
                        "請依 yt-dlp PO Token Guide 設定 provider plugin。"
                    ) from exc

        downloaded = Path(directory) / f"{OUTPUT_AUDIO_FILE}.mp3"
        if not downloaded.is_file() or downloaded.stat().st_size == 0:
            raise RuntimeError("下載程序結束，但未產生有效的 MP3 音訊檔案。")
        downloaded.replace(final_file)

    print(f"音訊下載完成：{final_file}")
    return str(final_file)
