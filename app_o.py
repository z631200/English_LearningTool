import os
from typing import Any, Dict, Tuple, Optional
import gradio as gr

from transcription_maker import whisper_ctrl

# ✅ 如果 whisper_ctrl.py 與本檔案同層，以下 import 會成功
#    若在套件資料夾中，請把對應的封裝路徑補上（例如 from transcription_maker.whisper_ctrl import core）

# === 共同輸出資料夾（可依專案調整） ===
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output_file")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === 事件處理函式 ===

def on_run_whisper(youtube_url: str) -> Tuple[str, Optional[str]]:
    """
    1) 觸發 whisper_ctrl.core()
    2) 嘗試從回傳中抓到 txt 路徑與轉錄文字
    3) 將路徑存在 State，並把摘要/提示顯示在輸出框
    回傳：(輸出框文字, txt_path_state)
    """
    if not youtube_url:
        return "請先輸入 YouTube 影片網址。", None

    try:
        result = whisper_ctrl.process_youtube_video(youtube_url)
    except TypeError:
        # 若 core() 不吃參數，退回無參數呼叫
        result = whisper_ctrl.process_youtube_video(youtube_url)  # type: ignore

    # 嘗試解析不同可能型態的回傳
    txt_path: Optional[str] = None
    preview_text: Optional[str] = None

    if isinstance(result, str):
        # 只回傳路徑字串
        txt_path = result
    elif isinstance(result, (list, tuple)):
        # 常見： (txt_path, full_text, meta)
        if len(result) >= 1 and isinstance(result[0], str):
            txt_path = result[0]
        if len(result) >= 2 and isinstance(result[1], str):
            preview_text = result[1]
    elif isinstance(result, dict):
        # 若回傳 dict，嘗試讀常見鍵名
        txt_path = result.get("txt_path") or result.get("path")  # type: ignore
        preview_text = result.get("text") or result.get("transcript")  # type: ignore

    # 組裝顯示內容
    if preview_text:
        head = preview_text.strip()
        # 若文字很長，截個頭讓 UI 不會爆
        if len(head) > 500:
            head = head[:500] + "\n...（內容過長已截斷，請按『確認 Whisper 輸出結果』完整載入）"
        display = head
    else:
        display = "已完成轉錄。若未自動顯示全文，請按『確認 Whisper 輸出結果』讀取檔案。"

    return display, txt_path


def on_confirm_output(txt_path: Optional[str]) -> str:
    """按下『確認 Whisper 輸出結果』，讀取 txt 並顯示到文字框。"""
    # 若沒有狀態中的路徑，嘗試抓資料夾裡最新的 .txt
    if not txt_path:
        try:
            candidates = [
                os.path.join(OUTPUT_DIR, f)
                for f in os.listdir(OUTPUT_DIR)
                if f.lower().endswith(".txt")
            ]
            if not candidates:
                return "找不到可讀取的轉錄檔案。請先執行轉錄或確認輸出目錄。"
            txt_path = max(candidates, key=os.path.getmtime)
        except Exception as e:
            return f"讀取輸出目錄時發生錯誤：{e}"

    if not os.path.exists(txt_path):
        return f"找不到檔案：{txt_path}"

    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"讀檔失敗：{e}"


# === 介面 ===
with gr.Blocks(title="ListeningTest — Whisper 轉錄（第一頁）") as demo:
    gr.Markdown("""
    # Whisper 轉錄（第一頁）
    1. 輸入 YouTube 影片網址 → 按 **執行 Whisper 轉錄**。
    2. 完成後可按 **確認 Whisper 輸出結果** 來讀取並顯示完整的 `.txt` 檔內容。
    """)

    # 狀態：保存轉錄後的 txt 檔路徑
    st_txt_path = gr.State(value=None)

    with gr.Row():
        url_in = gr.Textbox(
            label="YouTube 影片網址",
            placeholder="貼上影片連結，例如：https://www.youtube.com/watch?v=...",
        )

    with gr.Row():
        btn_run = gr.Button("執行 Whisper 轉錄", variant="primary")
        btn_confirm = gr.Button("確認 Whisper 輸出結果")

    out_box = gr.Textbox(
        label="Whisper 輸出結果",
        lines=18,
        placeholder="這裡會顯示轉錄文字或提示訊息",
    )

    # 綁定互動
    btn_run.click(
        fn=on_run_whisper,
        inputs=[url_in],
        outputs=[out_box, st_txt_path],
        show_progress=True,
    )

    btn_confirm.click(
        fn=on_confirm_output,
        inputs=[st_txt_path],
        outputs=[out_box],
        show_progress=False,
    )

if __name__ == "__main__":
    # 注意：若在雲端或特定環境，請調整 server_name / server_port
    demo.launch()
