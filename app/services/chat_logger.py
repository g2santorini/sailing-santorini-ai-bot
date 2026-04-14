import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("chat_logs.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_message TEXT NOT NULL,
            bot_reply TEXT NOT NULL,
            fallback INTEGER NOT NULL DEFAULT 0,
            detected_tour TEXT,
            language TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_chat_log(
    user_message: str,
    bot_reply: str,
    fallback: bool = False,
    detected_tour: str | None = None,
    language: str | None = None,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO chat_logs (
            timestamp,
            user_message,
            bot_reply,
            fallback,
            detected_tour,
            language
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        user_message,
        bot_reply,
        1 if fallback else 0,
        detected_tour,
        language,
    ))

    conn.commit()
    conn.close()


def get_chat_logs(limit: int = 100):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, timestamp, user_message, bot_reply, fallback, detected_tour, language
        FROM chat_logs
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]