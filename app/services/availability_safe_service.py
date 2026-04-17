from app.services.availability_lookup import check_tour_availability
from app.services.availability_search import find_available_tours


def safe_check_tour_availability(tour_key: str, date_str: str):
    try:
        return check_tour_availability(tour_key, date_str)
    except Exception as exc:
        print(f"Availability lookup error for {tour_key} on {date_str}: {exc}")
        return None


def safe_find_available_tours(
    effective_date: str,
    period: str | None,
    user_message: str,
    passenger_count: int | None,
    ignore_requested_tours: bool = False,
):
    try:
        return find_available_tours(
            effective_date,
            period,
            user_message,
            passenger_count,
            ignore_requested_tours=ignore_requested_tours,
        )
    except Exception as exc:
        print(f"Availability search error for {effective_date}: {exc}")
        return None