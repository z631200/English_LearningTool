import os
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_file")

def get_question_text(question_num: int):
    file_path = os.path.join(OUTPUT_DIR, "NormalTest.txt")
    if not os.path.exists(file_path):
        print(f"檔案不存在：{file_path}")
        return None

    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # 抓取第 N 題的完整區塊
    pattern = rf"Question {question_num}:(.*?)(?=Question \d+:|$)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        print(f"⚠️ 找不到第 {question_num} 題")
        return None

    question_block = match.group(1).strip()
    # 去掉答案行
    question_text = re.sub(r"Answer:\s*[A-D].*", "", question_block, flags=re.DOTALL).strip()

    # ✅ 保留題號
    full_question = f"Question {question_num}:\n{question_text}"

    return full_question


def get_correct_answer(question_num: int):
    file_path = os.path.join(OUTPUT_DIR, "NormalTest.txt")
    if not os.path.exists(file_path):
        print(f"檔案不存在：{file_path}")
        return None

    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    pattern = rf"Question {question_num}:(.*?)(?=Question \d+:|$)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        print(f"⚠️ 找不到第 {question_num} 題")
        return None

    question_block = match.group(1).strip()
    answer_match = re.search(r"Answer:\s*([A-D])", question_block)
    correct_answer = answer_match.group(1).strip() if answer_match else None

    return correct_answer


def core():
    question_txt = get_question_text(3)
    answer_txt = get_correct_answer(3)
    print("題目：\n", question_txt)
    print("\n答案：\n", answer_txt)
    return

if __name__ == "__main__":
    core()
