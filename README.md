# ListeningTest
Application for generating and conducting listening tests based on videos and uploaded text materials.  
This project can only run on Windows.

## 🎯 Objective
1. Create a listening test based on a video.
2. Use speech-to-text to extract transcripts (only for videos with scripts).
3. Use text-to-speech to read questions aloud during the test.
4. Generate text-based quizzes from uploaded materials.

## 🧰 Requirements
1. Whisper (speech-to-text)
2. OpenAI Response API (for test generation)
3. OpenAI TTS API (text-to-speech)

## 🔑 OpenAI API Key 設定（必做）
本專案會從專案根目錄的 `.env` 檔案讀取 OpenAI API Key。
1. 在專案根目錄建立 `.env` 檔案（與 `app.py` 同一層）。
2. 在 `.env` 內加入以下內容，並把你的 Key 填上去：

```dotenv
OPENAI_API_KEY=你的_API_KEY_貼在這裡
```

## ⚙️ Workflow
1. Use transcrip-tube to extract transcripts from local or YouTube videos (by https://github.com/RexWei1016/transcrip-tube).
2. Use OpenAI API to automatically generate listening test questions from the transcript or uploaded materials.
3. Use a TTS API to generate an audio file for the questions.
4. Run the listening or text-based test in the Gradio UI.

## 專案結構
```
/
├── app.py
├── config.py
├── output_file/         # 執行時生成，儲存輸出檔案
├── transcription_maker  # 逐字稿生成模組
│   ├── whisper_ctrl.py      # 主程式
│   ├── tool/                # 工具目錄（包含 FFmpeg）
│   ├── utils/               # 工具函數
│   ├── downloader/          # 下載相關模組
│   ├── audio_processing/    # 音訊處理模組
│   └── transcription/       # 轉錄相關模組
├── quiz_maker/          # 題目文字模組
│   └── response_ctrl.py     # 模組主程式
├── quiz_speaker/        # 題目語音模組
│   └── audio_maker.py       # 音訊生成
├── start_quiz/          # 測驗模組
│   ├── quiz_ctrl.py         # 聽力測驗
│   └── normal_quiz_ctrl.py  # 文字測驗
└── text_quiz_maker/     # 文字題目模組
    ├── file_ctrl.py         # 檔案管理
    └── response_ctrl.py     # 題目生成
```

## 套件
pip install dotenv openai pygame pydub yt-dlp gradio==5.44.1  
pip install git+https://github.com/openai/whisper.git

## reference
1. https://platform.openai.com/docs/guides/text?api-mode=chat&prompt-example=code
2. https://platform.openai.com/docs/guides/tools-file-search
3. https://platform.openai.com/docs/guides/text-to-speech
