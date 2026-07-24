# 🎙️ VoxBridge

**A voice-first AI assistant, built as a self-hosted web API — live at [voice.nimaserver.xyz](https://voice.nimaserver.xyz).**

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Whisper](https://img.shields.io/badge/OpenAI-Whisper-412991?style=flat-square)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-F55036?style=flat-square)
![Status](https://img.shields.io/badge/Status-Work_in_Progress-orange?style=flat-square)

VoxBridge takes a voice recording (or a text message), transcribes it locally with Whisper, sends it to an LLM, and returns the answer — with persistent conversation memory per session. It runs 24/7 as a `systemd` service on a Hetzner Cloud VPS behind Nginx and Cloudflare.

> **Honest scope:** This is a learning project I build alone, alongside my retraining as a Fachinformatiker (application development). It is a work in progress, not a finished product. The parts described below actually work; everything else lives in the [roadmap](#roadmap).

---

## How it works

```
Browser (mic / text input)
        │  HTTPS
        ▼
Cloudflare → Nginx (reverse proxy)
        │
        ▼
FastAPI  (src/api.py)
  ├─ Whisper (local STT)  →  transcribes uploaded audio
  ├─ Groq API (LLaMA 3.3 70B)  →  generates the reply
  └─ SQLite  →  per-session conversation history
        │
        ▼
JSON response: { transcription, response, session_id }
```

**What the server does *not* do:** speak. The API is text-out only. Offline text-to-speech (pyttsx3) exists, but only in the local CLI mode (`src/main.py`), because a headless cloud server has no audio device. Browser-side speech output is on the roadmap.

The assistant detects the user's language and answers in the same language — German, English and Persian are the ones I actively test.

---

## API

| Endpoint | Method | Rate limit | Description |
|---|---|---|---|
| `/` | GET | — | Minimal web UI (chat + mic recording) |
| `/health` | GET | — | Health check |
| `/chat` | POST | 20/min | `message`, optional `session_id` → AI reply |
| `/voice` | POST | 10/min | `audio` file (max 10 MB), optional `session_id`, `language` → transcription + AI reply |
| `/reset` | POST | — | Clears the conversation history for a `session_id` |

Sessions are identified by a UUID. If no `session_id` is sent, the server creates one and returns it; the web UI stores it in `localStorage`, so conversations survive page reloads — and server restarts, thanks to SQLite.

---

## Security measures

- **Rate limiting** per client IP via `slowapi` (stricter on `/voice`, since Whisper inference is expensive)
- **Upload size limit** of 10 MB on audio files
- **CORS** locked to the production origin
- **Secrets** only via `.env` (permissions `600`), never in code or git
- **HTTPS via Cloudflare** — TLS terminates at the Cloudflare edge, which proxies traffic to Nginx on the origin server. Upgrading to end-to-end TLS (Cloudflare *Full (strict)* with an origin certificate) is planned for the next maintenance window.
- **FastAPI bound to `127.0.0.1`** — only Nginx can reach it; the app process is never exposed publicly
- **Dedicated non-root service user** (`voxbridge`) runs the systemd service (least privilege)
- **Temporary audio files** are deleted after transcription (`finally` block)

---

## Project structure

```
VoxBridge/
├── src/
│   ├── api.py              # FastAPI app — the production entry point
│   ├── ai_engine.py        # LLM backend (Groq; OpenAI/Ollama stubs)
│   ├── memory.py           # SQLite conversation storage
│   ├── speech_to_text.py   # Whisper wrapper (local CLI mode)
│   ├── text_to_speech.py   # pyttsx3 TTS (local CLI mode only)
│   ├── main.py             # Local CLI voice loop (mic → LLM → speaker)
│   └── static/             # Web UI (HTML/CSS/JS)
├── deploy/
│   ├── nginx.conf.txt      # Reverse proxy config
│   └── voxbridge.service.txt  # systemd unit
├── requirements.txt
├── .env.example
└── README.md
```

---

## Quick start (local)

Prerequisites: Python 3.11+, `ffmpeg` (required by Whisper), a free [Groq API key](https://console.groq.com).

```bash
git clone https://github.com/NimaHamedIman/VoxBridge.git
cd VoxBridge

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env            # then add your GROQ_API_KEY
```

Run the web API:

```bash
uvicorn src.api:app --reload --port 8000
```

Open `http://localhost:8000` for the UI, `http://localhost:8000/docs` for the interactive API docs.

Alternatively, run the local CLI voice loop (mic in, spoken answer out):

```bash
python src/main.py
```

### Configuration (`.env`)

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | — | **Required.** Groq API key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model name |
| `AI_BACKEND` | `groq` | LLM backend (`openai`/`ollama` are stubs for now) |
| `WHISPER_MODEL` | `base` | Whisper size: `tiny` / `base` / `small` / `medium` |
| `LANGUAGE` | `de` | Default STT/TTS language for the CLI mode |

---

## Deployment (production)

Runs on Hetzner Cloud (Ubuntu 24.04) as a `systemd` service under a **dedicated non-root user**, behind Nginx with Cloudflare proxying and terminating TLS in front. The actual configs are in [`deploy/`](deploy/).

```bash
sudo cp deploy/voxbridge.service.txt /etc/systemd/system/voxbridge.service
sudo systemctl daemon-reload
sudo systemctl enable --now voxbridge
```

---

## Roadmap

- [ ] Browser-side text-to-speech (Web Speech API) so the web UI can talk back
- [ ] End-to-end TLS: origin certificate + Cloudflare *Full (strict)*
- [ ] Streaming responses for lower perceived latency
- [ ] Speaker recognition (experimental branch: `feature/speaker-recognition`)
- [ ] Automated tests (pytest) for the API endpoints
- [ ] Docker setup
- [ ] User authentication

---

## About

**Nima HamedIman** — retraining as Fachinformatiker Anwendungsentwicklung (IHK) at CBW Hamburg, expected 2027.
Certifications: Oracle OCFA Java · PCAP Python · AWS Cloud Practitioner · PSM I.

[LinkedIn](https://www.linkedin.com/in/nima-hamediman-827a733b4/) · [GitHub](https://github.com/NimaHamedIman)

## License

MIT — see [LICENSE](LICENSE).