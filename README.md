# 🎙️ VoxBridge — AI Voice Assistant

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)
![Groq](https://img.shields.io/badge/Groq_API-LLaMA_3.3-F55036?style=flat-square)
![Whisper](https://img.shields.io/badge/OpenAI-Whisper-412991?style=flat-square&logo=openai&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-Ubuntu_24.04-E95420?style=flat-square&logo=ubuntu&logoColor=white)
![Status](https://img.shields.io/badge/Status-Live_Production-brightgreen?style=flat-square)

**A modular, production-grade AI voice assistant — live on Hetzner Cloud 24/7.**

[Live Demo](#live-demo) · [Architecture](#architecture) · [Quick Start](#quick-start) · [Deployment](#deployment)

</div>

---

## 📌 What is VoxBridge?

VoxBridge is a **voice-first AI assistant** that combines speech recognition, large language model processing, and text-to-speech output into a clean, modular pipeline — deployed as a production service on a Linux cloud server.

> Built from scratch as a personal project to deepen practical skills in Python, REST APIs, cloud deployment, and AI integration.

---

## ✨ Key Features

| Feature | Technology |
|--------|-----------|
| 🎤 Speech-to-Text | OpenAI Whisper (local inference) |
| 🧠 AI Processing | Groq API · LLaMA 3.3 70B |
| 🔊 Text-to-Speech | pyttsx3 (offline TTS) |
| 🌐 REST API | FastAPI |
| 💾 Conversation Memory | SQLite (persistent across restarts) |
| 🔒 HTTPS & Security | Nginx · Let's Encrypt · Cloudflare CDN |
| 🚀 Cloud Deployment | Hetzner Cloud · Ubuntu 24.04 · systemd |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                  CLIENT                         │
│         (Browser / Mobile / CLI)                │
└────────────────────┬────────────────────────────┘
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────┐
│   Cloudflare CDN  →  Nginx Reverse Proxy        │
│              (SSL/TLS Termination)              │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│             FastAPI Application                 │
│                                                 │
│  ┌─────────────┐  ┌───────────┐  ┌──────────┐  │
│  │   Whisper   │→ │ Groq API  │→ │ pyttsx3  │  │
│  │ (STT Layer) │  │(LLM Layer)│  │(TTS Layer)│  │
│  └─────────────┘  └───────────┘  └──────────┘  │
│                         │                       │
│                   ┌─────▼──────┐                │
│                   │   SQLite   │                │
│                   │  (Memory)  │                │
│                   └────────────┘                │
└─────────────────────────────────────────────────┘
           systemd service · Ubuntu 24.04
              Hetzner Cloud VPS
```

**Design principles:**
- **Separation of concerns** — each layer (STT, LLM, TTS) is an independent module
- **Stateful conversations** — SQLite stores session history, surviving server restarts
- **Production-hardened** — runs as a `systemd` service with automatic restart on failure
- **Zero secrets in code** — all credentials via `.env` / `.gitignore`

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- A [Groq API key](https://console.groq.com) (free tier available)
- `ffmpeg` installed (required by Whisper)

### Installation

```bash
# Clone the repository
git clone https://github.com/nimaMira/VoxBridge.git
cd VoxBridge

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### Configuration

```env
# .env
GROQ_API_KEY=your_groq_api_key_here
WHISPER_MODEL=base          # tiny / base / small / medium
DATABASE_URL=voxbridge.db
HOST=0.0.0.0
PORT=8000
```

### Run Locally

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000` in your browser — the API docs are at `/docs`.

---

## 🌍 Deployment

### Hetzner Cloud (Ubuntu 24.04) — Production Setup

**1. Nginx Reverse Proxy**

```nginx
server {
    listen 443 ssl;
    server_name your-domain.xyz;

    ssl_certificate     /etc/letsencrypt/live/your-domain.xyz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.xyz/privkey.pem;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
    }
}
```

**2. systemd Service**

```ini
# /etc/systemd/system/voxbridge.service
[Unit]
Description=VoxBridge AI Voice Assistant
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/VoxBridge
ExecStart=/home/ubuntu/VoxBridge/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
EnvironmentFile=/home/ubuntu/VoxBridge/.env

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable voxbridge
sudo systemctl start voxbridge

# Check status
sudo systemctl status voxbridge
```

**3. SSL Certificate (Let's Encrypt)**

```bash
sudo certbot --nginx -d your-domain.xyz
```

---

## 🔒 Security

- All API keys stored in `.env` — never committed to version control
- Nginx handles SSL termination — FastAPI only exposed on `127.0.0.1`
- Cloudflare CDN as additional security and DDoS protection layer
- UFW firewall: only ports 22 (SSH), 80, 443 open

---

## 📁 Project Structure

```
VoxBridge/
├── main.py              # FastAPI app entry point
├── stt/
│   └── whisper_handler.py   # Speech-to-Text module
├── llm/
│   └── groq_handler.py      # Groq API / LLM module
├── tts/
│   └── pyttsx3_handler.py   # Text-to-Speech module
├── memory/
│   └── database.py          # SQLite conversation memory
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🛠️ Tech Stack

**Backend:** Python 3.11 · FastAPI · Uvicorn  
**AI/ML:** OpenAI Whisper · Groq API (LLaMA 3.3 70B) · pyttsx3  
**Database:** SQLite  
**Infrastructure:** Hetzner Cloud · Ubuntu 24.04 · Nginx · systemd  
**Security:** Let's Encrypt · Cloudflare · UFW  
**Tools:** Git · VS Code · Python-dotenv  

---

## 🗺️ Roadmap

- [ ] Web frontend (React) for browser-based voice interaction
- [ ] Multi-language support (German / English / Persian)
- [ ] Streaming responses for lower perceived latency
- [ ] Docker containerization for easier deployment
- [ ] User authentication and session management

---

## 👤 About the Author

**Nima HamedIman**  
IT Retraining — Fachinformatiker Anwendungsentwicklung (IHK) · CBW Hamburg · Expected 2027  
Certifications: Oracle OCFA Java · PCAP Python · AWS Cloud Practitioner · PSM I Scrum

🔗 [LinkedIn](https://www.linkedin.com/in/nima-hamediman-827a733b4/) · [GitHub](https://github.com/NimaHamedIman)

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
<sub>Built with ❤️ and a lot of Linux terminal sessions</sub>
</div>
