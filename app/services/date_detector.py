import re
from datetime import datetime, timedelta

from dateparser.search import search_dates


def detect_date(user_message: str) -> str | None:
    text = user_message.lower().strip()
    now = datetime.now()

    if "day after tomorrow" in text:
        return (now + timedelta(days=2)).strftime("%Y-%m-%d")

    if "tomorrow" in text:
        return (now + timedelta(days=1)).strftime("%Y-%m-%d")

    if "today" in text:
        return now.strftime("%Y-%m-%d")

    text = re.sub(r"\b(\d{1,2})(st|nd|rd|th)\b", r"\1", text)
    text = re.sub(r"\bthe\s+(\d{1,2})\s+of\s+([a-zA-Z]+)\b", r"\1 \2", text)
    text = re.sub(r"\b(\d{1,2})\s+of\s+([a-zA-Z]+)\b", r"\1 \2", text)

    results = search_dates(
        text,
        languages=["en", "el"],
        settings={
            "PREFER_DATES_FROM": "future",
            "DATE_ORDER": "DMY",
            "RELATIVE_BASE": now,
        },
    )

    if not results:
        return None

    for matched_text, parsed_dt in results:
        cleaned = matched_text.strip().lower()

        if len(cleaned) < 2:
            continue

        return parsed_dt.strftime("%Y-%m-%d")

    return None