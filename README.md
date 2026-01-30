# ListeningTest
Application for generating and conducting listening tests baesd on videos.  
This project can only run on windows.

## 🎯 Objective
1. Create a listening test based on a video.
2. Use speech-to-text to extract transcripts (only for videos with scripts).
3. Use text-to-speech to read questions aloud during the test.

## 🧰 Requirements
1. Whisper (speech-to-text)
3. OpenAI Response API (for test generation)
2. OpenAI TTS API (text-to-speech)

## ⚙️ Workflow
1. Use transcrip-tube to extract transcripts from local or YouTube videos (by https://github.com/RexWei1016/transcrip-tube).
2. Use OpenAI API to automatically generate listening test questions from the transcript.
3. Use a TTS API to generate an audio file for the questions.
4. Run the listening test.

## 專案結構
```
main/
├── app.py
├── config.py
├── output_file/         # 儲存輸出檔案
├── transcription_maker  # 逐字稿生成模組
    ├── whisper_ctrl.py      # 主程式
    ├── tool/                # 工具目錄（包含 FFmpeg）
    ├── utils/               # 工具函數
    ├── downloader/          # 下載相關模組
    ├── audio_processing/    # 音訊處理模組
    └── transcription/       # 轉錄相關模組
├── quiz_maker/          # 題目文字模組
    └── response_ctrl.py     # 模組主程式
├── quiz_speaker/        # 題目語音模組
    ├── audio_maker.py       # 音訊生成
    └── audio_ctrl.py        # 音訊控制
└── start_quiz/          # 測驗模組
    └── quiz_ctrl.py         # 模組主程式

```

## 套件
pip install dotenv openai pygame pydub yt-dlp gradio==5.44.1  
pip install git+https://github.com/openai/whisper.git

## reference
1. https://platform.openai.com/docs/guides/text?api-mode=chat&prompt-example=code
2. https://platform.openai.com/docs/guides/tools-file-search
3. https://platform.openai.com/docs/guides/text-to-speech
