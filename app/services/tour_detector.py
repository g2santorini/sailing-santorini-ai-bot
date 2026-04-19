def is_sunset(text: str) -> bool:
    return any(word in text for word in ["sunset", "afternoon", "evening", "tonight"])


def is_morning(text: str) -> bool:
    return "morning" in text


def detect_tour_key(user_message: str) -> str | None:
    text = user_message.lower()

    # ===== SHARED =====
    if "red" in text:
        if is_morning(text):
            return "red_morning"
        if is_sunset(text):
            return "red_sunset"

    if "gems" in text:
        if is_morning(text):
            return "gems_morning"
        if is_sunset(text):
            return "gems_sunset"

    if "platinum" in text:
        if is_morning(text):
            return "platinum_morning"
        if is_sunset(text):
            return "platinum_sunset"

    if "diamond" in text:
        if is_morning(text):
            return "diamond_morning"
        if is_sunset(text):
            return "diamond_sunset"

    # ===== PRIVATE =====
    if "lagoon" in text:
        if is_morning(text):
            return "lagoon_380_400_morning"
        if is_sunset(text):
            return "lagoon_380_400_sunset"

    if "emily" in text:
        if is_morning(text):
            return "emily_morning"
        if is_sunset(text):
            return "emily_sunset"

    if "ferretti 731" in text:
        if is_morning(text):
            return "ferretti_731_morning"
        if is_sunset(text):
            return "ferretti_731_sunset"

    if "ferretti 55" in text or "ferreti 55" in text or "my way" in text:
        if is_morning(text):
            return "ferretti_55_morning"
        if is_sunset(text):
            return "ferretti_55_sunset"

    # ===== BASE FALLBACK =====
    if "ferretti 731" in text:
        return "ferretti_731"

    if "ferretti 55" in text or "ferreti 55" in text or "my way" in text:
        return "ferretti_55"

    if "emily" in text:
        return "emily"

    if "lagoon" in text:
        return "lagoon_380_400"

    if "diamond" in text:
        return "diamond"

    if "platinum" in text:
        return "platinum"

    if "gems" in text:
        return "gems"

    if "red" in text:
        return "red"

    return None