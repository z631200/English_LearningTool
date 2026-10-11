"""Transcribe audio with OpenAI and save a plain-text transcript."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from dotenv import load_dotenv
from openai import OpenAI

from config import TRANSCRIPTION_MODEL
from ..audio_processing.prepare_audio import prepare_audio_chunks

BASE_DIR = Path(__file__).resolve().parents[2]
TRANSCRIPT_PATH = BASE_DIR / "output_file" / "transcription.txt"


def create_client() -> OpenAI:
    load_dotenv(BASE_DIR / ".env")
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("請在專案根目錄的 .env 或環境變數設定 OPENAI_API_KEY。")
    return OpenAI(api_key=api_key)


def transcribe_audio(audio_path: str, *, client: OpenAI) -> Path:
    """Publish a transcript only after all chunks have transcribed successfully."""
    texts = []
    with prepare_audio_chunks(audio_path) as chunks:
        for index, chunk in enumerate(chunks, start=1):
            print(f"正在使用 {TRANSCRIPTION_MODEL} 轉錄：{index}/{len(chunks)}")
            with chunk.open("rb") as audio_file:
                result = client.audio.transcriptions.create(
                    model=TRANSCRIPTION_MODEL,
                    file=audio_file,
                    extra_body={"languages": ["en"]},
                )
            if not isinstance(result.text, str):
                raise RuntimeError("轉錄 API 未回傳有效的文字結果。")
            if result.text.strip():
                texts.append(result.text.strip())

    if not texts:
        raise ValueError("未辨識到語音，請確認音訊內容。")

    TRANSCRIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=TRANSCRIPT_PATH.parent,
            suffix=".tmp", delete=False,
        ) as output:
            temporary_path = Path(output.name)
            output.write("\n\n".join(texts) + "\n")
        temporary_path.replace(TRANSCRIPT_PATH)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    print(f"轉錄結果已保存至：{TRANSCRIPT_PATH}")
    return TRANSCRIPT_PATH
