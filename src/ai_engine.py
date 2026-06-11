"""
AI Engine — communicates with the chosen LLM backend.
Supports Groq (free), OpenAI, and Ollama (local).
"""
import os
from dotenv import load_dotenv
load_dotenv()

SYSTEM_PROMPT = """You are VoxBridge, a Voice-frist AI assistant.
you are empathetic, warm , and human-centered.
keep responses short and natural _ they will be spoken aloud.
Detect the user's language and always respond in the same language.
If the user speaks German, respond in German.
If the user speaks Persian, respond in Persian.
If the user speaks English, respond in English."""

def get_response(user_message: str, history: list = None) -> str:
    backend = os.getenv("AI_BACKEND", "groq")

    if backend == "groq":
        return get_groq_response(user_message, history)
    elif backend == "openai":
        return _get_openai_response(user_message, history)
    elif backend == "ollama":
        return _get_ollama_response(user_message, history)
    else:
        raise ValueError(f"Unsupported AI_BACKEND: {backend}")


def get_groq_response(user_message: str, history: list = None) -> str:
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "Error: GROQ_API_KEY not found in .env file."
        from groq import Groq
        client = Groq(api_key=api_key)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        response = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=messages,
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"Error communicating with Groq: {str(e)}"


def _get_openai_response(user_message: str, history: list = None) -> str:
    raise NotImplementedError("OpenAI backend is not implemented yet.")


def _get_ollama_response(user_message: str, history: list = None) -> str:
    raise NotImplementedError("Ollama backend is not implemented yet.")
