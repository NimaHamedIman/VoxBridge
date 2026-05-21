"""
ai_engine.py — مغز هوش مصنوعی VoxBridge
بسته به AI_BACKEND در .env: یا OpenAI (ابری) یا Ollama (محلی).
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# کدام مغز را می‌خواهیم؟
AI_BACKEND = os.getenv("AI_BACKEND", "ollama").lower()

# تنظیمات هر دو مغز را برمی‌داریم
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# بسته به انتخاب، کلاینت و مدل را آماده می‌کنیم
if AI_BACKEND == "openai":
    client = OpenAI(api_key=OPENAI_API_KEY)
    MODEL = OPENAI_MODEL
else:  # ollama
    # Ollama درگاه سازگار با OpenAI دارد، پس از همان کلاینت استفاده می‌کنیم
    client = OpenAI(base_url=f"{OLLAMA_HOST}/v1", api_key="ollama")
    MODEL = OLLAMA_MODEL

SYSTEM_PROMPT = (
    "You are VoxBridge, a voice-first AI assistant designed to be accessible, "
    "empathetic, and human-centered. Keep responses concise and natural, "
    "suitable for being spoken aloud. Adapt to the user's tone and emotional state."
)


def get_response(user_input: str) -> str:
    """متنِ کاربر را می‌گیرد و جوابِ مدل را برمی‌گرداند."""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as error:
        return f"[خطا در ارتباط با AI: {error}]"