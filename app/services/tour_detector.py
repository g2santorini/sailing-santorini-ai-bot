def is_sunset(text: str) -> bool:
    return (
        "sunset" in text
        or "afternoon" in text
        or "evening" in text
        or "tonight" in text
    )


def is_morning(text: str) -> bool:
    return "morning" in text


def detect_tour_key(user_message: str) -> str | None:
    text = user_message.lower()

    if "red" in text and is_morning(text):
        return "red_morning"

    if "red" in text and is_sunset(text):
        return "red_sunset"

    if "gems" in text and is_morning(text):
        return "gems_morning"

    if "gems" in text and is_sunset(text):
        return "gems_sunset"

    if "platinum" in text and is_morning(text):
        return "platinum_morning"

    if "platinum" in text and is_sunset(text):
        return "platinum_sunset"

    if "diamond" in text and is_morning(text):
        return "diamond_morning"

    if "diamond" in text and is_sunset(text):
        return "diamond_sunset"

    if "lagoon" in text and is_morning(text):
        return "lagoon_380_400_morning"

    if "lagoon" in text and is_sunset(text):
        return "lagoon_380_400_sunset"

    if "emily" in text and is_morning(text):
        return "emily_morning"

    if "emily" in text and is_sunset(text):
        return "emily_sunset"

    if "ferretti 731" in text and is_morning(text):
        return "ferretti_731_morning"

    if "ferretti 731" in text and is_sunset(text):
        return "ferretti_731_sunset"

    if "ferretti 55" in text and is_morning(text):
        return "ferretti_55_morning"

    if "ferretti 55" in text and is_sunset(text):
        return "ferretti_55_sunset"

    # Fallback χωρίς period
    if "ferretti 55" in text:
        return "ferretti_55_sunset"

    if "ferretti 731" in text:
        return "ferretti_731_sunset"

    if "emily" in text:
        return "emily_sunset"

    if "lagoon" in text:
        return "lagoon_380_400_sunset"

    if "diamond" in text:
        return "diamond_sunset"

    if "platinum" in text:
        return "platinum_sunset"

    if "gems" in text:
        return "gems_sunset"

    if "red" in text:
        return "red_sunset"

    return None