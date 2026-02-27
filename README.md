# English_LearningTool
An application for generating and conducting listening tests and text-based quizzes based on videos and uploaded text materials.
This project currently runs on Windows only.


## 🎯 Objective
Provide a simple, Windows-only tool to generate and run both listening tests (from videos) and text-based quizzes (from uploaded materials) through a Gradio web interface, using OpenAI for question generation and optional text-to-speech for audio playback.


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
### Listening Test
1. Create a listening test from a video (local file or YouTube).
2. Extract transcripts using speech-to-text (best suited for videos with clear speech/script).
3. Generate listening questions from the transcript using the OpenAI Response API.
4. Use text-to-speech to read questions aloud during the listening test.
5. Run the listening test in the Gradio UI.
### Text-Based Quiz
1. Upload text files/materials.
2. Upload the materials to an OpenAI Vector Store for retrieval (File Search / RAG).
3. Generate text-based quiz questions using the OpenAI Response API with retrieval from the Vector Store.
4. Run the text-based quiz in the Gradio UI.


## 🗂️ Project Structure
```
/
├── app.py
├── config.py
├── output_file/         # Generated at runtime (output files)
├── transcription_maker  # Transcription module (Whisper)
│   ├── whisper_ctrl.py      
│   ├── tool/               # Tools (includes FFmpeg) 
│   ├── utils/              
│   ├── downloader/          
│   ├── audio_processing/    
│   └── transcription/       
├── quiz_maker/          # Listening quiz generator (from transcript)
│   └── response_ctrl.py     
├── quiz_speaker/        # TTS module (generate audio for questions)
│   └── audio_maker.py       # Audio generation  
├── start_quiz/          # Quiz runner
│   ├── quiz_ctrl.py         # Listening test runner
│   └── normal_quiz_ctrl.py  # Text-based quiz runner
└── text_quiz_maker/     # Text-based quiz generator
    ├── file_ctrl.py         
    └── response_ctrl.py     # Question generation
```

## 📦 Package
```
pip install dotenv openai pygame pydub yt-dlp gradio==5.44.1 git+https://github.com/openai/whisper.git
```

## 📚 Reference
1. https://platform.openai.com/docs/guides/text?api-mode=chat&prompt-example=code
2. https://platform.openai.com/docs/guides/tools-file-search
3. https://platform.openai.com/docs/guides/text-to-speech
