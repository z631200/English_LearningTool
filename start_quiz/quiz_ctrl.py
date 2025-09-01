import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_file")

import os

def extract_answer(file_path):
    if not os.path.exists(file_path):
        print(f"⛔ 題目檔案不存在：{file_path}")
        raise FileNotFoundError(f"⛔ 題目檔案不存在")

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line.startswith("Answer:"):
                answer = line.replace("Answer:", "").strip().lower()
                return answer

    print("⛔ 找不到答案")
    return None

def check_user_answer(correct_answer):
    user_input = input("\n請輸入你的答案（格式：C,C,C）：").strip().lower()

    if user_input == correct_answer:
        print("🥳 答案正確！")
    else:
        print(f"😢 答案錯誤。正確答案是：{correct_answer}")

def show_quiz(file_path):
    if not os.path.exists(file_path):
        print(f"檔案不存在：{file_path}")
        return

    print("\n=== 測驗內容如下 ===\n")
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        print(content)
    print("\n====================\n")


def core():
    file_path = os.path.join(OUTPUT_DIR, "ListeningTest.txt")
    correct_answer = extract_answer(file_path)

    if correct_answer:
        check_user_answer(correct_answer)

    showing_quiz = input("\n是否查看考試題目與答案? (y/n): ").lower()
    if showing_quiz == "y":
        show_quiz(file_path)

if __name__ == "__main__":
    core()
