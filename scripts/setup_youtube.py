"""Install YouTube dependencies into the active Python environment and project."""

import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.request import urlopen
from zipfile import ZipFile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DENO_VERSION = "2.9.7"
DENO_SHA256 = "a0c3101b4158d1dfb7d6a78a7bf0f3de80c96bb423c152beec8beb22786f2238"
DENO_URL = (
    f"https://github.com/denoland/deno/releases/download/v{DENO_VERSION}/"
    "deno-x86_64-pc-windows-msvc.zip"
)
YT_DLP_REQUIREMENT = "yt-dlp[default]==2026.8.19"


def install_runtime():
    destination = PROJECT_ROOT / "transcription_maker" / "tool" / "deno.exe"
    if destination.is_file():
        result = subprocess.run([str(destination), "--version"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.startswith(f"deno {DENO_VERSION} "):
            print(f"Deno {DENO_VERSION} already installed: {destination}")
            return

    with TemporaryDirectory(prefix="youtube-setup-") as directory:
        archive = Path(directory) / "deno.zip"
        print(f"Downloading official Deno {DENO_VERSION} release...")
        with urlopen(DENO_URL, timeout=60) as response, archive.open("wb") as output:
            shutil.copyfileobj(response, output)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest != DENO_SHA256:
            raise RuntimeError("Deno archive SHA-256 does not match the official release.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(archive) as zipped, zipped.open("deno.exe") as source:
            with destination.open("wb") as output:
                shutil.copyfileobj(source, output)
    subprocess.run([str(destination), "--version"], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-only", action="store_true", help="Only install bundled Deno")
    args = parser.parse_args()
    if sys.platform != "win32":
        raise RuntimeError("This setup script installs the Windows x64 Deno runtime.")
    install_runtime()
    if not args.runtime_only:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", YT_DLP_REQUIREMENT],
            check=True,
        )
    print("YouTube setup complete. Restart the application to load updated dependencies.")


if __name__ == "__main__":
    main()
