"""
VoxBridge API _ SastAPI server .
Receives audio or text, returns AI response as text.
"""
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import sys
import whisper
import uuid
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from ai_engine import get_response
from memory import init_db, save_message, get_history, clear_history
from dotenv import load_dotenv
load_dotenv()


app = FastAPI(
    title="VoxBridge API",
    description="Voice-First AI Assistant API",
    version="0.2.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

init_db()

@app.get("/health")
def health_check():
    return {"status": "VoxBridge API is running", "version": "0.2.0"}

 
@app.get("/")
def server_ui():
    return FileResponse(Path(__file__).parent / "static" / "index.html")

@app.post("/chat")
async def chat(message: str = Form(...), session_id: str = Form(None)):
    if not session_id:
        session_id = str(uuid.uuid4())
    history = get_history(session_id)

    response = get_response(message, history)
    save_message(session_id, "user", message)
    save_message(session_id, "assistant", response)

    return {"response": response, "session_id": session_id}

_whisper_model = None

def get_whisper(): 
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model(os.getenv("WHISPER_MODEL", "base"))
    return _whisper_model
 
 
 

_whisper_model = None

def get_whisper():
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model(os.getenv("WHISPER_MODEL", "base"))
    return _whisper_model


@app.post("/voice")
async def voice(audio: UploadFile = File(...), session_id: str = Form(None)):
    if not session_id:
        session_id = str(uuid.uuid4())

    # Save uploaded audio to a temporary file
    suffix = os.path.splitext(audio.filename or "clip.webm")[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    try:
        # voice → text
        model = get_whisper()
        result = model.transcribe(tmp_path, fp16=False)
        user_text = result.get("text", "").strip()

        if not user_text:
            return {"error": "Keine Sprache erkannt.", "session_id": session_id}

        # AI response
        history = get_history(session_id)
        response = get_response(user_text, history)
        save_message(session_id, "user", user_text)
        save_message(session_id, "assistant", response)

        return {
            "transcription": user_text,
            "response": response,
            "session_id": session_id
        }
    finally:
        # Clean up temporary file
        os.remove(tmp_path)
 
 
 
 
 
 
 
 
 
 
    

@app.post("/reset")
async def reset(session_id: str = Form(...)):
    clear_history(session_id)
    return {"status": "Conversation reset.", "session_id": session_id}
