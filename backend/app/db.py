import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

DB_PATH = str(Path(__file__).resolve().parents[2] / "omnicore.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS auth_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(conversation_id) REFERENCES conversations(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        memory_key TEXT NOT NULL,
        memory_value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, memory_key)
    )''')
    conn.commit()
    conn.close()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def load_user_memory(user_id: str) -> dict[str, Any]:
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT memory_key, memory_value FROM user_memory WHERE user_id = ?",
            (user_id,),
        ).fetchall()

    memory: dict[str, Any] = {}
    for row in rows:
        key = str(row["memory_key"])
        raw_value = row["memory_value"]
        if key in {"preferences", "goals"}:
            memory[key] = [item for item in str(raw_value).split("||") if item]
        else:
            memory[key] = str(raw_value)

    return memory


def save_user_memory(user_id: str, memory: dict[str, Any]):
    if not isinstance(memory, dict) or not memory:
        return

    with get_db() as conn:
        cursor = conn.cursor()
        for key, value in memory.items():
            if value in (None, "", []):
                continue

            if isinstance(value, list):
                stored_value = "||".join(str(item).strip() for item in value if str(item).strip())
                if not stored_value:
                    continue
            else:
                stored_value = str(value).strip()
                if not stored_value:
                    continue

            cursor.execute(
                '''
                INSERT INTO user_memory (user_id, memory_key, memory_value, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, memory_key)
                DO UPDATE SET memory_value = excluded.memory_value, updated_at = CURRENT_TIMESTAMP
                ''',
                (user_id, key, stored_value),
            )
        conn.commit()


def clear_user_memory(user_id: str | None = None):
    with get_db() as conn:
        cursor = conn.cursor()
        if user_id:
            cursor.execute("DELETE FROM user_memory WHERE user_id = ?", (user_id,))
        else:
            cursor.execute("DELETE FROM user_memory")
        conn.commit()
