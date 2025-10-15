from tkinter import filedialog
from tkinter import Tk
import asyncio
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("環境變數 OPENAI_API_KEY 未設定")

client = AsyncOpenAI(api_key=api_key)

def select_file():
    root = Tk()
    root.withdraw()  # 隱藏主視窗
    file_path = filedialog.askopenfilename(
        title="選擇檔案",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )
    print("選擇的檔案：", file_path)
    return file_path

async def create_vector_store():
    page = await client.vector_stores.list()
    stores = page.data  # 這時候才有 .data
    existing = next((s for s in stores if s.name == "SE_Class"), None)

    if existing:
        vector_store_id = existing.id
        print("✅ 已存在 vector store:", vector_store_id)
    else:
        new_store = await client.vector_stores.create(name="SE_Class")
        vector_store_id = new_store.id
        print("🆕 建立新的 vector store:", vector_store_id)

    return vector_store_id

async def upload_file_to_vector_store(vector_store_id: str):
    file_path = select_file()
    if not file_path:
        print("⚠️ 未選擇檔案，已跳過上傳")
        return

    # 注意：這個呼叫同樣需要 await
    with open(file_path, "rb") as f:
        upload = await client.vector_stores.files.upload(
            vector_store_id=vector_store_id,
            file=f
        )
    print(f"✅ 檔案已上傳到 Vector Store ({vector_store_id})：{upload.id}")

async def delete_vector_store_all(target_name: str = "SE_Class"):
    page = await client.vector_stores.list()
    stores = page.data

    # 找出所有同名 vector store
    matches = [s for s in stores if s.name == target_name]

    if not matches:
        print(f"⛔ 找不到名為 '{target_name}' 的 Vector Store，無法刪除")
        return

    for s in matches:
        try:
            await client.vector_stores.delete(id=s.id)
            print(f"✅ 已刪除 Vector Store：{s.id} ({s.name})")
        except Exception as e:
            print(f"⚠️ 刪除 {s.id} 時發生錯誤: {str(e)}")

    print(f"🧹 共刪除 {len(matches)} 個名為 '{target_name}' 的 Vector Store")


async def main():
    vs_id = await create_vector_store()
    await upload_file_to_vector_store(vs_id)
    print("Vector Store ID:", vs_id)

if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(delete_vector_store_all())
