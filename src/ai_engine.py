"""
AI Engine — communicates with the chosen LLM backend.
Supports Groq (free), OpenAI, and Ollama (local).
"""
import os
import re
from dotenv import load_dotenv
load_dotenv()

SYSTEM_PROMPT = """You are VoxBridge, a voice assistant. Everything you
write is read out loud by a speech synthesiser, so write the way people
speak, not the way people write.

- Answer in two or three short sentences. Four at the very most.
- Never use lists, bullet points, headings, markdown or emoji.
- Write abbreviations out in full: "zum Beispiel" instead of "z.B.",
  "und so weiter" instead of "usw.", "circa" instead of "ca." — a speech
  synthesiser mispronounces the shortened forms.
- Prefer short main clauses over long subordinate constructions.
- Be warm and direct. Ask a short follow-up question when it genuinely
  helps, but not in every reply.
- Detect the user's language and answer in that language. German is the
  primary language."""

def clean_name(raw):
    """A name becomes part of the system prompt, so it is untrusted input.
    Collapsing it to a single short line is what stops a "name" from
    carrying instructions of its own (prompt injection)."""
    if not raw:
        return None
    name = raw.strip()
    name = name.replace("\r", " ").replace("\n", " ")
    name = re.sub(r"\s+", " ", name).strip()
    name = name[:40].strip()
    return name or None


def build_system_prompt(user_name=None, assistant_name=None) -> str:
    prompt = SYSTEM_PROMPT
    assistant_name = clean_name(assistant_name)
    user_name = clean_name(user_name)

    if assistant_name:
        prompt += f"\n\nYour name is {assistant_name}. Answer to it naturally."
    if user_name:
        prompt += f"\n\nThe person you are talking to is called {user_name}. Use their name occasionally, not in every reply."

    return prompt


def get_response(user_message: str, history: list = None, user_name=None, assistant_name=None) -> str:
    backend = os.getenv("AI_BACKEND", "groq")

    if backend == "groq":
        return get_groq_response(user_message, history, user_name=user_name, assistant_name=assistant_name)
    elif backend == "openai":
        return _get_openai_response(user_message, history)
    elif backend == "ollama":
        return _get_ollama_response(user_message, history)
    else:
        raise ValueError(f"Unsupported AI_BACKEND: {backend}")


def get_groq_response(user_message: str, history: list = None, user_name=None, assistant_name=None) -> str:
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "Error: GROQ_API_KEY not found in .env file."
        from groq import Groq
        client = Groq(api_key=api_key)
        messages = [{"role": "system", "content": build_system_prompt(user_name=user_name, assistant_name=assistant_name)}]
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
        print(f"Groq request failed: {e}")
        return "Entschuldigung, ich kann gerade nicht antworten. Bitte versuche es noch einmal."
        


def _get_openai_response(user_message: str, history: list = None) -> str:
    raise NotImplementedError("OpenAI backend is not implemented yet.")


def _get_ollama_response(user_message: str, history: list = None) -> str:
    raise NotImplementedError("Ollama backend is not implemented yet.")
