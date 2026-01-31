from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
from pydub import AudioSegment
from tqdm import tqdm
import os
import re

load_dotenv(find_dotenv(), override=True)
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_file")
input_file_path = os.path.join(OUTPUT_DIR, "ListeningTest.txt") 


def make_volume_audio():
    print("\n⏳ 正在產生音量測試語音檔...")
    volume_test_file_path = os.path.join(OUTPUT_DIR, "VolumeTest.mp3")
    try:
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="coral",
            input="Please adjust the volume. This is a test audio file.",
            speed=0.8,
        ) as response:
            response.stream_to_file(volume_test_file_path)
            print("✅ 測試語音檔已完成...")
            print(f"音訊已儲存至 {volume_test_file_path}")
        return True, None
    except Exception as e:
        print(f"❌ 錯誤: {str(e)}")
        return False, str(e)

def make_audio():
    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # filter Answer 
        filtered_lines = [line.strip() for line in lines if not line.strip().startswith("Answer:")]
        # split quiz
        question_list = split_question("\n".join(filtered_lines))

    except FileNotFoundError:
        print("找不到 ListeningTest.txt 檔案")
        return False, "找不到題目文字檔案"
    except Exception as e:
        print(f"生成語音檔案發生錯誤: {str(e)}")
        return False, str(e)

    audio_paths = []
    print("🔊 題目語音檔產生中...")
    for i, question in tqdm(enumerate(question_list, start=1), desc="進度", unit="題", total=len(question_list)):
        question_file_path = os.path.join(OUTPUT_DIR, f"Question_{i}.mp3")

        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="coral",
            input=question,
            speed=0.9,
            instructions="Please speak clearly and articulate every word. "
                        "Maintain a steady pace and proper enunciation for better understanding.",
        ) as response:
            response.stream_to_file(question_file_path)

        audio_paths.append(question_file_path)

    print("✅ 所有題目語音檔產生完成！")
    merge_audio(audio_paths)

    return True, None


def split_question(input_text):
    # split by "Question X:"
    question_splits = re.split(r'(Question \d+:)', input_text)    
    question_list = []
    for i in range(1, len(question_splits), 2):
        question = question_splits[i] + question_splits[i + 1]
        question_list.append(question.strip())

    return question_list


def merge_audio(audio_paths, delay_seconds=3):
    combined = AudioSegment.empty()
    silence = AudioSegment.silent(duration=delay_seconds * 1000)

    for path in audio_paths:
        audio = AudioSegment.from_mp3(path)
        combined += audio + silence

    output_path = os.path.join(OUTPUT_DIR, "ListeningTest.mp3")
    combined.export(output_path, format="mp3")
    print(f"✅ 合併完成，儲存於: {output_path}")

    for path in audio_paths:
        try:
            os.remove(path)
        except Exception as e:
            print(f"刪除檔案失敗 {path}: {e}")



