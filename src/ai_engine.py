"""AI engine for VoxBridge.

Picks the backend (OpenAI or Ollama) based on AI_BACKEND in .env.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

AI_BACKEND = os.getenv("AI_BACKEND", "ollama").lower()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

if AI_BACKEND == "openai":
    client = OpenAI(api_key=OPENAI_API_KEY)
    MODEL = OPENAI_MODEL
else:
    # Ollama exposes an OpenAI-compatible endpoint, so we reuse the same client.
    client = OpenAI(base_url=f"{OLLAMA_HOST}/v1", api_key="ollama")
    MODEL = OLLAMA_MODEL

SYSTEM_PROMPT = (
    "You are VoxBridge, a voice-first AI assistant designed to be accessible, "
    "empathetic, and human-centered. Keep responses concise and natural, "
    "suitable for being spoken aloud. Adapt to the user's tone and emotional state. "
    "Always reply in the same language the user speaks — "
    "if they speak German, reply in German; if Persian, reply in Persian."
)


def get_response(history: list) -> str:
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
        response = client.chat.completions.create(model=MODEL, messages=messages)
        return response.choices[0].message.content.strip()
    except Exception as error:
        return f"[AI request failed: {error}]"
