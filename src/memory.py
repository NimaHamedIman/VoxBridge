"""
Memory modeule _ Persistent conversation storage using SQLite.
Conversations survive server restarts.
"""
import re
import sqlite3
import os
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).parent.parent / "data" / "memory.db"

MAX_FACTS = 30
MAX_FACT_LENGTH = 200

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(""" CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    cursor.execute(""" CREATE TABLE IF NOT EXISTS facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_key TEXT NOT NULL,
            fact TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_key, fact)
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_facts_user_key ON facts (user_key)
    """)
    conn.commit()
    conn.close()



def save_message(session_id: str, role: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO conversations (session_id, role, content, timestamp)
        VALUES (?, ?, ?, ?)
    """, (session_id, role, content, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()



def get_history(session_id: str, limit: int = 20) -> list:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT role, content FROM conversations
        WHERE session_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (session_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    rows.reverse()
    
    return [{"role": row[0], "content": row[1]} for row in rows]

def clear_history(session_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM conversations
        WHERE session_id = ?
    """, (session_id,))

    conn.commit()
    conn.close()


def _clean_fact(text: str):
    # A saved fact gets written back into the system prompt on every future
    # request, indefinitely, so it must be normalized to a single bounded
    # line rather than trusted as-is.
    cleaned = text.replace("\r", " ").replace("\n", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = cleaned[:MAX_FACT_LENGTH]

    if not cleaned:
        return None

    return cleaned


def save_fact(user_key: str, fact: str) -> str:
    cleaned = _clean_fact(fact)
    if cleaned is None:
        return "The fact was empty after cleaning and was not saved."

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM facts
        WHERE user_key = ?
    """, (user_key,))

    count = cursor.fetchone()[0]

    if count >= MAX_FACTS:
        conn.close()
        return f"Fact limit of {MAX_FACTS} reached; the fact was not saved."

    cursor.execute("""
        INSERT OR IGNORE INTO facts (user_key, fact, created_at)
        VALUES (?, ?, ?)
    """, (user_key, cleaned, datetime.now().isoformat()))

    # rowcount must be read before commit, and the result fed straight back
    # to the model as its tool response, so it has to truthfully reflect
    # whether INSERT OR IGNORE actually inserted a row or silently skipped
    # a duplicate — otherwise the model reports success for a no-op.
    inserted = cursor.rowcount == 1

    conn.commit()
    conn.close()

    if inserted:
        return "Fact saved."
    return "That fact is already known; no new fact was saved."


def get_facts(user_key: str) -> list:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT fact FROM facts
        WHERE user_key = ?
        ORDER BY id ASC
    """, (user_key,))

    rows = cursor.fetchall()
    conn.close()

    return [row[0] for row in rows]


def forget_facts(user_key: str, contains: str = None) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if contains is None:
        cursor.execute("""
            DELETE FROM facts
            WHERE user_key = ?
        """, (user_key,))
    else:
        cursor.execute("""
            DELETE FROM facts
            WHERE user_key = ? AND fact LIKE ?
        """, (user_key, f"%{contains}%"))

    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    return deleted

