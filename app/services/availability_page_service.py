from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any

import requests

from app.core.config import LINKTWIST_API_KEY, LINKTWIST_BASE_URL


TOUR_CONFIG = [
    {
        "key": "red_morning",
        "name": "Red Morning",
        "category": "shared",
        "pricing_type": "per_person",
        "product_id": 35,
        "option_id": 136,
        "details": "Departure: 09:30 Amoudi or Athinios port\nReturn: 14:30 Amoudi or Athinios port\nMenu: Greek salad, grilled chicken and pork skewers, grilled vegetables (vegetarians), stuffed vine leaves with rice, tzatziki, potato salad and pita bread\nDrinks: soft drinks, white local wine, water\nGuests: 55 max\nNeed to Bring: Towels\n https://sailing-santorini.com/itineraries/ocean-voyager-74-tahiti-80/",
    },
    {
        "key": "red_morning_no_transfer",
        "name": "Red Morning NO TRANSFER",
        "category": "shared",
        "pricing_type": "per_person",
        "product_id": 35,
        "option_id": 184,
        "details": "This option does not include transfer services.\nDeparture: 09:30 Amoudi port\nReturn: 14:30 Amoudi port\nMenu: Greek salad, grilled chicken and pork skewers, grilled vegetables (vegetarians), stuffed vine leaves with rice, tzatziki, potato salad and pita bread\nDrinks: soft drinks, white local wine, water\nGuests: 55 max\nNeed to Bring: Towels\n https://sailing-santorini.com/itineraries/ocean-voyager-74-tahiti-80/",
    },
    {
        "key": "red_sunset",
        "name": "Red Sunset",
        "category": "shared",
        "pricing_type": "per_person",
        "product_id": 35,
        "option_id": 137,
        "details": "Departure: 14:30 Amoudi or Athinios port\nReturn: After the sunset at Amoudi or Athinios port\nMenu: Greek salad, grilled chicken and pork skewers, grilled vegetables (vegetarians), stuffed vine leaves with rice, tzatziki, potato salad and pita bread\nDrinks: soft drinks, white local wine, water\nGuests: 55 max\nNeed to Bring: Towels\n https://sailing-santorini.com/itineraries/ocean-voyager-74-tahiti-80/",
    },
    {
        "key": "red_sunset_no_transfer",
        "name": "Red Sunset NO TRANSFER",
        "category": "shared",
        "pricing_type": "per_person",
        "product_id": 35,
        "option_id": 247,
        "details": "This option does not include transfer services.\nDeparture: 14:30 Amoudi port\nReturn: After the sunset at Amoudi port\nMenu: Greek salad, grilled chicken and pork skewers, grilled vegetables (vegetarians), stuffed vine leaves with rice, tzatziki, potato salad and pita bread\nDrinks: soft drinks, white local wine, water\nGuests: 55 max\nNeed to Bring: Towels\n https://sailing-santorini.com/itineraries/ocean-voyager-74-tahiti-80/",
    },
    {
        "key": "gems_morning",
        "name": "Gems Morning",
        "category": "shared",
        "pricing_type": "per_person",
        "product_id": 37,
        "option_id": 138,
        "details": "Departure: 09.45 Amoudi port\nReturn: 14:30 Vlychada port\nBBQ prepared on the spot with pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water\nGuests: 20 max\n https://sailing-santorini.com/itineraries/santorini-gems/",
    },
    {
        "key": "gems_sunset",
        "name": "Gems Sunset",
        "category": "shared",
        "pricing_type": "per_person",
        "product_id": 37,
        "option_id": 139,
        "details": "Departure: 14.45 Vlychada port\nReturn: After the Sunset at Amoudi port\nBBQ prepared on the spot with pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water\nGuests: 20 max\n https://sailing-santorini.com/itineraries/santorini-gems/",
    },
    {
        "key": "platinum_morning",
        "name": "Platinum Morning",
        "category": "shared",
        "pricing_type": "per_person",
        "product_id": 39,
        "option_id": 140,
        "details": "Departure: 09.45 Amoudi port\nReturn: 14:30 Vlychada port\nBBQ prepared on the spot with pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water\nGuests: 14 max\n https://sailing-santorini.com/itineraries/platinum-cruise-with-lagoon-450/",
    },
    {
        "key": "platinum_sunset",
        "name": "Platinum Sunset",
        "category": "shared",
        "pricing_type": "per_person",
        "product_id": 39,
        "option_id": 141,
        "details": "Departure: 14.45 Vlychada port\nReturn: After the Sunset at Amoudi port\nBBQ prepared on the spot with pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water\nGuests: 14 max\n https://sailing-santorini.com/itineraries/platinum-cruise-with-lagoon-450/",
    },
    {
        "key": "diamond_morning",
        "name": "Diamond Morning",
        "category": "shared",
        "pricing_type": "per_person",
        "product_id": 41,
        "option_id": 142,
        "details": "Departure: 09:30 Amoudi port\nReturn: 14:30 Amoudi port\nMenu: BBQ prepared on the spot with fresh fish or pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water and one cocktail\nGuests: 20 max\n https://sailing-santorini.com/itineraries/diamond-cruise-with-ipanema-58/",
    },
    {
        "key": "diamond_sunset",
        "name": "Diamond Sunset",
        "category": "shared",
        "pricing_type": "per_person",
        "product_id": 41,
        "option_id": 143,
        "details": "Departure: 14:30 Amoudi port\nReturn: After the Sunset at Amoudi port\nMenu: BBQ prepared on the spot with fresh fish or pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water and one cocktail\nGuests: 20 max\n https://sailing-santorini.com/itineraries/diamond-cruise-with-ipanema-58/",
    },
    {
        "key": "lagoon380_private_morning",
        "name": "Private Morning Lagoon 380",
        "category": "private",
        "pricing_type": "per_group_up_to_4",
        "product_id": 42,
        "option_id": 241,
        "details": "Departure: 10:15 Amoudi port\nReturn: 14:30 Vlychada port\nMenu: BBQ prepared on the spot with pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta and fresh fish available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water\nGuests: 8 max\n https://sailing-santorini.com/itineraries/private-lagoon-380-400/",
    },
    {
        "key": "lagoon380_private_sunset",
        "name": "Private Sunset Lagoon 380",
        "category": "private",
        "pricing_type": "per_group_up_to_4",
        "product_id": 42,
        "option_id": 242,
        "details": "Departure: 15:15 Vlychada port\nReturn: After the sunset at Amoudi port\nMenu: BBQ prepared on the spot with pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta and fresh fish available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water\nGuests: 8 max\n https://sailing-santorini.com/itineraries/private-lagoon-380-400/",
    },
    {
        "key": "lagoon400_private_morning",
        "name": "Private Morning Lagoon 400",
        "category": "private",
        "pricing_type": "per_group_up_to_4",
        "product_id": 42,
        "option_id": 144,
        "details": "Departure: 10:15 Amoudi port\nReturn: 14:30 Vlychada port\nMenu: BBQ prepared on the spot with pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta and fresh fish available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water\nGuests: 14 max\n https://sailing-santorini.com/itineraries/private-lagoon-380-400/",
    },
    {
        "key": "lagoon400_private_sunset",
        "name": "Private Sunset Lagoon 400",
        "category": "private",
        "pricing_type": "per_group_up_to_4",
        "product_id": 42,
        "option_id": 145,
        "details": "Departure: 15:15 Vlychada port\nReturn: After the sunset at Amoudi port\nMenu: BBQ prepared on the spot with pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta and fresh fish available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water\nGuests: 14 max\n https://sailing-santorini.com/itineraries/private-lagoon-380-400/",
    },
    {
        "key": "elba45_private_morning",
        "name": "Private Morning Elba 45",
        "category": "private",
        "pricing_type": "per_group_up_to_4",
        "product_id": 87,
        "option_id": 243,
        "details": "Departure: 09:45 Amoudi port\nReturn: 14:45 Vlychada port\nMenu: BBQ prepared on the spot with pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta and fresh fish available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water\nGuests: 8 max\n https://sailing-santorini.com/itineraries/private-elba-fp-450/",
    },
    {
        "key": "elba45_private_sunset",
        "name": "Private Sunset Elba 45",
        "category": "private",
        "pricing_type": "per_group_up_to_4",
        "product_id": 87,
        "option_id": 244,
        "details": "Departure: 14:45 Vlychada port\nReturn: After the sunset at Amoudi port\nMenu: BBQ prepared on the spot with pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta and fresh fish available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water\nGuests: 8 max\n https://sailing-santorini.com/itineraries/private-elba-fp-450/",
    },
    {
        "key": "lagoon42_private_morning",
        "name": "Private Morning Lagoon 42",
        "category": "private",
        "pricing_type": "per_group_up_to_4",
        "product_id": 87,
        "option_id": 234,
        "details": "Departure: 09:45 Amoudi port\nReturn: 14:45 Vlychada port\nMenu: BBQ prepared on the spot with pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta and fresh fish available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water\nGuests: 10 max\n https://sailing-santorini.com/itineraries/private-elba-fp-450/",
    },
    {
        "key": "lagoon42_private_sunset",
        "name": "Private Sunset Lagoon 42",
        "category": "private",
        "pricing_type": "per_group_up_to_4",
        "product_id": 87,
        "option_id": 235,
        "details": "Departure: 14:45 Vlychada port\nReturn: After the sunset at Amoudi port\nMenu: BBQ prepared on the spot with pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta and fresh fish available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water\nGuests: 10 max\n https://sailing-santorini.com/itineraries/private-elba-fp-450/",
    },
    {
        "key": "emily46_private_morning",
        "name": "Private Morning Emily 46",
        "category": "private",
        "pricing_type": "per_group_up_to_4",
        "product_id": 44,
        "option_id": 146,
        "details": "Departure: 10:30 Amoudi port\nReturn: 15:30 Amoudi port\nMenu: BBQ prepared on the spot with pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta and fresh fish available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water\nGuests: 14 max\n https://sailing-santorini.com/itineraries/private-emily-46-power-catamaran/",
    },
    {
        "key": "emily46_private_sunset",
        "name": "Private Sunset Emily 46",
        "category": "private",
        "pricing_type": "per_group_up_to_4",
        "product_id": 44,
        "option_id": 147,
        "details": "Departure: 15:30 Amoudi port\nReturn: After the sunset at Amoudi port\nMenu: BBQ prepared on the spot with pork chops or chicken fillet or grilled vegetables (vegetarians), sea food (Shrimps saganaki), pasta with red sauce, stuffed vine leaves with rice, tzatziki, Greek salad and pita bread. Gluten free pasta and fresh fish available (prior notice required)\nDrinks: soft drinks, white local wine, beer, water\nGuests: 14 max\n https://sailing-santorini.com/itineraries/private-emily-46-power-catamaran/",
    },
    {
        "key": "pardo43_private_morning",
        "name": "Private Morning Pardo 43",
        "category": "private",
        "pricing_type": "per_group_up_to_4",
        "product_id": 56,
        "option_id": 158,
        "details": "Departure: 11:00 Amoudi port\nReturn: 15:00 Amoudi port\nMenu: Fresh fish fillet, variety of salads, tzatziki or fava dip, cheese board, cold cuts, finger food, dessert\nDrinks: welcome Aperol cocktail, soft drinks, beers, water, juices and 1 bottle of premium white wine per 4 guests\nGuests: 6 max\n https://sailing-santorini.com/itineraries/pardo-43/",
    },
    {
        "key": "pardo43_private_sunset",
        "name": "Private Sunset Pardo 43",
        "category": "private",
        "pricing_type": "per_group_up_to_4",
        "product_id": 56,
        "option_id": 159,
        "details": "Departure: 16:00 Amoudi port\nReturn: After the sunset at Amoudi port\nMenu: Fresh fish fillet, variety of salads, tzatziki or fava dip, cheese board, cold cuts, finger food, dessert\nDrinks: welcome Aperol cocktail, soft drinks, beers, water, juices and 1 bottle of premium white wine per 4 guests\nGuests: 6 max\n https://sailing-santorini.com/itineraries/pardo-43/",
    },
    {
        "key": "melaniec_pardo43_private_morning",
        "name": "Private Morning Melanie C Pardo 43",
        "category": "private",
        "pricing_type": "per_group_up_to_4",
        "product_id": 56,
        "option_id": 245,
        "details": "Departure: 11:00 Amoudi port\nReturn: 15:00 Amoudi port\nMenu: Fresh fish fillet, variety of salads, tzatziki or fava dip, cheese board, cold cuts, finger food, dessert\nDrinks: welcome Aperol cocktail, soft drinks, beers, water, juices and 1 bottle of premium white wine per 4 guests\nGuests: 6 max\n https://sailing-santorini.com/itineraries/pardo-43/",
    },
    {
        "key": "melaniec_pardo43_private_sunset",
        "name": "Private Sunset Melanie C Pardo 43",
        "category": "private",
        "pricing_type": "per_group_up_to_4",
        "product_id": 56,
        "option_id": 246,
        "details": "Departure: 16:00 Amoudi port\nReturn: After the sunset at Amoudi port\nMenu: Fresh fish fillet, variety of salads, tzatziki or fava dip, cheese board, cold cuts, finger food, dessert\nDrinks: welcome Aperol cocktail, soft drinks, beers, water, juices and 1 bottle of premium white wine per 4 guests\nGuests: 6 max\n https://sailing-santorini.com/itineraries/pardo-43/",
    },
    {
        "key": "ferretti550_private_morning",
        "name": "Private Morning My Way Ferretti 550",
        "category": "private",
        "pricing_type": "per_group_up_to_4",
        "product_id": 65,
        "option_id": 189,
        "details": "Departure: 11:00 Amoudi port\nReturn: 15:00 Amoudi port\nMenu: Fresh fish fillet, variety of salads, tzatziki or fava dip, cheese board, cold cuts, finger food, dessert\nDrinks: welcome Aperol cocktail, soft drinks, beers, water, juices and 1 bottle of premium white wine per 4 guests\nGuests: 6 max\n https://sailing-santorini.com/itineraries/luxury-yacht-my-way-ferretti-550/",
    },
    {
        "key": "ferretti550_private_sunset",
        "name": "Private Sunset My Way Ferretti 550",
        "category": "private",
        "pricing_type": "per_group_up_to_4",
        "product_id": 65,
        "option_id": 190,
        "details": "Departure: 16:00 Amoudi port\nReturn: After the sunset at Amoudi port\nMenu: Fresh fish fillet, variety of salads, tzatziki or fava dip, cheese board, cold cuts, finger food, dessert\nDrinks: welcome Aperol cocktail, soft drinks, beers, water, juices and 1 bottle of premium white wine per 4 guests\nGuests: 6 max\n https://sailing-santorini.com/itineraries/luxury-yacht-my-way-ferretti-550/",
    },
    {
        "key": "ferretti731_private_morning",
        "name": "Private Morning Alexandros Ferretti 731",
        "category": "private",
        "pricing_type": "per_group_up_to_4",
        "product_id": 48,
        "option_id": 150,
        "details": "Departure: 11:00 Amoudi port\nReturn: 15:00 Amoudi port\nMenu: Fresh fish fillet, variety of salads, tzatziki or fava dip, cheese board, cold cuts, finger food, dessert\nDrinks: welcome Aperol cocktail, soft drinks, beers, water, juices and 1 bottle of premium white wine per 4 guests\nGuests: 6 max\n https://sailing-santorini.com/itineraries/luxury-yachts-private-excursion/",
    },
    {
        "key": "ferretti731_private_sunset",
        "name": "Private Sunset Alexandros Ferretti 731",
        "category": "private",
        "pricing_type": "per_group_up_to_4",
        "product_id": 48,
        "option_id": 151,
        "details": "Departure: 16:00 Amoudi port\nReturn: After the sunset at Amoudi port\nMenu: Fresh fish fillet, variety of salads, tzatziki or fava dip, cheese board, cold cuts, finger food, dessert\nDrinks: welcome Aperol cocktail, soft drinks, beers, water, juices and 1 bottle of premium white wine per 4 guests\nGuests: 6 max\n https://sailing-santorini.com/itineraries/luxury-yachts-private-excursion/",
    },
]


def _build_url(product_id: int, option_id: int, date: str) -> str:
    return (
        f"{LINKTWIST_BASE_URL}/products/{product_id}/options/{option_id}/availability"
        f"?from={date}T00:00:00&to={date}T23:59:59&pricing=true"
    )


def _extract_price(item: dict[str, Any], pricing_type: str) -> float | None:
    pricing = item.get("pricing")

    if not pricing or not isinstance(pricing, list):
        return None

    if pricing_type == "per_person":
        for participant in pricing:
            if not isinstance(participant, dict):
                continue

            alias = str(participant.get("participant_type_alias", "")).lower()

            if any(x in alias for x in ["adult", "person"]):
                prices = participant.get("prices", [])

                if isinstance(prices, list) and prices:
                    first_price = prices[0]

                    if isinstance(first_price, dict):
                        value = first_price.get("price_per_participant")
                        if isinstance(value, (int, float)) and value > 0:
                            return float(value)

    if pricing_type == "per_group_up_to_4":
        for participant in pricing:
            if not isinstance(participant, dict):
                continue

            alias = str(participant.get("participant_type_alias", "")).lower()
            if alias != "boatprice":
                continue

            prices = participant.get("prices", [])
            if not isinstance(prices, list):
                continue

            for price_entry in prices:
                if not isinstance(price_entry, dict):
                    continue

                pax_from = price_entry.get("pax_from")
                pax_to = price_entry.get("pax_to")

                if pax_from == 1 and pax_to == 4:
                    fixed_price = price_entry.get("fixed_price")
                    if isinstance(fixed_price, (int, float)) and fixed_price > 0:
                        return float(fixed_price)

                    original_fixed_price = price_entry.get("original_fixed_price")
                    if isinstance(original_fixed_price, (int, float)) and original_fixed_price > 0:
                        return float(original_fixed_price)

    return None


def _status(spots: int | None, category: str) -> str:
    if spots is None:
        return "unknown"

    if category == "private":
        if spots <= 0:
            return "contact_us"
        return "available"

    if spots <= 0:
        return "contact_us"
    if spots <= 6:
        return "low"
    return "available"


def _display_spots(spots: int | None, category: str) -> int | None:
    if category == "private":
        if spots is None:
            return None
        if spots <= 0:
            return 0
        return None

    return spots


def _fetch(tour: dict[str, Any], date: str) -> dict[str, Any]:
    category = tour.get("category", "shared")
    pricing_type = tour.get("pricing_type", "per_person")

    if not tour["product_id"] or not tour["option_id"]:
        return {
            "key": tour["key"],
            "name": tour["name"],
            "category": category,
            "pricing_type": pricing_type,
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
            "category": category,
            "pricing_type": pricing_type,
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
            "category": category,
            "pricing_type": pricing_type,
            "details": tour.get("details", ""),
            "price": None,
            "available_spots": 0,
            "status": "contact_us",
        }

    item = data[0]

    raw_spots = item.get("vacancies")
    if not isinstance(raw_spots, int):
        raw_spots = None

    return {
        "key": tour["key"],
        "name": tour["name"],
        "category": category,
        "pricing_type": pricing_type,
        "details": tour.get("details", ""),
        "price": _extract_price(item, pricing_type),
        "available_spots": _display_spots(raw_spots, category),
        "status": _status(raw_spots, category),
    }


def get_availability_page_data(date: str, view: str = "shared") -> dict[str, Any]:
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Date must be YYYY-MM-DD")

    normalized_view = (view or "shared").strip().lower()
    if normalized_view not in {"shared", "private", "all"}:
        normalized_view = "shared"

    if normalized_view == "shared":
        selected_tours = [t for t in TOUR_CONFIG if t.get("category") == "shared"]
    elif normalized_view == "private":
        selected_tours = [t for t in TOUR_CONFIG if t.get("category") == "private"]
    else:
        selected_tours = TOUR_CONFIG

    max_workers = min(12, max(1, len(selected_tours)))
    tours_by_key: dict[str, dict[str, Any]] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_tour = {
            executor.submit(_fetch, tour, date): tour for tour in selected_tours
        }

        for future in as_completed(future_to_tour):
            tour = future_to_tour[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "key": tour["key"],
                    "name": tour["name"],
                    "category": tour.get("category", "shared"),
                    "pricing_type": tour.get("pricing_type", "per_person"),
                    "details": tour.get("details", ""),
                    "price": None,
                    "available_spots": None,
                    "status": "error",
                    "error": str(exc),
                }

            tours_by_key[tour["key"]] = result

    tours = [tours_by_key[tour["key"]] for tour in selected_tours if tour["key"] in tours_by_key]

    return {
        "date": date,
        "view": normalized_view,
        "tours": tours,
    }