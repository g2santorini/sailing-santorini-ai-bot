from datetime import datetime
from typing import Any

import requests

from app.core.config import LINKTWIST_API_KEY, LINKTWIST_BASE_URL


TOUR_CONFIG = [
    {
        "key": "red_morning",
        "name": "Red Morning",
        "product_id": 35,
        "option_id": 136,
        "details": "Departure: 09:30 Amoudi or Athinios port\nReturn: 14:30 Amoudi or Athinios port\nMenu: Greek salad, grilled chicken and pork skewers, grilled vegetables (vegetarians), stuffed vine leaves with rice, tzatziki, potato salad and pita bread\nDrinks: soft drinks, white local wine, water\nGuests: 55 max\nNeed to Bring: Towels\n https://sailing-santorini.com/itineraries/ocean-voyager-74-tahiti-80/",
    },
    {
        "key": "red_morning_no_transfer",
        "name": "Red Morning NO TRANSFER",
        "product_id": 35,
        "option_id": 184,
        "details": "This option does not include transfer services.\nDeparture: 09:30 Amoudi port\nReturn: 14:30 Amoudi port\nMenu: Greek salad, grilled chicken and pork skewers, grilled vegetables (vegetarians), stuffed vine leaves with rice, tzatziki, potato salad and pita bread\nDrinks: soft drinks, white local wine, water\nGuests: 55 max\nNeed to Bring: Towels\n https://sailing-santorini.com/itineraries/ocean-voyager-74-tahiti-80/",
    },
    {
        "key": "red_sunset",
        "name": "Red Sunset",
        "product_id": 35,
        "option_id": 137,
        "details": "Departure: 14:30 Amoudi or Athinios port\nReturn: After the sunset at Amoudi or Athinios port\nMenu: Greek salad, grilled chicken and pork skewers, grilled vegetables (vegetarians), stuffed vine leaves with rice, tzatziki, potato salad and pita bread\nDrinks: soft drinks, white local wine, water\nGuests: 55 max\nNeed to Bring: Towels\n https://sailing-santorini.com/itineraries/ocean-voyager-74-tahiti-80/",
    },
    {
        "key": "red_sunset_no_transfer",
        "name": "Red Sunset NO TRANSFER",
        "product_id": 35,
        "option_id": 247,
        "details": "This option does not include transfer services.\nDeparture: 14:30 Amoudi port\nReturn: After the sunset at Amoudi port\nMenu: Greek salad, grilled chicken and pork skewers, grilled vegetables (vegetarians), stuffed vine leaves with rice, tzatziki, potato salad and pita bread\nDrinks: soft drinks, white local wine, water\nGuests: 55 max\nNeed to Bring: Towels\n https://sailing-santorini.com/itineraries/ocean-voyager-74-tahiti-80/",
    },
    {
        "key": "gems_morning",
        "name": "Gems Morning",
        "product_id": 37,
        "option_id": 138,
        "details": "Departure: 09.45 Amoudi port\nReturn: 14:30 Vlychada port\nBBQ prepared on the spot with pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water\nGuests: 20 max\n https://sailing-santorini.com/itineraries/santorini-gems/",
    },
    {
        "key": "gems_sunset",
        "name": "Gems Sunset",
        "product_id": 37,
        "option_id": 139,
        "details": "Departure: 14.45 Vlychada port\nReturn: After the Sunset at Amoudi port\nBBQ prepared on the spot with pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water\nGuests: 20 max\n https://sailing-santorini.com/itineraries/santorini-gems/",
    },
    {
        "key": "platinum_morning",
        "name": "Platinum Morning",
        "product_id": 39,
        "option_id": 140,
        "details": "Departure: 09.45 Amoudi port\nReturn: 14:30 Vlychada port\nBBQ prepared on the spot with pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water\nGuests: 14 max\n https://sailing-santorini.com/itineraries/platinum-cruise-with-lagoon-450/",
    },
    {
        "key": "platinum_sunset",
        "name": "Platinum Sunset",
        "product_id": 39,
        "option_id": 141,
        "details": "Departure: 14.45 Vlychada port\nReturn: After the Sunset at Amoudi port\nBBQ prepared on the spot with pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water\nGuests: 14 max\n https://sailing-santorini.com/itineraries/platinum-cruise-with-lagoon-450/",
    },
    {
        "key": "diamond_morning",
        "name": "Diamond Morning",
        "product_id": 41,
        "option_id": 142,
        "details": "Departure: 09:30 Amoudi port\nReturn: 14:30 Amoudi port\nMenu: BBQ prepared on the spot with fresh fish or pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water and one cocktail\nGuests: 20 max\n https://sailing-santorini.com/itineraries/diamond-cruise-with-ipanema-58/",
    },
    {
        "key": "diamond_sunset",
        "name": "Diamond Sunset",
        "product_id": 41,
        "option_id": 143,
        "details": "Departure: 14:30 Amoudi port\nReturn: After the Sunset at Amoudi port\nMenu: BBQ prepared on the spot with fresh fish or pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water and one cocktail\nGuests: 20 max\n https://sailing-santorini.com/itineraries/diamond-cruise-with-ipanema-58/",
    },
]


def _build_url(product_id: int, option_id: int, date: str) -> str:
    return (
        f"{LINKTWIST_BASE_URL}/products/{product_id}/options/{option_id}/availability"
        f"?from={date}T00:00:00&to={date}T23:59:59&pricing=true"
    )


def _extract_price(item: dict[str, Any]) -> float | None:
    pricing = item.get("pricing")

    if not pricing:
        return None

    if isinstance(pricing, list):
        for participant in pricing:
            if not isinstance(participant, dict):
                continue

            alias = str(participant.get("participant_type_alias", "")).lower()

            # STRICT adult detection
            if any(x in alias for x in ["adult", "person"]):
                prices = participant.get("prices", [])

                if isinstance(prices, list) and prices:
                    first_price = prices[0]

                    if isinstance(first_price, dict):
                        value = first_price.get("price_per_participant")
                        if isinstance(value, (int, float)) and value > 0:
                            return float(value)

    return None


def _status(spots: int | None) -> str:
    if spots is None:
        return "unknown"
    if spots <= 0:
        return "contact_us"
    if spots <= 6:
        return "low"
    return "available"


def _fetch(tour: dict[str, Any], date: str) -> dict[str, Any]:
    if not tour["product_id"] or not tour["option_id"]:
        return {
            "key": tour["key"],
            "name": tour["name"],
            "details": tour.get("details", ""),
            "price": None,
            "available_spots": None,
            "status": "missing_ids",
        }

    headers = {
        "accept": "application/json",
        "API-Key": LINKTWIST_API_KEY,
    }

    url = _build_url(tour["product_id"], tour["option_id"], date)

    try:
        res = requests.get(
            url,
            headers=headers,
            timeout=15,
        )
        res.raise_for_status()
        data = res.json()
    except Exception as exc:
        return {
            "key": tour["key"],
            "name": tour["name"],
            "details": tour.get("details", ""),
            "price": None,
            "available_spots": None,
            "status": "error",
            "error": str(exc),
            "url": url,
        }

    if not data:
        return {
            "key": tour["key"],
            "name": tour["name"],
            "details": tour.get("details", ""),
            "price": None,
            "available_spots": 0,
            "status": "contact_us",
        }

    item = data[0]

    spots = item.get("vacancies")
    if not isinstance(spots, int):
        spots = None

    return {
        "key": tour["key"],
        "name": tour["name"],
        "details": tour.get("details", ""),
        "price": _extract_price(item),
        "available_spots": spots,
        "status": _status(spots),
    }


def get_availability_page_data(date: str) -> dict[str, Any]:
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Date must be YYYY-MM-DD")

    tours = [_fetch(t, date) for t in TOUR_CONFIG]

    return {
        "date": date,
        "tours": tours,
    }