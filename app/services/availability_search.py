from app.services.tour_mapping import TOUR_OPTIONS
from app.services.availability_lookup import check_tour_availability


def find_available_tours(date_str: str, period: str | None = None) -> list[dict]:
    results = []
    seen_labels = set()

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