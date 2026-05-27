# 🤖 Smart Autofill Agent — LangGraph × Chrome Extension

> An AI-powered browser extension that intelligently fills out any web form — job applications, sign-ups, surveys, and more — using your resume and saved profile data. Powered by **LangGraph**, **GPT-4o** (vision + text), and a **Chrome Extension (Manifest V3)**.

---

## ✨ Features

- 🧠 **Agentic form analysis** — GPT-4o reads your page screenshot AND DOM to understand every field
- 📄 **Resume parsing** — Upload a PDF resume once; the agent extracts and remembers all your info
- 💾 **Persistent memory** — Answers you give are saved locally and never asked again
- 🎙️ **Voice input** — Answer agent questions by speaking (WebKit Speech API built-in)
- 📁 **File upload support** — Automatically injects your saved resume into file-upload fields on forms
- 🔁 **Interactive loop** — If a field can't be auto-filled, the agent asks you directly in the popup
- ⚡ **Works on any web form** — Not just job applications; any HTML form on any website

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Chrome Extension                       │
│                                                         │
│  popup.html/js        background.js       content.js    │
│  ─────────────        ─────────────       ──────────     │
│  UI + voice input  →  screenshot +    →  DOM extract    │
│  question display     API calls           + actions     │
└───────────────────────────┬─────────────────────────────┘
                            │  HTTP  (localhost:8000)
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 FastAPI Backend (Python)                  │
│                                                         │
│   /upload_resume   →  parse PDF → save file + profile   │
│   /process_page    →  run LangGraph agent               │
│   /get_resume      →  serve saved file (base64)         │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    LangGraph Agent                        │
│                                                         │
│  process_user_response → analyze_form → map_data        │
│                                            │            │
│                          ┌─────────────────┤            │
│                          ▼                 ▼            │
│                   generate_question  generate_actions   │
│                   (status = "ask")   (status = "fill")  │
└─────────────────────────────────────────────────────────┘
```

### LangGraph Node Flow

| Node | What it does |
|------|-------------|
| `process_user_response` | If the user answered a question, extracts info and saves to `user_profile.json` |
| `analyze_form` | Uses GPT-4o vision to identify all form fields from the screenshot + DOM |
| `map_data` | Maps known profile data to form fields; identifies what's missing |
| `generate_question` | Asks the user (in the popup) for any missing info |
| `generate_actions` | Produces a list of `type` / `click` / `upload` commands for the extension |

---

## 📁 Project Structure

```
autofill_agent/
├── backend/
│   ├── main.py                  # FastAPI server (3 endpoints)
│   ├── requirements.txt
│   ├── agent/
│   │   ├── graph.py             # LangGraph workflow definition
│   │   ├── nodes.py             # All agent node logic
│   │   └── state.py             # AgentState TypedDict
│   ├── core/
│   │   ├── llm.py               # GPT-4o configuration
│   │   └── profile_manager.py   # JSON-based user memory
│   └── tools/
│       └── document_parser.py   # PDF resume text extraction
│
└── extension/
    ├── manifest.json            # Chrome Manifest V3
    ├── popup/
    │   ├── popup.html           # Extension popup UI
    │   ├── popup.css
    │   └── popup.js             # UI logic + WebKit Speech API
    └── scripts/
        ├── background.js        # Screenshot capture + API calls
        └── content.js           # DOM scraping + action execution
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js (not required — extension is vanilla JS)
- Google Chrome
- An [OpenAI API key](https://platform.openai.com/api-keys)

---

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/autofill_agent.git
cd autofill_agent
```

---

### 2. Set Up the Backend

```bash
cd backend

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate       # macOS/Linux
# .\venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:

```env
OPENAI_API_KEY=sk-your-key-here
```

Start the server:

```bash
uvicorn main:app --reload
```

The API will be live at `http://localhost:8000`. You can verify it at [http://localhost:8000/docs](http://localhost:8000/docs).

---

### 3. Load the Chrome Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Toggle **Developer mode** ON (top-right corner)
3. Click **Load unpacked**
4. Select the `extension/` folder from this repository

The **Smart Autofill Agent** icon will appear in your Chrome toolbar.

---

## 🧪 How to Use

### Step 1 — Upload Your Resume (one time only)

1. Click the extension icon 🤖
2. Click **Choose File**, select your PDF resume
3. Click **Process Resume**
4. Wait for the ✓ success message — your profile is now saved

### Step 2 — Autofill Any Form

1. Navigate to any web form (job application, sign-up, contact form, etc.)
2. Click the extension icon
3. Click **Autofill This Page**
4. The agent will:
   - Take a screenshot of the page
   - Extract the form fields
   - Fill everything it knows from your profile
   - Ask you (in the popup) for anything it doesn't know

### Step 3 — Answer Missing Questions

If the agent needs more info, it will show a question in the popup:

- **Type** your answer in the text box, or
- **Click 🎤 Voice** and speak your answer

Your answer is saved automatically — you'll never be asked the same question again.

---

## 🔌 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload_resume` | `POST` | Upload a PDF resume; parses and saves profile |
| `/process_page` | `POST` | Runs the LangGraph agent on the current page state |
| `/get_resume` | `GET` | Returns the saved resume as base64 (used for file-upload fields) |

---

## 🎙️ Voice Input — Two Modes

The extension supports two voice input approaches. The active one uses the **browser's built-in speech recognition**. The alternative (sending raw audio to the backend for Whisper transcription) is included as **commented-out code** in `popup.js` for easy switching.

| Mode | Implementation | Status |
|------|---------------|--------|
| WebKit Speech API | Browser-native, no API cost | ✅ Active |
| OpenAI Whisper | Backend audio transcription | 💬 Commented out in `popup.js` |

To switch to Whisper mode: uncomment the `MediaRecorder` block in `popup.js` and comment out the `webkitSpeechRecognition` block.

---

## 💾 Data Storage

All user data is stored **locally on your machine** — nothing is sent to any third-party database.

| Data | Location |
|------|----------|
| Extracted profile (name, email, experience, etc.) | `backend/user_profile.json` |
| Uploaded resume file | `backend/uploaded_resume.pdf` |

To reset your profile, delete `user_profile.json` and/or `uploaded_resume.pdf`.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | [LangGraph](https://github.com/langchain-ai/langgraph) |
| LLM | GPT-4o (vision + text + JSON mode) |
| Backend | FastAPI + Uvicorn |
| PDF Parsing | PyPDF2 |
| Extension | Chrome Manifest V3 (Vanilla JS) |
| Memory | Local JSON file |
| Voice | WebKit Speech Recognition API |

---

## ⚙️ Configuration

| Variable | File | Description |
|----------|------|-------------|
| `OPENAI_API_KEY` | `backend/.env` | Your OpenAI API key |
| `API_URL` | `extension/scripts/background.js` line 1 | Backend URL (default: `http://localhost:8000`) |

---

## 🔒 Security Notes

- The CORS policy in `main.py` currently allows `*`. For production use, replace with your specific Chrome extension ID: `chrome-extension://YOUR_EXTENSION_ID`
- Your resume and profile data never leave your local machine (except to OpenAI's API for processing)
- The extension does NOT auto-submit forms — it fills fields only

---

## 🐛 Debugging Tips

**Extension not responding?**
- Reload the extension at `chrome://extensions/`
- Refresh the target webpage (content script needs to be injected fresh)
- Check the background service worker console: `chrome://extensions/` → click **"service worker"** link

**Backend errors?**
- Make sure `uvicorn` is running and accessible at `http://localhost:8000`
- Check your `.env` file has a valid `OPENAI_API_KEY`
- View server logs in the terminal where uvicorn is running

**Resume not being recognized?**
- Ensure the backend server was running when you uploaded the resume
- Check `backend/user_profile.json` exists and has content
- Check `backend/uploaded_resume.pdf` exists

---

## 📄 License

MIT License — feel free to use, modify, and distribute.

---

## 🙌 Contributing

PRs welcome! Some ideas for contributions:
- Support for `.docx` resume format
- Multi-language form support
- Better selector strategies for complex React/Angular forms
- A settings page in the extension popup
