# English_LearningTool
An application for generating and conducting listening tests and text-based quizzes based on videos and uploaded text materials.
This project currently runs on Windows only.

## 🎯 Objective
Provide a simple, Windows-only tool to generate and run both listening tests (from videos) and text-based quizzes (from uploaded materials) through a Gradio web interface, using OpenAI for question generation and optional text-to-speech for audio playback.

## 📖 How to use
1. Clone this project
2. Set up OpenAI API Key  
   This project reads your OpenAI API key from a `.env` file located in the project root directory.
   1. Create a `.env` file in the project root (same directory as `app.py`).
   2. Add the following line to your `.env` file and paste your API key:
      ```dotenv
      OPENAI_API_KEY=your_api_key_here
      ```
3. Install required packages in your Python environment (see `requirements.txt`).  
   If you use Anaconda to create a virtual environment, you only need to run the following command **inside that environment**:
   ```bash
   pip install python-dotenv openai pygame pydub tqdm "yt-dlp[default]==2026.8.19" gradio==5.44.1
   ```
4. Install the YouTube JavaScript runtime and matching EJS dependencies **using the same Python environment as the application**:
   ```bash
   python scripts/setup_youtube.py
   ```
   This downloads the official Windows x64 Deno runtime into `transcription_maker/tool/`, verifies its SHA-256, and installs yt-dlp with its `default` dependencies (including `yt-dlp-ejs`). No system PATH changes are required. Restart the application after setup.
5. Run `app.py`
6. Choose a workflow in the Gradio UI:

   ### 🎧 Listening Test
   1. Transcribe a YouTube video with OpenAI `gpt-transcribe`. For local audio or video, run `python -m transcription_maker.transcription_ctrl` and select option 1.
   2. Generate listening questions from the transcript using the OpenAI Response API (you can decide how many questions to create).
   3. Use text-to-speech to read questions aloud during the listening test.
   4. Run the listening test in the Gradio UI.

   ### 📝 Text-Based Quiz
   1. Upload the materials to an OpenAI Vector Store for retrieval (File Search / RAG).
   2. Generate text-based quiz questions using the OpenAI Response API with retrieval from the Vector Store.
   3. Run the text-based quiz in the Gradio UI.
  
## Speech-to-text
Transcription calls the OpenAI Audio Transcriptions API with `model="gpt-transcribe"`
and uses the same `OPENAI_API_KEY` as question generation and text-to-speech.
Your API account must have access to this model and sufficient API credit.

FFmpeg converts the complete recording into consecutive mono 64 kbps MP3 chunks
of approximately 10 minutes, each below the API's 25 MB upload limit. Chunks are
transcribed in order, and temporary audio files are removed even if a request fails.
The completed transcript is saved as UTF-8 plain text in
`output_file/transcription.txt`, ready for listening-question generation.
No original-video timestamps or timestamp mapping are generated.
Transcription runs entirely through the API; no local speech model or GPU is needed.

Run the offline regression tests with `python -m unittest discover -s tests -v`.
These tests use the bundled FFmpeg and mocked API responses, without API charges.

## 🎬 Demo Video
Listening Test Part: https://youtu.be/zczMy0f_P0E

## YouTube download troubleshooting
The downloader explicitly enables bundled Deno, or a compatible Deno/Node runtime
on PATH. You can override the executable using `YOUTUBE_DENO_PATH` or
`YOUTUBE_NODE_PATH` in `.env`. Supported minimum versions are Deno 2.3 and Node 22.
EJS must be installed in the application's Python environment; installing a runtime
alone does not install the challenge solver.

Downloadable formats are checked before selection. If direct audio formats return
403 or none pass the format check, the downloader first obtains fresh media URLs
and retries with 1 MB HTTP chunks. If needed, it then tries HLS formats from the
default clients plus `web_safari`, extracts their audio, and converts it to MP3.
A failed download does not
replace an existing audio file, and temporary/partial files are removed.

Runtime/EJS fixes do not guarantee access to every video. If the video requires
login, optionally set `YOUTUBE_COOKIES_FILE` to a Netscape-format cookies file for
your authorized session (relative paths resolve from the project root). Keep cookie
files private and outside Git. If yt-dlp reports a required PO Token, follow the
[official PO Token Guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide) to
configure a provider plugin in the same Python environment. Tokens can be bound to
individual videos, so the application does not hardcode a shared token.
See the [official EJS setup guide](https://github.com/yt-dlp/yt-dlp/wiki/EJS).

## 🧰 Requirements
- **OpenAI Audio Transcriptions API / `gpt-transcribe`** (speech-to-text transcription)
- **yt-dlp** (download YouTube videos)
- **FFmpeg** (audio processing; included under `transcription_maker/tool/` if bundled)
- **OpenAI Response API** (question generation for both listening and text quizzes)
- **OpenAI Vector Store / File Search** (store uploaded materials as embeddings for retrieval-augmented question generation)
- **OpenAI TTS API** (text-to-speech for listening questions)
- **Gradio** (web UI)
- **Python** : 3.11
- **Python packages**: `python-dotenv`, `openai`, `pygame`, `pydub`


## 🗂️ Project Structure
```
/
├── app.py
├── config.py
├── output_file/         # Generated at runtime (output files)
├── transcription_maker  # Transcription module (OpenAI API)
│   ├── transcription_ctrl.py
│   ├── tool/               # Tools (includes FFmpeg) 
│   ├── downloader/          
│   ├── audio_processing/prepare_audio.py
│   └── transcription/openai_transcriber.py
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

## 📚 Reference
1. https://platform.openai.com/docs/guides/text?api-mode=chat&prompt-example=code
2. https://platform.openai.com/docs/guides/tools-file-search
3. https://platform.openai.com/docs/guides/text-to-speech
4. https://github.com/RexWei1016/transcrip-tube
5. https://developers.openai.com/api/docs/guides/speech-to-text
