import re


def detect_date(user_message: str) -> str | None:
    text = user_message.lower().strip()

    month_map = {
        "january": "01",
        "february": "02",
        "march": "03",
        "april": "04",
        "may": "05",
        "june": "06",
        "july": "07",
        "august": "08",
        "september": "09",
        "october": "10",
        "november": "11",
        "december": "12",
        "ιανουαρίου": "01",
        "φεβρουαρίου": "02",
        "μαρτίου": "03",
        "μαρτιου": "03",
        "απριλίου": "04",
        "απριλιου": "04",
        "μαΐου": "05",
        "μαιου": "05",
        "ιουνίου": "06",
        "ιουνιου": "06",
        "ιουλίου": "07",
        "ιουλιου": "07",
        "αυγούστου": "08",
        "αυγουστου": "08",
        "σεπτεμβρίου": "09",
        "σεπτεμβριου": "09",
        "οκτωβρίου": "10",
        "οκτωβριου": "10",
        "νοεμβρίου": "11",
        "νοεμβριου": "11",
        "δεκεμβρίου": "12",
        "δεκεμβριου": "12",
    }

    # 1. YYYY-MM-DD
    match = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month}-{day}"

    # 2. DD/MM/YYYY or DD-MM-YYYY
    match = re.search(r"\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})\b", text)
    if match:
        day, month, year = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"

    # 3. DD/MM (assume 2026)
    match = re.search(r"\b(\d{1,2})[\/\-](\d{1,2})\b", text)
    if match:
        day, month = match.groups()
        return f"2026-{int(month):02d}-{int(day):02d}"

    # 4. 16 June / 16 Ιουνίου
    match = re.search(r"\b(\d{1,2})\s+([a-zA-Zα-ωΑ-Ωΐϊΰάέήίόύώ]+)\b", text)
    if match:
        day, month_name = match.groups()
        month = month_map.get(month_name)
        if month:
            return f"2026-{month}-{int(day):02d}"

    # 5. June 16
    match = re.search(r"\b([a-zA-Z]+)\s+(\d{1,2})\b", text)
    if match:
        month_name, day = match.groups()
        month = month_map.get(month_name)
        if month:
            return f"2026-{month}-{int(day):02d}"

    return None