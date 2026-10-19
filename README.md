# 🌐 Language Translation Tool

A web app that translates text between 23 languages, with a one-click **Copy** button and **Text-to-Speech**.

Built as **Task 1: Language Translation Tool**, with a FastAPI backend and a Streamlit interface.

## 🔗 Live Demo

| Part | Link |
|---|---|
| App (Streamlit) | https://codealpha-translation-tool.streamlit.app/ |
| API (FastAPI) | https://translation-tool-nja5.onrender.com |
| API docs (Swagger) | https://translation-tool-nja5.onrender.com/docs |

> **Note:** The backend runs on a free Render instance that sleeps after 15 minutes of inactivity. The first request after a quiet period can take up to a minute while the server wakes up. After that it responds normally.

<!-- Add a screenshot: save it as docs/screenshot.png and uncomment the next line -->
<!-- ![App screenshot](docs/screenshot.png) -->

## ✨ Features

- Select **source** and **target** language (or use **Auto Detect**)
- Swap languages with one click
- Translate up to **5,000 characters** at a time, with a live character counter
- Translated text shown clearly in a dedicated result box
- Always-visible **Copy** button (works with Bengali and multi-line text)
- **Text-to-Speech**: listen to the translation as audio
- Friendly error messages when the service is busy or unreachable

## 🏗️ Architecture

```text
Browser
   │
   ▼
Streamlit UI  (Streamlit Community Cloud)
   │   HTTPS (requests)
   ▼
FastAPI backend  (Render)
   ├── POST /translate ──► Gemini API
   └── POST /tts ────────► gTTS (audio/mpeg)
```

The UI never talks to the translation service directly. All logic (validation, caching, retries, error handling) lives in the backend, so the frontend stays thin and the translation engine can be swapped without touching the UI.

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit, custom CSS, a small JavaScript snippet for the Copy button |
| Backend | FastAPI, Pydantic, Uvicorn |
| Translation | Google Gemini API (`gemini-3.1-flash-lite`) via `google-genai` |
| Text-to-Speech | gTTS |
| Hosting | Render (backend), Streamlit Community Cloud (frontend) |

## 📁 Project Structure

```text
translation-tool/
├── backend/
│   ├── __init__.py
│   └── main.py              # FastAPI app: /health, /languages, /translate, /tts
├── frontend/
│   ├── app.py               # Streamlit UI
│   └── requirements.txt     # Frontend dependencies
├── requirements.txt         # Backend dependencies
├── .gitignore
└── README.md
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check that the server is running |
| GET | `/languages` | List of supported languages (name → code) |
| POST | `/translate` | Translate text |
| POST | `/tts` | Convert text to speech (returns an MP3) |

**Translate request**

```json
{
  "text": "Hello, how are you?",
  "source": "en",
  "target": "bn"
}
```

Use `"source": "auto"` to detect the source language automatically.

**Translate response**

```json
{
  "translated_text": "...",
  "source": "en",
  "target": "bn"
}
```

**Text-to-speech request**

```json
{
  "text": "Hello, how are you?",
  "lang": "en"
}
```

**Error codes**

| Code | Meaning |
|---|---|
| 400 | Invalid input (empty text, unsupported language, same source and target) |
| 429 | Translation service is busy, try again shortly |
| 502 | The upstream service (Gemini or gTTS) failed |

## 🌍 Supported Languages

English, Bengali, Hindi, Urdu, Arabic, Spanish, French, German, Italian, Portuguese, Russian, Japanese, Korean, Chinese (Simplified), Turkish, Indonesian, Thai, Vietnamese, Tamil, Nepali, Dutch, Greek, Swahili.

These are the languages that both the translation step and the text-to-speech step support, so the Listen button works for every one of them.

## 🚀 Run Locally

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/mahmudulhasan3/translation-tool.git
cd translation-tool
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt -r frontend/requirements.txt
```

### 3. Add your Gemini API key

Create a `.env` file in the project root:

```text
GEMINI_API_KEY=your_api_key_here
```

You can get a free key from [Google AI Studio](https://aistudio.google.com/). The `.env` file is listed in `.gitignore` and must never be committed.

### 4. Start the backend

```bash
uvicorn backend.main:app --reload
```

The API runs at `http://127.0.0.1:8000` and the docs are at `http://127.0.0.1:8000/docs`.

### 5. Start the frontend (in a second terminal)

```bash
source venv/bin/activate
API_URL=http://127.0.0.1:8000 streamlit run frontend/app.py
```

The app opens at `http://localhost:8501`.

> Without `API_URL`, the frontend connects to the deployed Render backend.

## ⚙️ Configuration

| Variable | Where | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | Backend (`.env` locally, environment variable on Render) | Gemini API key |
| `API_URL` | Frontend (environment variable or Streamlit secret) | Backend URL. Defaults to the deployed Render backend |

## ☁️ Deployment

**Backend (Render)**

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- Environment variable: `GEMINI_API_KEY`

**Frontend (Streamlit Community Cloud)**

- Repository: `mahmudulhasan3/translation-tool`, branch `main`
- Main file path: `frontend/app.py`
- Python version: 3.12

Both services redeploy automatically on every push to `main`.

## 🔒 Design Decisions

- **Gemini instead of a free Google Translate wrapper.** The free unofficial Google Translate endpoint blocked repeated requests (HTTP 429), so translation uses the official Gemini API.
- **Prompt-injection protection.** The user's text is wrapped in `<text>` tags and the system instruction tells the model to translate any instructions it finds there instead of obeying them.
- **Deterministic output.** `temperature=0` gives the same translation for the same input.
- **Caching.** Identical requests are served from an in-memory `lru_cache`, which saves API calls.
- **Retry with exponential backoff** when the API returns a rate-limit error (429).
- **Blocking libraries run in plain `def` endpoints**, so FastAPI executes them in a thread pool and the event loop is never blocked.
- **Secrets stay out of Git.** API keys live in `.env` locally and in the hosting dashboard in production.

## ⚠️ Known Limitations

- The free Render instance sleeps when idle, so the first request can be slow.
- Text-to-speech uses `gTTS`, which relies on an unofficial Google endpoint and may be rate-limited or blocked from cloud servers.
- The Gemini free tier has rate limits, and data sent on the free tier may be used by Google to improve its products, so do not translate sensitive text.
- The cache lives in memory and is cleared on every restart.
- The backend API is public and has no authentication yet.

## 🛣️ Future Improvements

- Shared secret between the frontend and backend, plus rate limiting per client
- Translation history stored in PostgreSQL
- Shared cache (Redis) instead of in-memory cache
- Official Google Cloud Translation and Text-to-Speech APIs for production use
- Docker setup and automated tests with GitHub Actions
- Browser-based text-to-speech as a fallback

## 👤 Author

**Mahmudul Hasan**

- GitHub: [@mahmudulhasan3](https://github.com/mahmudulhasan3)
- LinkedIn: [@mahmudulhasan03](https://www.linkedin.com/in/mahmudulhasan03/)