import re


def detect_cruise_type_intent(
    user_message: str, history: list[dict] | None = None
) -> str | None:
    text = user_message.lower()

    private_keywords = [
        "private",
        "privately",
        "just for us",
        "only for us",
        "for our group only",
    ]

    shared_keywords = [
        "shared",
        "semi private",
        "semi-private",
        "join",
        "group cruise",
    ]

    has_private = any(k in text for k in private_keywords)
    has_shared = any(k in text for k in shared_keywords)

    if has_private and not has_shared:
        return "private"

    if has_shared and not has_private:
        return "shared"

    if history:
        for item in reversed(history[-6:]):
            if item.get("role") != "user":
                continue

            previous_text = item.get("content", "").lower()

            prev_has_private = any(k in previous_text for k in private_keywords)
            prev_has_shared = any(k in previous_text for k in shared_keywords)

            if prev_has_private and not prev_has_shared:
                return "private"

            if prev_has_shared and not prev_has_private:
                return "shared"

    return None


def detect_passenger_count(
    user_message: str, history: list[dict] | None = None
) -> int | None:
    texts_to_check = [user_message.lower()]

    if history:
        for item in reversed(history[-8:]):
            if item.get("role") == "user":
                previous_text = item.get("content", "").lower()
                if previous_text:
                    texts_to_check.append(previous_text)

    patterns = [
        r"\bwe are (\d+)\b",
        r"\bwe have (\d+)\b",
        r"\bgroup of (\d+)\b",
        r"\bparty of (\d+)\b",
        r"\bfor (\d+) people\b",
        r"\bfor (\d+) persons\b",
        r"\bfor (\d+) guests\b",
        r"\b(\d+) people\b",
        r"\b(\d+) persons\b",
        r"\b(\d+) guests\b",
        r"\b(\d+) pax\b",
    ]

    for text in texts_to_check:
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))

    return None