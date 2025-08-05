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


exit_flag = False
paused = False
playing = False
user_command = None


def audio_test_volume():
    make_volume_audio()
    load_audio(volume_test_file_path)
    input("➡️  按下 Enter 鍵開始播放音訊...")

    while True:
        t = threading.Thread(target=audio_thread)
        t.start()

        while pygame.mixer.music.get_busy():
            time.sleep(0.5)

        replay = input("是否再播放一次測試音檔？(y/n)： ").strip().lower()
        if replay != "y":
            print("關閉音量測試...")
            break
    return


def load_audio(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)

def play_audio():
    global playing
    pygame.mixer.music.play()
    playing = True

def pause_audio():
    global paused
    pygame.mixer.music.pause()
    paused = True

def unpause_audio():
    global paused
    pygame.mixer.music.unpause()
    paused = False

def stop_audio():
    global paused, playing
    pygame.mixer.music.stop()
    paused = False
    playing = False

def audio_thread():
    global playing, exit_flag
    play_audio()
    while playing:
        if not pygame.mixer.music.get_busy() and not paused:
            break
        time.sleep(0.5)
    playing = False
    exit_flag = True
    # print("exit_flag 已設置為 True，音訊播放結束。")

def user_input_thread():
    global user_command, exit_flag
    while not exit_flag:
        try:
            command = input("輸入指令 (p: 暫停, r: 繼續, s: 停止, q: 離開程式)： ").strip().lower()
            user_command = command
        except EOFError:
            break

def handle_commands_thread():
    global exit_flag, user_command
    while not exit_flag:
        if user_command:
            command = user_command
            user_command = None

            if command == "p":
                pause_audio()
            elif command == "r":
                unpause_audio()
            elif command == "s":
                stop_audio()
                print("播放已停止。")
                exit_flag = True
                break
            elif command == "q":
                stop_audio()
                print("離開程式。")
                exit_flag = True
                break
            else:
                print(f"未知指令：{command}")

        if not pygame.mixer.music.get_busy() and not paused:
            exit_flag = True
            break

        time.sleep(0.1)


def core(full_execution=True):
    global exit_flag
    exit_flag = False

    if full_execution:
        make_audio()

    use_command = input("\n是否啟用指令控制？(y/n)： ").lower()
    if use_command != "y":
        print("將自動播放音訊...")
    else:
        print("進入指令控制模式，可輸入指令控制。")
        print("p: 暫停, r: 繼續, s: 停止, q: 離開")

    if not os.path.exists(speech_file_path):
        print(f"錯誤：找不到音訊檔案 {speech_file_path}。請先生成題目語音檔。")
        return

    load_audio(speech_file_path)
    input("➡️  按下 Enter 鍵開始播放音訊...")

    # 啟動播放音訊
    audio_t = threading.Thread(target=audio_thread, daemon=True)
    audio_t.start()

    # 啟動輸入與控制指令
    if use_command == "y":
        threading.Thread(target=user_input_thread, daemon=True).start()
        threading.Thread(target=handle_commands_thread, daemon=True).start()

    # 主執行緒等待退出
    while not exit_flag:
        time.sleep(0.2)

    print("\n✅ 音訊播放結束，若停止請按 Enter 繼續。")


def test_func():
    # make_audio()
    return


if __name__ == "__main__":
    try:
        core()
    except KeyboardInterrupt:
        print("\n已偵測到 Ctrl+C，程式結束。")
        stop_audio()
