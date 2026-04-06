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

    original_text = text

    text = re.sub(r"\b(\d{1,2})(st|nd|rd|th)\b", r"\1", text)
    text = re.sub(r"\bthe\s+(\d{1,2})\s+of\s+([a-zA-Z]+)\b", r"\1 \2", text)
    text = re.sub(r"\b(\d{1,2})\s+of\s+([a-zA-Z]+)\b", r"\1 \2", text)

    # Only attempt generic date parsing if the message contains actual date-like clues
    date_clues = [
        "january", "february", "march", "april", "may", "june", "july",
        "august", "september", "october", "november", "december",
        "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
        "/", "-", ".",
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
        "δευτέρα", "τρίτη", "τετάρτη", "πέμπτη", "παρασκευή", "σάββατο", "κυριακή"
    ]

    has_date_clue = any(clue in original_text for clue in date_clues)

    if not has_date_clue:
        return None

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

        # Ignore plain numbers like "6" from phrases such as "we are 6 people"
        if re.fullmatch(r"\d{1,2}", cleaned):
            continue

        return parsed_dt.strftime("%Y-%m-%d")

    return None