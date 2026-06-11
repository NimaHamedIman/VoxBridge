"""
VoxBridge API _ SastAPI server .
Receives audio or text, returns AI response as text.
"""
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from ai_engine import get_response
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

conversation_history = []

@app.get("/")
def health_check():
    return {"status": "VoxBridge API is running", "version": "0.2.0"}

@app.post("/chat")
async def chat(message: str = Form(...)):
    global conversation_history

    response = get_response(message, conversation_history)
    conversation_history.append({"role": "user", "content": message})
    conversation_history.append({"role": "assistant", "content": response})

    if len(conversation_history) > 20:
        conversation_history = conversation_history[-20:]
    return {"response": response}

@app.post("/reset")
async def reset():
    global conversation_history
    conversation_history = []
    return {"status": "Conversation history reset."}
