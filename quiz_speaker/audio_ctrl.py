# quiz_speaker/audio_ctrl.py
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from .audio_maker import make_audio, make_volume_audio
import os
import pygame
import threading
import time

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_file")

speech_file_path = os.path.join(OUTPUT_DIR, "ListeningTest.mp3")
volume_test_file_path = os.path.join(OUTPUT_DIR, "VolumeTest.mp3")

# status
_play_thread: threading.Thread | None = None
_pause_ev = threading.Event()   # True = pausing
_stop_ev = threading.Event()    # True = stop
_loaded = False
_loaded_path: str | None = None
_lock = threading.Lock()

def _ensure_mixer():
    if not pygame.mixer.get_init():
        pygame.mixer.init()

def _is_busy() -> bool:
    return pygame.mixer.get_init() and pygame.mixer.music.get_busy()


# ====== call API ======
def load_audio(file_path: str):
    global _loaded, _loaded_path
    _ensure_mixer()
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到音訊檔案：{file_path}")
    pygame.mixer.music.load(file_path)
    _loaded = True
    _loaded_path = file_path

def UI_load_audio(is_quiz_audio: bool):
    path = speech_file_path if is_quiz_audio else volume_test_file_path
    load_audio(path)

def _play_loop(start_new: bool):
    _stop_ev.clear()

    if _pause_ev.is_set() and not start_new:
        # strat from pause
        pygame.mixer.music.unpause()
        _pause_ev.clear()
    else:
        # start from beginning
        pygame.mixer.music.play()
        _pause_ev.clear()

    # playing
    while not _stop_ev.is_set():
        if _pause_ev.is_set():
            pygame.mixer.music.pause()

            # wait for pause or stop
            while _pause_ev.is_set() and not _stop_ev.is_set():
                time.sleep(0.03)
            if _stop_ev.is_set():
                break
            pygame.mixer.music.unpause()

        # end play
        if not pygame.mixer.music.get_busy() and not _pause_ev.is_set():
            break

        time.sleep(0.03)

    pygame.mixer.music.stop()
    _pause_ev.clear()
    _stop_ev.clear()

def play_audio(restart: bool = False):
    if not _loaded:
        raise RuntimeError("未載入音訊")

    _ensure_mixer()
    with _lock:
        global _play_thread

        # is playing
        if _play_thread and _play_thread.is_alive():
            if _pause_ev.is_set() and not restart:
                # start from pause
                _pause_ev.clear()
            else:
                # replay
                _stop_ev.set()
                _play_thread.join(timeout=1.0)
                _stop_ev.clear()
                _play_thread = threading.Thread(target=_play_loop, args=(True,), daemon=True)
                _play_thread.start()
            return

        start_new = True if restart else (not _pause_ev.is_set())
        _play_thread = threading.Thread(target=_play_loop, args=(start_new,), daemon=True)
        _play_thread.start()

def pause_audio():
    if _is_busy():
        _pause_ev.set()

def stop_audio():
    with _lock:
        global _play_thread
        _stop_ev.set()
        if _play_thread and _play_thread.is_alive():
            _play_thread.join(timeout=1.0)
        _play_thread = None
        _pause_ev.clear()
        _stop_ev.clear()
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()

# check status
def is_playing() -> bool:
    return _is_busy() and not _pause_ev.is_set()

def is_paused() -> bool:
    return _pause_ev.is_set()

def is_loaded() -> bool:
    return _loaded and (_loaded_path is not None)
