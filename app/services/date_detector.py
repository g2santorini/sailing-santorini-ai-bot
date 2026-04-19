import re
from datetime import datetime, timedelta

from dateparser.search import search_dates


MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def build_future_date(day: int, month: int, now: datetime) -> str | None:
    try:
        year = now.year
        candidate = datetime(year, month, day)

        if candidate.date() < now.date():
            candidate = datetime(year + 1, month, day)

        return candidate.strftime("%Y-%m-%d")
    except ValueError:
        return None


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

    # 1) STRICT pattern: 03 May / 3 May
    match = re.search(
        r"\b(\d{1,2})\s+("
        r"jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|"
        r"aug|august|sep|sept|september|oct|october|nov|november|dec|december"
        r")\b",
        text,
    )
    if match:
        day = int(match.group(1))
        month_name = match.group(2)
        month = MONTHS.get(month_name)

        if month:
            parsed = build_future_date(day, month, now)
            if parsed:
                return parsed

    # 2) STRICT pattern: May 03 / May 3
    match = re.search(
        r"\b("
        r"jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|"
        r"aug|august|sep|sept|september|oct|october|nov|november|dec|december"
        r")\s+(\d{1,2})\b",
        text,
    )
    if match:
        month_name = match.group(1)
        day = int(match.group(2))
        month = MONTHS.get(month_name)

        if month:
            parsed = build_future_date(day, month, now)
            if parsed:
                return parsed

    # 3) STRICT numeric pattern: 03/05 or 3/5 or 03-05
    match = re.search(r"\b(\d{1,2})[\/\-.](\d{1,2})\b", text)
    if match:
        day = int(match.group(1))
        month = int(match.group(2))

        parsed = build_future_date(day, month, now)
        if parsed:
            return parsed

    # Only attempt generic date parsing if the message contains actual date-like clues
    date_clues = [
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
        "jan",
        "feb",
        "mar",
        "apr",
        "jun",
        "jul",
        "aug",
        "sep",
        "sept",
        "oct",
        "nov",
        "dec",
        "/",
        "-",
        ".",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]

    has_date_clue = any(clue in original_text for clue in date_clues)

    if not has_date_clue:
        return None

    results = search_dates(
        text,
        languages=["en"],
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