def detect_tour_key(user_message: str) -> str | None:
    text = user_message.lower()

    if "red" in text and "morning" in text:
        return "red_morning"

    if "red" in text and "sunset" in text:
        return "red_sunset"

    if "gems" in text and "morning" in text:
        return "gems_morning"

    if "gems" in text and "sunset" in text:
        return "gems_sunset"

    if "platinum" in text and "morning" in text:
        return "platinum_morning"

    if "platinum" in text and "sunset" in text:
        return "platinum_sunset"

    if "diamond" in text and "morning" in text:
        return "diamond_morning"

    if "diamond" in text and "sunset" in text:
        return "diamond_sunset"

    if "lagoon" in text and "morning" in text:
        return "lagoon_380_400_morning"

    if "lagoon" in text and "sunset" in text:
        return "lagoon_380_400_sunset"

    if "emily" in text and "morning" in text:
        return "emily_morning"

    if "emily" in text and "sunset" in text:
        return "emily_sunset"

    if "ferretti 731" in text and "morning" in text:
        return "ferretti_731_morning"

    if "ferretti 731" in text and "sunset" in text:
        return "ferretti_731_sunset"

    if "ferretti 55" in text and "morning" in text:
        return "ferretti_55_morning"

    if "ferretti 55" in text and "sunset" in text:
        return "ferretti_55_sunset"

    return None