from datetime import date, datetime

from app.services.translation_service import get_text


def parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def get_requested_period(tour_key: str | None, period: str | None) -> str | None:
    if tour_key:
        lowered = tour_key.lower()
        if "morning" in lowered:
            return "morning"
        if "sunset" in lowered:
            return "sunset"
    return period


def get_seasonal_reply(
    date_str: str | None,
    language: str,
    booking_link: str,
    whatsapp_link: str,
    tour_key: str | None = None,
    period: str | None = None,
    generic_availability: bool = False,
) -> str | None:
    requested_date = parse_iso_date(date_str)
    if not requested_date:
        return None

    requested_period = get_requested_period(tour_key, period)

    sunset_only_start = date(2026, 10, 25)
    sunset_only_end = date(2026, 11, 15)
    off_season_start = date(2026, 11, 16)
    season_resume = date(2027, 3, 15)

    if off_season_start <= requested_date < season_resume:
        return get_text(
            "off_season_reply",
            language,
            booking_link,
            whatsapp_link,
        )

    if sunset_only_start <= requested_date <= sunset_only_end:
        if requested_period == "morning":
            return get_text(
                "morning_unavailable_reply",
                language,
                booking_link,
                whatsapp_link,
            )

        if generic_availability and requested_period is None and tour_key is None:
            return get_text(
                "sunset_only_reply",
                language,
                booking_link,
                whatsapp_link,
            )

    return None