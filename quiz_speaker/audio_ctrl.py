# quiz_speaker/audio_ctrl.py
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from .audio_maker import make_audio, make_volume_audio
import os
import pygame
import threading
import time

# ── env / client（保留，以便外部使用 make_audio / make_volume_audio） ──
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# ── 路徑 ──
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_file")

speech_file_path = os.path.join(OUTPUT_DIR, "ListeningTest.mp3")
volume_test_file_path = os.path.join(OUTPUT_DIR, "VolumeTest.mp3")

# ── 狀態（單一播放緒 + 事件控制） ──
_play_thread: threading.Thread | None = None
_pause_ev = threading.Event()   # True = 暫停中
_stop_ev = threading.Event()    # True = 要停止
_loaded = False
_loaded_path: str | None = None
_lock = threading.Lock()        # 保護 _play_thread 與狀態

def _ensure_mixer():
    if not pygame.mixer.get_init():
        pygame.mixer.init()

def _is_busy() -> bool:
    return pygame.mixer.get_init() and pygame.mixer.music.get_busy()

# ─────────────────────────────────────────
# 對外 API：載入 / 播放控制（單一播放緒）
# ─────────────────────────────────────────
def load_audio(file_path: str):
    """只載入，不播放。"""
    global _loaded, _loaded_path
    _ensure_mixer()
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到音訊檔案：{file_path}")
    pygame.mixer.music.load(file_path)
    _loaded = True
    _loaded_path = file_path

def UI_load_audio(is_quiz_audio: bool):
    """只載入（UI 友善）。"""
    path = speech_file_path if is_quiz_audio else volume_test_file_path
    load_audio(path)

def _play_loop(start_new: bool):
    """
    單一播放緒：
    - start_new=True → 從頭播放
    - start_new=False → 若暫停就繼續，否則保持現況（若未播放則從頭）
    """
    # 啟動前清除停止事件
    _stop_ev.clear()

    # 決定如何開始
    if _pause_ev.is_set() and not start_new:
        # 從暫停繼續
        pygame.mixer.music.unpause()
        _pause_ev.clear()
    else:
        # 從頭播放
        pygame.mixer.music.play()
        _pause_ev.clear()

    # 主循環：直到被停止或播完
    while not _stop_ev.is_set():
        if _pause_ev.is_set():
            pygame.mixer.music.pause()
            # 等待恢復或停止
            while _pause_ev.is_set() and not _stop_ev.is_set():
                time.sleep(0.03)
            if _stop_ev.is_set():
                break
            pygame.mixer.music.unpause()

        # 播放完畢（且非暫停）→ 離開
        if not pygame.mixer.music.get_busy() and not _pause_ev.is_set():
            break

        time.sleep(0.03)

    # 收尾
    pygame.mixer.music.stop()
    _pause_ev.clear()
    _stop_ev.clear()

def play_audio(restart: bool = False):
    """
    合併原 unpause 行為：
    - 若目前「暫停中」且 restart=False → 直接繼續播放
    - 其他情況 → 從頭播放
    ◉ 僅保留一條播放緒：若緒已存在且活著，就僅調整狀態（暫停/繼續），不重啟緒。
    """
    if not _loaded:
        raise RuntimeError("尚未載入音訊，請先呼叫 load_audio()/UI_load_audio()")

    _ensure_mixer()
    with _lock:
        global _play_thread

        # 若有播放緒在跑
        if _play_thread and _play_thread.is_alive():
            if _pause_ev.is_set() and not restart:
                # 從暫停繼續
                _pause_ev.clear()  # 讓緒循環解除暫停，自動 unpause
            else:
                # 強制重新播放：先停掉現有播放，緒會正常結束
                _stop_ev.set()
                _play_thread.join(timeout=1.0)
                _stop_ev.clear()
                # 開新的播放緒
                _play_thread = threading.Thread(target=_play_loop, args=(True,), daemon=True)
                _play_thread.start()
            return

        # 沒有播放緒：依參數啟動新播放
        start_new = True if restart else (not _pause_ev.is_set())
        _play_thread = threading.Thread(target=_play_loop, args=(start_new,), daemon=True)
        _play_thread.start()

def pause_audio():
    """暫停播放（若正在播）。"""
    if _is_busy():
        _pause_ev.set()

def stop_audio():
    """停止播放並回收播放緒。"""
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

# ─────────────────────────────────────────
# 查詢狀態
# ─────────────────────────────────────────
def is_playing() -> bool:
    """正在播放且非暫停"""
    return _is_busy() and not _pause_ev.is_set()

def is_paused() -> bool:
    return _pause_ev.is_set()

def is_loaded() -> bool:
    return _loaded and (_loaded_path is not None)
