from app.services.tour_mapping import TOUR_OPTIONS
from app.services.availability_lookup import check_tour_availability


def detect_requested_tours(user_message: str) -> set[str]:
    text = user_message.lower()
    requested = set()

    if "red" in text:
        requested.add("red")

    if "diamond" in text:
        requested.add("diamond")

    if "gems" in text or "santorini gems" in text:
        requested.add("gems")

    if "platinum" in text:
        requested.add("platinum")

    if "lagoon" in text:
        requested.add("lagoon")

    if "emily" in text:
        requested.add("emily")

    if "ferretti" in text:
        requested.add("ferretti")

    return requested


def tour_matches_requested(tour_key: str, reply_label: str, requested_tours: set[str]) -> bool:
    if not requested_tours:
        return True

    combined = f"{tour_key} {reply_label}".lower()

    if "red" in requested_tours and "red" in combined:
        return True

    if "diamond" in requested_tours and "diamond" in combined:
        return True

    if "gems" in requested_tours and "gems" in combined:
        return True

    if "platinum" in requested_tours and "platinum" in combined:
        return True

    if "lagoon" in requested_tours and "lagoon" in combined:
        return True

    if "emily" in requested_tours and "emily" in combined:
        return True

    if "ferretti" in requested_tours and "ferretti" in combined:
        return True

    return False


def find_available_tours(date_str: str, period: str | None = None, user_message: str = "") -> list[dict]:
    results = []
    seen_labels = set()
    requested_tours = detect_requested_tours(user_message)

    for tour_key, tour in TOUR_OPTIONS.items():
        option_name = tour.get("option_name", "").lower()

        if period == "morning" and "morning" not in option_name:
            continue

        if period == "sunset" and "sunset" not in option_name:
            continue

        data = check_tour_availability(tour_key, date_str)

        if not data or not data.get("success"):
            continue

        availability = data.get("availability")
        if not availability or not availability.get("available"):
            continue

        reply_label = data["reply_label"]

        if reply_label in seen_labels:
            continue

        if not tour_matches_requested(tour_key, reply_label, requested_tours):
            continue

        seen_labels.add(reply_label)

        results.append({
            "tour_key": tour_key,
            "reply_label": reply_label,
            "booking_url": data["booking_url"],
            "vacancies": availability["vacancies"],
            "date_time": availability["date_time"],
            "tour_type": tour.get("tour_type"),
        })

    return results