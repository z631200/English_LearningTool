import asyncio
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
from pathlib import Path
import random

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
api_key = os.getenv("OPENAI_API_KEY")

client = AsyncOpenAI(api_key=api_key)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_file")

async def read_vector_file():
    stores = []
    async for store in client.vector_stores.list():
        stores.append(store)

    existing = next((s for s in stores if s.name == "SE_Class"), None)

    if existing:
        vector_store_id = existing.id
        print("✅ 已存在 vector store:", vector_store_id)
        return vector_store_id
    else:
        print("⛔ 尚未建立 vector store，請先上傳檔案")
        return None


async def write_to_test_file(content: str):
    try:
        file_path = os.path.join(OUTPUT_DIR, "NormalTest.txt")
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

async def generate_question_from_text(vector_store_id, quiz_count: str, input_prompt: str = ""):
    answer_pattern = random_choices(int(quiz_count))
    system_prompt = (
        "You are a university Software Engineering professor. "
        "Your task is to create multiple-choice quiz questions that test students’ understanding "
        "of materials stored in a specified vector store. "
        "Each question must be answerable *only* using information contained in the vector store files. "
        "Do not use external knowledge or assumptions. "
        "All questions should reflect the content, terminology, and examples found in the vector store documents. "
        "and that the correct answer positions are randomized naturally across the quiz."
    )

    user_prompt = (
        f"The correct answers for the questions should be: {answer_pattern}\n\n"
        f"{input_prompt}\n\n"
        f"Based on the materials retrieved from the specified vector store about Software Engineering, "
        f"generate {quiz_count} single-choice questions in the following format:\n\n"
        f"Question 1:\n<question based on vector store content>\n\n"
        f"A) ...\nB) ...\nC) ...\nD) ...\nAnswer: A\n\n"
        f"Question 2:\n...\n\nAnswer: B\n\n"
        f"The questions should assess understanding of software engineering concepts, "
        f"principles, methodologies, or examples discussed in the retrieved documents.\n\n"
        f"Requirements:\n"
        f"- Each answer must be directly supported by the content of the vector store.\n"
        f"- Use expressions like 'According to the material' or 'In the lecture notes' instead of 'According to the vector store'.\n"
        f"- Do NOT output explanations or commentary — only the questions and answers in the exact format.\n"
        f"- Ensure that the correct answers (A, B, C, D) are *well distributed* and not repetitive. "
        f"For example, across {quiz_count} questions, each letter should appear roughly the same number of times.\n"
    )

    try:
        print("⏳ 正在產生題目文字檔...")
        response = await client.responses.create(
            model="gpt-4.1-mini",
            instructions=system_prompt,
            input=[
                {"role": "user", "content": user_prompt},
                # {"role": "user", "content": input_prompt},
            ],
            tools=[{
                "type": "file_search",
                "vector_store_ids": [vector_store_id],
                }],
            tool_choice="auto",
        )
        
        result = response.output_text
        print("✅ 題目文字檔已完成...")
        # print(result)
        if isinstance(result, str):
            await write_to_test_file(result)
        else:
            print("API 回傳的結果格式不正確，為 None 或其他型別。")

    except AttributeError:
        result = None
        print("⚠️ 無法取得 output_text 屬性")
    except Exception as e:
        print(f"API error: {str(e)}")

async def test_func(vector_store_id: str):
    try:
        print("⏳ 正在向向量庫檢索並產生回覆...")
        response = await client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": ""},
                {"role": "user", "content": "tell me what is in the vector store and the content of the files"},
            ],
            tools=[{
                "type": "file_search",
                "vector_store_ids": [vector_store_id],
            }],
            tool_choice="auto",
        )

        # 取文字輸出（新版 SDK 多半有 output_text；保留退路以防沒有）
        try:
            result_text = response.output_text
        except AttributeError:
            # 後備做法：手動拼接 output 區段中的文字
            result_text = ""
            for item in getattr(response, "output", []) or []:
                for c in getattr(item, "content", []) or []:
                    if getattr(c, "type", "") in ("output_text", "text"):
                        # c 可能是物件或 dict，兩者都處理
                        text_val = getattr(c, "text", None) or (c.get("text") if isinstance(c, dict) else None)
                        if text_val:
                            result_text += text_val + "\n"

        if result_text and result_text.strip():
            print("✅ 完成。")
            print(f"API return: {result_text}")
            # 若你有自訂寫檔函式，維持不變
            await write_to_test_file(result_text)
        else:
            print("⚠️ 沒有取得可用文字輸出（可能只有引用/工具呼叫內容）。")
    except Exception as e:
        print(f"API error: {str(e)}")


async def core(quiz_count, input_prompt=""):
    try:
        vector_store_id = await read_vector_file()
        if vector_store_id:
            await generate_question_from_text(vector_store_id, quiz_count, input_prompt)
            # await test_func(vector_store_id)
            return f"✅ 已產生 {quiz_count} 題"
        else:
            print("請先上傳檔案以建立 vector store。")
            return "❌ 尚未建立 vector store，請先上傳檔案"
    except Exception as e:
        print(f"發生錯誤: {str(e)}")
        return f"❌ 發生錯誤: {str(e)}"

# async def main():
#     quiz_count = str(2)
#     try:
#         vector_store_id = await read_vector_file()
#         if vector_store_id:
#             await generate_question_from_text(vector_store_id, quiz_count)
#             # await test_func(vector_store_id)
#         else:
#             print("請先上傳檔案以建立 vector store。")
#     except Exception as e:
#         print(f"發生錯誤: {str(e)}")

if __name__ == "__main__":
    asyncio.run(core(2))
