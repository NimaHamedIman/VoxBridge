import json
import os

MEMORY_FILE = "memory.json"


def load_history() -> list:
    """Load conversation history from disk, or return an empty list if missing."""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(history: list) -> None:
    """Persist conversation history as JSON."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
