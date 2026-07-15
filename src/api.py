"""
VoxBridge API _ SastAPI server .
Receives audio or text, returns AI response as text.
"""
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import sys
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
    
    

    

@app.post("/reset")
async def reset(session_id: str = Form(...)):
    clear_history(session_id)
    return {"status": "Conversation reset.", "session_id": session_id}
