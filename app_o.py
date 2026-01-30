import gradio as gr
import os
import glob
from transcription_maker import whisper_ctrl
from quiz_maker import response_ctrl
from quiz_speaker import audio_ctrl
from quiz_speaker import audio_maker
from start_quiz import quiz_ctrl

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_file")
TRANSCRIP_TOOL_DIR = os.path.join(BASE_DIR, "transcription_maker/tool")

os.environ["PATH"] = f"{TRANSCRIP_TOOL_DIR};{os.environ['PATH']}"

def delete_files_in_output_file(full_execution = False):
    extensions = ["*.wav", "*.mp3", "*.txt"]
    deleted_files = []
    for ext in extensions:
        pattern = os.path.join(OUTPUT_DIR, ext)
        for file in glob.glob(pattern):
            try:
                os.remove(file)
                deleted_files.append(file)
            except Exception as e:
                print(f"⚠️ 無法刪除 {file}：{e}")

    if not full_execution:
        if deleted_files:
            print("✅ 已刪除以下檔案：")
            for f in deleted_files:
                print(f" - {f}")
        else:
            print("📂 沒有在 output_file 資料夾中找到任何 wav、mp3 或 txt 檔案。")
    else:
        print("📂 已重置output_file資料夾")

# ====== Callback ======
def on_run_transcribe(youtube_url: str):
    if not youtube_url:
        return "請先輸入 YouTube 連結。"
    delete_files_in_output_file()
    transcribe_done = whisper_ctrl.process_youtube_video(youtube_url)
    if transcribe_done:
        return "✅ 已完成轉錄"
    else:
        return "❌ 未完成轉錄"


def on_show_transcript():
    file_path = os.path.join(OUTPUT_DIR, "transcription.txt")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        status = "📥 已載入轉錄結果"
        return content, status
    except FileNotFoundError:
        return "", "❌ 找不到檔案"
    except Exception as e:
        return "", f"❌ 讀取失敗：{e}"

async def on_generate_questions(quiz_count: str):
    try:
        n = int(quiz_count)
        if n < 1 or n > 10:
            return "❗ 題數需在1~10"        
        await response_ctrl.core(n)
        return f"✅ 已產生 {n} 題"
    except (TypeError, ValueError):
        return "❗ 請輸入整數題數(例如:3)"
    except Exception as e:
        return f"❌ 錯誤：{str(e)}"


def on_load_volume_audio():
    volume_audio_done, err_msg = audio_maker.make_volume_audio()
    if volume_audio_done:
        audio_ctrl.UI_load_audio(False)
        return "📥 已讀取音量測試音檔"
    else:
        return f"❌ 未生成音量測試音檔，原因：{err_msg}"    

def on_load_questions_audio():
    quiz_audio_done, err_msg = audio_maker.make_audio()
    if quiz_audio_done:
        audio_ctrl.UI_load_audio(True)
        return "📥 已讀取題目音檔"
    else:
        return f"❌ 未生成題目音檔，原因：{err_msg}"

def on_play_audio():
    try:
        audio_ctrl.play_audio()
        return "▶️ 播放"
    except Exception as e:
        return f"⛔ 播放時發生錯誤: {str(e)}"
    

def on_pause_audio():
    audio_ctrl.pause_audio()
    return "⏸️ 暫停"

def on_stop_audio():
    audio_ctrl.stop_audio()
    return "⏹️ 停止"

def check_answer(user_answer: str, unlocked: bool):
    try:
        if (user_answer or "").strip():
            file_path = os.path.join(OUTPUT_DIR, "ListeningTest.txt")
            correct_answer = quiz_ctrl.extract_answer(file_path)
            unlocked = True
            if user_answer == correct_answer:
                return "🥳 答案正確！", gr.update(interactive=True), unlocked
            else:
                return f"😢 答案錯誤。正確答案是：{correct_answer}", gr.update(interactive=True), unlocked
        else:
            return "❗ 請先輸入答案再送出。", gr.update(interactive=False), unlocked
    except Exception as e:
        return f"⛔ 檢查答案時發生錯誤: {str(e)}", gr.update(interactive=False), unlocked

def on_show_answers(unlocked: bool):
    if not unlocked:
        return "", "❗ 尚未解鎖，無法顯示答案。"
    file_path = os.path.join(OUTPUT_DIR, "ListeningTest.txt")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        return content
    except FileNotFoundError:
        return "", "❌ 找不到檔案"
    except Exception as e:
        return "", f"❌ 讀取失敗：{e}"

# ====== Gradio interface ======
with gr.Blocks(title="ListeningTest") as demo:
    gr.Markdown("## 🎧 ListeningTest\n> " \
    "每頁的步驟完成後才換下頁")

    with gr.Tabs():
        # ====== p1. YouTube transcribe ======
        with gr.Tab("YouTube 轉錄"):
            youtube_url = gr.Textbox(label="YouTube 連結", placeholder="貼上 YouTube 連結")
            with gr.Row():
                run_btn = gr.Button("執行轉錄", variant="primary")
                show_btn = gr.Button("顯示轉錄結果")
            status_1 = gr.Textbox(label="狀態", interactive=False)
            transcript_box = gr.Textbox(label="轉錄結果", lines=18)

            run_btn.click(fn=on_run_transcribe, inputs=youtube_url, outputs=status_1)
            show_btn.click(fn=on_show_transcript, inputs=None, outputs=[transcript_box, status_1])

        # ====== p2. make quiz ======
        with gr.Tab("產生題目"):
            quiz_count = gr.Textbox(label="題數", value="", placeholder="輸入要產生的題數")
            gen_btn = gr.Button("產生題目", variant="primary")
            status_2 = gr.Textbox(label="狀態", interactive=False)

            gen_btn.click(fn=on_generate_questions, inputs=quiz_count, outputs=status_2)

        # ====== p3. make audio ======
        with gr.Tab("題目語音"):
            is_playing_volume = gr.State(False)
            is_playing_question = gr.State(False)

            with gr.Row():
                make_vol_btn = gr.Button("產生音量測試", variant="huggingface") 
                make_audio_btn = gr.Button("產生題目語音", variant="primary")
            with gr.Row():
                play_btn = gr.Button("播放")
                pause_btn = gr.Button("暫停")
                stop_btn = gr.Button("中止", variant="stop")
            status_3 = gr.Textbox(label="狀態", interactive=False)

            make_vol_btn.click(fn=on_load_volume_audio,inputs=None,outputs=status_3)
            make_audio_btn.click(fn=on_load_questions_audio,inputs=None,outputs=status_3)
            play_btn.click(fn=on_play_audio, inputs=None, outputs=status_3)
            pause_btn.click(fn=on_pause_audio, inputs=None, outputs=status_3)
            stop_btn.click(fn=on_stop_audio, inputs=None, outputs=status_3)

        # ====== p4. start quiz ======
        with gr.Tab("檢視與測驗"):
            ans_unlocked = gr.State(False) # unlock view btn
            user_answer = gr.Textbox(label="輸入答案", placeholder="例如：A,B,C,D,E")
            with gr.Row():
                submit_btn = gr.Button("送出答案", variant="primary")
                show_ans_btn = gr.Button("顯示答案", interactive=False) # unable first
            status_4 = gr.Textbox(label="狀態", interactive=False)
            answers_view = gr.Textbox(label="檢視答案", lines=12)

            submit_btn.click(
                fn=check_answer,
                inputs=[user_answer, ans_unlocked],
                outputs=[status_4, show_ans_btn, ans_unlocked]
            )
            show_ans_btn.click(
                fn=on_show_answers,
                inputs=ans_unlocked,
                outputs=[answers_view]
            )

if __name__ == "__main__":
    demo.launch(
        share=True,
        auth=("203", "203"),
        auth_message="需要帳密才能使用"
    )


