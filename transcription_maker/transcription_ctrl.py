"""Local media and YouTube speech-to-text entry points."""

from .downloader.audio_downloader import download_audio
from .transcription.openai_transcriber import create_client, transcribe_audio


def process_local_audio(audio_path: str) -> bool:
    with create_client() as client:
        transcribe_audio(audio_path, client=client)
    return True


def process_youtube_video(youtube_url: str) -> bool:
    if not youtube_url or not youtube_url.strip():
        raise ValueError("請先輸入 YouTube 連結。")
    with create_client() as client:
        audio_path = download_audio(youtube_url.strip())
        transcribe_audio(audio_path, client=client)
    return True


def core():
    print("1. 處理本地音訊或影片檔案")
    print("2. 處理 YouTube 影片")
    choice = input("請輸入選項 (1/2)：").strip()
    try:
        if choice == "1":
            process_local_audio(input("請輸入檔案路徑：").strip())
        elif choice == "2":
            process_youtube_video(input("請輸入 YouTube 連結：").strip())
        else:
            print("無效的選項")
    except Exception as exc:
        print(f"轉錄失敗：{exc}")


if __name__ == "__main__":
    core()
