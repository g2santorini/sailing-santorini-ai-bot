from app.services.tour_detector import detect_tour_key
from app.services.date_detector import detect_date


def detect_tour_key_from_history_text(text: str) -> str | None:
    detected = detect_tour_key(text)
    if detected:
        return detected

    lowered = text.lower()

    if "diamond sunset" in lowered:
        return "diamondsunset"
    if "diamond morning" in lowered:
        return "diamondmorning"
    if "gems sunset" in lowered:
        return "gemssunset"
    if "gems morning" in lowered:
        return "gemsmorning"
    if "platinum sunset" in lowered:
        return "platinumsunset"
    if "platinum morning" in lowered:
        return "platinummorning"
    if "red sunset" in lowered:
        return "redsunset"
    if "red morning" in lowered:
        return "redmorning"

    return None


def has_recent_availability_context(
    history: list[dict] | None = None,
    is_availability_request_fn=None,
    detect_period_fn=None,
) -> bool:
    if not history:
        return False

    for item in reversed(history[-8:]):
        if item.get("role") != "user":
            continue

        content = item.get("content", "").strip()
        if not content:
            continue

        if is_availability_request_fn and is_availability_request_fn(content):
            return True

        if detect_date(content):
            return True

        if detect_tour_key(content):
            return True

        if detect_period_fn and detect_period_fn(content):
            return True

    return False


def get_last_tour_and_date_from_history(
    user_message: str,
    history: list[dict]
) -> tuple[str | None, str | None]:
    current_tour = detect_tour_key_from_history_text(user_message)
    current_date = detect_date(user_message)

    if current_tour and current_date:
        return current_tour, current_date

    # First preference:
    # find the most recent USER message that contains BOTH tour and date together.
    if history:
        for item in reversed(history[-10:]):
            if item.get("role") != "user":
                continue

            content = item.get("content", "").strip()
            if not content:
                continue

            hist_tour = detect_tour_key_from_history_text(content)
            hist_date = detect_date(content)

            if hist_tour and hist_date:
                return current_tour or hist_tour, current_date or hist_date

    # Second preference:
    # if user already gave one part now, complete it from the most recent USER message
    # that contains the missing part.
    if history:
        if not current_tour:
            for item in reversed(history[-10:]):
                if item.get("role") != "user":
                    continue

                content = item.get("content", "").strip()
                if not content:
                    continue

                hist_tour = detect_tour_key_from_history_text(content)
                if hist_tour:
                    current_tour = hist_tour
                    break

        if not current_date:
            for item in reversed(history[-10:]):
                if item.get("role") != "user":
                    continue

                content = item.get("content", "").strip()
                if not content:
                    continue

                hist_date = detect_date(content)
                if hist_date:
                    current_date = hist_date
                    break

    return current_tour, current_date


def get_effective_date(user_message: str, history: list[dict] | None = None) -> str | None:
    current_date = detect_date(user_message)
    if current_date:
        return current_date

    if history:
        for item in reversed(history[-10:]):
            if item.get("role") != "user":
                continue

            content = item.get("content", "").strip()
            if not content:
                continue

            previous_date = detect_date(content)
            if previous_date:
                return previous_date

    return detect_date("today")