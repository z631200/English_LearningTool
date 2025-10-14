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

async def read_vector_file():
    stores = client.vector_stores.list().data
    existing = next((s for s in stores if s.name == "SE_Class"), None)

    if existing:
        vector_store_id = existing.id
        print("✅ 已存在 vector store:", vector_store_id)
    else:
        print("⛔ 尚未建立 vector store，請先上傳檔案")
        return None
    
    return vector_store_id


async def write_to_test_file(content: str):
    try:
        file_path = os.path.join(OUTPUT_DIR, "NormalTest.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"內容已寫入 {file_path}")
    except Exception as e:
        print(f"寫入檔案時發生錯誤: {str(e)}")


async def generate_question_from_text(vector_store_id, quiz_count: str):
    system_prompt = (
        "You are a university Software Engineering professor. "
        "Your role is to create multiple-choice quiz questions that test students’ understanding "
        "of materials stored in a specified vector store. "
        "Each question must be answerable *only* using information contained in the vector store files. "
        "Do not use external knowledge or assumptions. "
        "All questions should reflect the content, terminology, and examples found in the vector store documents."
    )

    user_prompt = (
        f"Based on the materials retrieved from the specified vector store about Software Engineering, "
        f"generate {quiz_count} single-choice questions in the following format:\n\n"
        f"Question 1:\n<question based on vector store content>\n\nA) ...\nB) ...\nC) ...\nD) ...\nAnswer: A\n\n"
        f"Question 2:\n...\n\nAnswer: B\n\n"
        f"The questions should assess understanding of software engineering concepts, "
        f"principles, methodologies, or examples discussed in the retrieved documents.\n"
        f"Each answer must be directly supported by the content of the vector store — "
        f"do not create answers not found within it.\n"
        f"Use expressions like 'According to the material' or 'In the lecture notes' "
        f"instead of 'According to the vector store'.\n"
        f"Only output the questions and answers in this format, with no explanations or extra text.\n\n"
    )




    try:
        print("⏳ 正在產生題目文字檔...")
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            tools=[{"type": "file_search"}],
            tool_choice="auto",
            file_search={"vector_store_ids": [vector_store_id]},
        )
        result = response.choices[0].message.content
        print("✅ 題目文字檔已完成...")
        # print(result)

        if isinstance(result, str):
            await write_to_test_file(result)
        else:
            print("API 回傳的結果格式不正確，為 None 或其他型別。")
    except Exception as e:
        print(f"API error: {str(e)}")


async def core(quiz_count):
    try:
        vector_store_id = await read_vector_file()
        if vector_store_id:
            await generate_question_from_text(vector_store_id, quiz_count)
        else:
            print("請先上傳檔案以建立 vector store。")
    except Exception as e:
        print(f"發生錯誤: {str(e)}")

if __name__ == "__main__":
    asyncio.run(core())
