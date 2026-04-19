import os
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(os.getenv("CHAT_DB_PATH", "chat_logs.db"))

print(f"[CHAT LOGGER] Using DB: {DB_PATH.resolve()}")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # ✅ Create table if not exists (with session_id)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            session_id TEXT,
            user_message TEXT NOT NULL,
            bot_reply TEXT NOT NULL,
            fallback INTEGER NOT NULL DEFAULT 0,
            detected_tour TEXT,
            language TEXT
        )
    """)

    # ✅ Ensure column exists (for old DBs)
    try:
        cursor.execute("ALTER TABLE chat_logs ADD COLUMN session_id TEXT")
    except:
        pass

    conn.commit()
    conn.close()


def save_chat_log(
    user_message: str,
    bot_reply: str,
    fallback: bool = False,
    detected_tour: str | None = None,
    language: str | None = None,
    session_id: str | None = None,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO chat_logs (
            timestamp,
            session_id,
            user_message,
            bot_reply,
            fallback,
            detected_tour,
            language
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        session_id or "unknown",
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
        SELECT id, timestamp, session_id, user_message, bot_reply, fallback, detected_tour, language
        FROM chat_logs
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_chat_sessions(
    limit: int = 1000,
    from_date: str | None = None,
    to_date: str | None = None,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, timestamp, session_id, user_message, bot_reply, fallback, detected_tour, language
        FROM chat_logs
        ORDER BY id ASC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    sessions_map = {}

    for row in rows:
        log = dict(row)
        session_id = log.get("session_id") or "unknown"

        if session_id not in sessions_map:
            sessions_map[session_id] = {
                "session_id": session_id,
                "start_time": log["timestamp"],
                "last_activity": log["timestamp"],
                "messages_count": 0,
                "conversation": [],
                "fallback_count": 0,
                "language": log.get("language"),
                "detected_tours": set(),
            }

        session = sessions_map[session_id]

        session["last_activity"] = log["timestamp"]
        session["messages_count"] += 1

        if log.get("fallback"):
            session["fallback_count"] += 1

        if log.get("detected_tour"):
            session["detected_tours"].add(log["detected_tour"])

        if not session.get("language") and log.get("language"):
            session["language"] = log["language"]

        session["conversation"].append({
            "timestamp": log["timestamp"],
            "user_message": log["user_message"],
            "bot_reply": log["bot_reply"],
            "fallback": bool(log["fallback"]),
            "detected_tour": log.get("detected_tour"),
            "language": log.get("language"),
        })

    sessions = []
    for session in sessions_map.values():
        session["detected_tours"] = sorted(list(session["detected_tours"]))
        sessions.append(session)

    if from_date or to_date:
        filtered_sessions = []

        for session in sessions:
            last_activity = session.get("last_activity", "")
            last_date = last_activity[:10] if last_activity else ""

            if from_date and last_date < from_date:
                continue
            if to_date and last_date > to_date:
                continue

            filtered_sessions.append(session)

        sessions = filtered_sessions

    sessions.sort(key=lambda x: x["last_activity"], reverse=True)

    return sessions