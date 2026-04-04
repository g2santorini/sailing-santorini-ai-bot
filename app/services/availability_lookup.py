from app.services.availability_service import get_day_availability
from app.services.tour_mapping import TOUR_OPTIONS


def check_tour_availability(tour_key: str, date_str: str) -> dict:
    tour = TOUR_OPTIONS.get(tour_key)

    if not tour:
        return {
            "success": False,
            "message": "Tour not found."
        }

    result = get_day_availability(
        tour["product_id"],
        tour["product_option_id"],
        date_str
    )

    return {
        "success": True,
        "tour_key": tour_key,
        "reply_label": tour["reply_label"],
        "booking_url": tour["booking_url"],
        "availability": result
    }