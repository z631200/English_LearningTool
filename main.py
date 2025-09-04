# import os
# import glob
# import asyncio
# from transcription_maker import whisper_ctrl
# from quiz_maker import response_ctrl
# from quiz_speaker import audio_ctrl
# from start_quiz import quiz_ctrl

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# OUTPUT_DIR = os.path.join(BASE_DIR, "output_file")
# TRANSCRIP_TOOL_DIR = os.path.join(BASE_DIR, "transcription_maker/tool")

# os.environ["PATH"] = f"{TRANSCRIP_TOOL_DIR};{os.environ['PATH']}"

# def delete_files_in_output_file(full_execution = False):
#     extensions = ["*.wav", "*.mp3", "*.txt"]
#     deleted_files = []
#     for ext in extensions:
#         pattern = os.path.join(OUTPUT_DIR, ext)
#         for file in glob.glob(pattern):
#             try:
#                 os.remove(file)
#                 deleted_files.append(file)
#             except Exception as e:
#                 print(f"⚠️ 無法刪除 {file}：{e}")

#     if not full_execution:
#         if deleted_files:
#             print("✅ 已刪除以下檔案：")
#             for f in deleted_files:
#                 print(f" - {f}")
#         else:
#             print("📂 沒有在 output_file 資料夾中找到任何 wav、mp3 或 txt 檔案。")
#     else:
#         print("📂 已重置output_file資料夾")

def main():
#     print("🎛️  請選擇模式：")
#     print("1. 完整啟動")
#     print("2. 語音轉錄功能")
#     print("3. 生成聽力題目文字檔")
#     print("4. 聽力題目語音檔: 生成&控制")
#     print("5. 啟動測驗")    
#     print("6. 刪除當前目錄下的 wav, mp4, txt 檔案並結束")    
#     choice = input("請輸入選項 (1/2/3/4/5/6)： ")

#     if choice == "1":
#         audio_ctrl.audio_test_volume()
#         whisper_ctrl.core()
#         asyncio.run(response_ctrl.core())
#         audio_ctrl.core(True)
#         quiz_ctrl.core()
#         return
#     elif choice == "2":
#         whisper_ctrl.core()
#         return
#     elif choice == "3":
#         asyncio.run(response_ctrl.core())
#         return
#     elif choice == "4":
#         audio_ctrl.core(True)
#         return
#     elif choice == "5":
#         quiz_ctrl.core()
#         return
#     elif choice == "6":
#         delete_files_in_output_file()
#         return
#     elif choice == "0":
#         audio_ctrl.core(False)
#         quiz_ctrl.core()
#         return
    return
    

if __name__ == "__main__":
    main()
