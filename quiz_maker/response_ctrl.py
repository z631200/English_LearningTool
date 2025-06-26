import asyncio
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
api_key = os.getenv("OPENAI_API_KEY")

client = AsyncOpenAI(api_key=api_key)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_file")

async def read_txt_file(file_path: str) -> str:
    """非同步讀取 txt 檔案內容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "quiz_maker: File not found."
    except Exception as e:
        return f"quiz_maker: Error reading file: {str(e)}"

async def write_to_listening_test_file(content: str):
    try:
        file_path = os.path.join(OUTPUT_DIR, "ListeningTest.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"內容已寫入 {file_path}")
    except Exception as e:
        print(f"寫入檔案時發生錯誤: {str(e)}")

async def generate_question_from_text(text: str, quiz_count: str):
    """使用 Chat Completions API 根據文字產生多題英文題目"""
    system_prompt = "You are an assistant that generates English quiz questions based on text input."
    user_prompt = (
        f"Based on the following transcript of an English listening audio, generate {quiz_count} listening comprehension quiz questions "
        f"(multiple-choice) in the following format:\n\n"
        f"Question 1:\n<question based on what listeners hear>\n\nA) ...\nB) ...\nC) ...\nD) ...\n\n"
        f"Question 2:\n...\n\nAnswer: A,B,...\n\n"
        f"The questions must test understanding of spoken content, such as speaker's intention, tone, specific details, or implied meaning.\n"
        f"Only output the questions and answers in this format, no explanation.\n\n"
        f"Transcript:\n{text}"
    )


    try:
        print("正在產生題目文字檔...")
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        result = response.choices[0].message.content
        print("題目文字檔已完成...")
        # print(result)

        if isinstance(result, str):
            await write_to_listening_test_file(result)
        else:
            print("API 回傳的結果格式不正確，為 None 或其他型別。")
    except Exception as e:
        print(f"API error: {str(e)}")

async def core():
    file_path = os.path.join(OUTPUT_DIR, "transcription.txt")
    content = await read_txt_file(file_path)
    if "Error" not in content and "not found" not in content:
        quiz_count = input("\n請輸入題數：")
        await generate_question_from_text(content,quiz_count)
    else:
        print("Error:", content)

if __name__ == "__main__":
    asyncio.run(core())
