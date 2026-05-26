

import json
import os

MEMORY_FILE = "memory.json"


def load_history() -> list:
    """اگر فایل حافظه باشد آن را می‌خواند، وگرنه لیست خالی می‌دهد."""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(history: list) -> None:
    """تاریخچهٔ مکالمه را در فایل JSON ذخیره می‌کند."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)