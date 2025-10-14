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

client = AsyncOpenAI(api_key=api_key)

def create_vector_store():
    stores = client.vector_stores.list().data
    existing = next((s for s in stores if s.name == "SE_Class"), None)

    if existing:
        vector_store_id = existing.id
        print("✅ 已存在 vector store:", vector_store_id)
    else:
        new_store = client.vector_stores.create(name="SE_Class")
        vector_store_id = new_store.id
        print("🆕 建立新的 vector store:", vector_store_id)

    return vector_store_id


def uplaod_file_to_vector_store(vector_store_id):
    file_path = select_file()
    if not file_path:
        return

    with open(file_path, "rb") as f:
        upload = client.vector_stores.files.upload(
            vector_store_id=vector_store_id,
            file=f
        )
    print(f"✅ 檔案已上傳到 Vector Store ({vector_store_id})：{upload.id}")

    return


def select_file():
    root = Tk()
    root.withdraw()  # 隱藏主視窗
    file_path = filedialog.askopenfilename(
        title="選擇檔案",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )
    print("選擇的檔案：", file_path)

    return file_path
