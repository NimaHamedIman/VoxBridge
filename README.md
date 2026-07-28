# 🎙️ VoxBridge

**A voice-first AI assistant, built as a self-hosted web API — live at [voice.nimaserver.xyz](https://voice.nimaserver.xyz).**

![VoxBridge](src/static/demo.gif)

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Whisper](https://img.shields.io/badge/OpenAI-Whisper-412991?style=flat-square)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-F55036?style=flat-square)
![Version](https://img.shields.io/badge/Version-0.6.0-blue?style=flat-square)
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

**What the server does *not* do:** speak. The API is text-out only — the reply comes back as JSON, nothing more. Speech happens in the browser instead: the web UI reads the response aloud via the Web Speech API. Offline text-to-speech (pyttsx3) still exists for the local CLI mode (`src/main.py`), because that one runs on real hardware with a sound card; a headless cloud server has neither, and no reason to be given one when the browser already can.

The web UI itself is an orb-centred interface: an animated Canvas 2D sphere that shifts between four states — idle, listening, thinking, speaking — next to a pipeline strip showing which stage (upload, Whisper, LLaMA, done) is currently running. Voice and text input both feed the same `/voice` and `/chat` endpoints.

The assistant detects the user's language and answers in the same language — German, English and Persian are the ones I actively test.

---

## API

| Endpoint | Method | Rate limit | Description |
|---|---|---|---|
| `/` | GET | — | Web UI (orb interface, voice + text input) |
| `/health` | GET | — | Health check |
| `/chat` | POST | 20/min | `message`, optional `session_id` → AI reply |
| `/voice` | POST | 10/min | `audio` file (max 10 MB), optional `session_id`, `language` → transcription + AI reply |
| `/reset` | POST | 10/min | Clears the conversation history for a `session_id` |

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

## Design decisions

**TTS runs in the browser, not on the server.** The VPS shares its CPU and RAM with other services running on the same box, so adding speech synthesis there would compete with Whisper for resources on every request. The Web Speech API runs on the user's own device and costs the server nothing — the tradeoff is that voice quality depends on what the OS has installed (see [Known limitations](#known-limitations)).

**The orb outline is built from three superimposed sine waves at frequencies 3, 5 and 7**, not one. A single wave produces a shape that visibly repeats itself every cycle, which reads as mechanical. Three non-harmonic frequencies combined never realign into the same pattern, so the outline never quite retraces itself — that's what makes it read as alive rather than looping.

**The pipeline strip lights up "Whisper" and "LLaMA" at the same time.** Transcription and generation both happen inside the single HTTP request behind `/voice`, so the server has no way to report that it finished one stage and started the next — from the client's perspective they're simultaneous. This is the main reason WebSockets are on the roadmap: a persistent connection would let the server push real progress instead of the UI approximating it.

---

## Known limitations

- **Speech output quality varies by OS.** The Web Speech API uses whatever voices are installed on the user's system — some sound natural, others robotic, and availability differs between Windows, macOS and mobile browsers.
- **Rate limiting keys on the Cloudflare edge IP**, not the real client IP, since that's what reaches Nginx/FastAPI by default. Two users behind the same Cloudflare PoP could affect each other's limits.
- **No authentication yet.** Sessions are identified by an unguessable UUID stored in `localStorage`. That's enough to keep strangers from stumbling into each other's conversations, but a leaked session ID would expose that conversation's full history — there's no password or account behind it.
- **Whisper runs on CPU.** The first voice request after a service restart takes roughly a minute while the model loads into memory; subsequent requests are fast.

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
│   └── static/              # Web UI
│       ├── index.html       # Markup + meta tags
│       ├── style.css        # Styling
│       ├── app.js           # UI logic, state, API calls
│       ├── orb.js           # Canvas 2D orb animation
│       └── icon.svg         # Favicon
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

- [x] Browser-side text-to-speech (Web Speech API) so the web UI can talk back
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