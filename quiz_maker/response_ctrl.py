import asyncio
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
import random

load_dotenv(find_dotenv(), override=True)
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("環境變數 OPENAI_API_KEY 未設定")
client = AsyncOpenAI(api_key=api_key)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_file")

async def read_txt_file(file_path: str) -> str:
    # read transcription
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "⛔ 題目檔案不存在"
    except Exception as e:
        return f"⛔ 無法讀取題目檔案，原因: {str(e)}"

async def write_to_listening_test_file(content: str):
    try:
        file_path = os.path.join(OUTPUT_DIR, "ListeningTest.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"內容已寫入 {file_path}")
    except Exception as e:
        print(f"寫入檔案時發生錯誤: {str(e)}")

def random_choices(n: int):
    options = ['a', 'b', 'c', 'd']
    result = [random.choice(options) for _ in range(n)]
    random.shuffle(result)
    # print("Correct answer pattern:", ",".join(result))
    return ",".join(result)

async def generate_question_from_text(text: str, quiz_count: str, input_prompt: str = ""):
    answer_pattern = random_choices(int(quiz_count))
    system_prompt = "You are an assistant that generates English quiz questions based on a video clip used in English listening tests."
    user_prompt = (
        f"The correct answers for the questions should be: {answer_pattern}\n\n"
        f"{input_prompt}\n\n"
        f"Based on the following transcript of a video used in an English listening comprehension test, "
        f"generate {quiz_count} multiple-choice questions in the following format:\n\n"
        f"Question 1:\n<question based on what listeners hear>\n\nA) ...\nB) ...\nC) ...\nD) ...\n\n"
        f"Question 2:\n...\n\nAnswer: A,B,...\n\n"
        f"The questions must test understanding of spoken content in the video, "
        f"such as the speaker's tone, intention, key details, or implied meaning.\n"
        f"Use expressions like 'According to the video' instead of 'According to the transcript' to reflect a listening context.\n"
        f"Only output the questions and answers in this format, no explanation.\n\n"
        f"Transcript:\n{text}"

    )

    try:
        if not api_key:
             raise RuntimeError("OPENAI_API_KEY not found. Check your .env and load_dotenv path.")

        print("⏳ 正在產生題目文字檔...")
        response = await client.responses.create(
            model="gpt-4.1-mini",
            instructions=system_prompt,
            input=[
                {"role": "user", "content": user_prompt},
                # {"role": "user", "content": input_prompt}
            ]
        )
        result = response.output_text
        print("✅ 題目文字檔已完成...")
        # print(result)

        if isinstance(result, str):
            await write_to_listening_test_file(result)
        else:
            print("API 回傳的結果格式不正確，為 None 或其他型別。")
    except Exception as e:
        print(f"API error: {str(e)}")

async def core(quiz_count, input_prompt=""):
    file_path = os.path.join(OUTPUT_DIR, "transcription.txt")
    content = await read_txt_file(file_path)
    if "Error" not in content and "not found" not in content:
        # quiz_count = input("\n請輸入題數：")
        await generate_question_from_text(content, quiz_count, input_prompt)
    else:
        print("Error:", content)

if __name__ == "__main__":
    asyncio.run(core(2))
