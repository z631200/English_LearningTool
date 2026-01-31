# LearningTool
An application for generating and conducting listening tests and text-based quizzes based on videos and uploaded text materials.
This project currently runs on Windows only.

## 🎯 Objective
### Listening Test
1. Create a listening test from a video (local file or YouTube).
2. Extract transcripts using speech-to-text (best suited for videos with clear speech/script).
3. Generate listening questions from the transcript using the OpenAI Response API.
4. Use text-to-speech to read questions aloud during the listening test.
### Text-Based Quiz
1. Create a text-based quiz from uploaded text files/materials (no audio required).
2. Run the text quiz through a Gradio web UI.


## 🧰 Requirements
- **Whisper** (speech-to-text transcription)
- **yt-dlp** (download YouTube videos)
- **FFmpeg** (audio processing; included under `transcription_maker/tool/` if bundled)
- **OpenAI Response API** (question generation for both listening and text quizzes)
- **OpenAI Vector Store / File Search** (store uploaded materials as embeddings for retrieval-augmented question generation)
- **OpenAI TTS API** (text-to-speech for listening questions)
- **Gradio** (web UI)
- **Python packages**: `python-dotenv`, `openai`, `pygame`, `pydub`


## 🔑 OpenAI API Key Setup (Required)
This project reads your OpenAI API key from a .env file located in the project root directory.
1. Create a `.env` file in the project root (same directory as `app.py`).
2. Add the following line to your `.env` file and paste your API key:
```dotenv
OPENAI_API_KEY=your_api_key_here
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
```
pip install dotenv openai pygame pydub yt-dlp gradio==5.44.1 git+https://github.com/openai/whisper.git
```

## reference
1. https://platform.openai.com/docs/guides/text?api-mode=chat&prompt-example=code
2. https://platform.openai.com/docs/guides/tools-file-search
3. https://platform.openai.com/docs/guides/text-to-speech
