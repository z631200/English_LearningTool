import os
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_file")

def get_question(question_num: int):
    file_path = os.path.join(OUTPUT_DIR, "NormalTest.txt")
    if not os.path.exists(file_path):
        print(f"檔案不存在：{file_path}")
        return None, None

    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # 使用正則表達式擷取指定題目
    # 模式說明：
    # - 找出 "Question {num}:" 開頭
    # - 直到下一個 "Question " 或檔案結尾為止
    pattern = rf"Question {question_num}:(.*?)(?=Question \d+:|$)"
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        print(f"⚠️ 找不到第 {question_num} 題")
        return None, None

    question_block = match.group(1).strip()

    # 分離題目內容與答案
    # 找出 "Answer: " 行
    answer_match = re.search(r"Answer:\s*([A-D])", question_block)
    correct_answer = answer_match.group(1).strip() if answer_match else ""

    # 去除 Answer 段落後，留下題目文字
    question_text = re.sub(r"Answer:\s*[A-D].*", "", question_block, flags=re.DOTALL).strip()

    return question_text, correct_answer

def core():
    question_txt, answer_txt = get_question(3)
    print("題目：\n", question_txt)
    print("\n答案：\n", answer_txt)
    return

if __name__ == "__main__":
    core()
