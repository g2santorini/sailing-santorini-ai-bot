from app.services.tour_mapping import TOUR_OPTIONS, extract_max_guests
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


def detect_requested_cruise_type(user_message: str) -> str | None:
    text = user_message.lower()

    private_keywords = [
        "private",
        "privately",
        "just for us",
        "only for us",
        "for our group only",
        "ιδιωτική",
        "ιδιωτικη",
        "μόνο για εμάς",
        "μονο για εμας",
        "privata",
        "solo per noi",
    ]

    shared_keywords = [
        "shared",
        "semi private",
        "semi-private",
        "join",
        "group cruise",
        "κοινή",
        "κοινη",
        "condivisa",
        "di gruppo",
    ]

    has_private = any(keyword in text for keyword in private_keywords)
    has_shared = any(keyword in text for keyword in shared_keywords)

    if has_private and not has_shared:
        return "private"

    if has_shared and not has_private:
        return "shared"

    return None


def tour_matches_requested(
    tour_key: str,
    reply_label: str,
    requested_tours: set[str],
) -> bool:
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


def tour_matches_cruise_type(tour: dict, requested_cruise_type: str | None) -> bool:
    if not requested_cruise_type:
        return True

    tour_type = str(tour.get("tour_type", "")).lower().strip()

    if not tour_type:
        return True

    if requested_cruise_type == "private":
        return tour_type == "private"

    if requested_cruise_type == "shared":
        return tour_type == "shared"

    return True


def has_enough_vacancies(availability: dict, passenger_count: int | None) -> bool:
    if passenger_count is None:
        return True

    vacancies = availability.get("vacancies")

    if vacancies is None:
        return False

    try:
        return int(vacancies) >= int(passenger_count)
    except (TypeError, ValueError):
        return False


def has_enough_capacity(tour: dict, passenger_count: int | None) -> bool:
    if passenger_count is None:
        return True

    max_guests = extract_max_guests(tour)

    if max_guests is None:
        return True

    try:
        return int(passenger_count) <= int(max_guests)
    except (TypeError, ValueError):
        return True


def find_available_tours(
    date_str: str,
    period: str | None = None,
    user_message: str = "",
    passenger_count: int | None = None,
    ignore_requested_tours: bool = False,
) -> list[dict]:
    results = []
    seen_labels = set()

    requested_tours = set()
    if not ignore_requested_tours:
        requested_tours = detect_requested_tours(user_message)

    requested_cruise_type = detect_requested_cruise_type(user_message)

    for tour_key, tour in TOUR_OPTIONS.items():
        option_name = tour.get("option_name", "").lower()

        if period == "morning" and "morning" not in option_name:
            continue

        if period == "sunset" and "sunset" not in option_name:
            continue

        if not tour_matches_cruise_type(tour, requested_cruise_type):
            continue

        if not tour_matches_requested(
            tour_key,
            tour.get("reply_label", ""),
            requested_tours,
        ):
            continue

        if not has_enough_capacity(tour, passenger_count):
            continue

        data = check_tour_availability(tour_key, date_str)

        if not data or not data.get("success"):
            continue

        availability = data.get("availability")
        if not availability or not availability.get("available"):
            continue

        if not has_enough_vacancies(availability, passenger_count):
            continue

        reply_label = data["reply_label"]

        if reply_label in seen_labels:
            continue

        if not tour_matches_requested(tour_key, reply_label, requested_tours):
            continue

        seen_labels.add(reply_label)

        results.append(
            {
                "tour_key": tour_key,
                "reply_label": reply_label,
                "booking_url": data["booking_url"],
                "vacancies": availability["vacancies"],
                "date_time": availability["date_time"],
                "tour_type": tour.get("tour_type"),
                "max_guests": extract_max_guests(tour),
            }
        )

    return results