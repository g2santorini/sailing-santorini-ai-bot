import requests

from app.core.config import LINKTWIST_API_KEY, LINKTWIST_BASE_URL


def test_connection():
    url = f"{LINKTWIST_BASE_URL}/products/35/options/136/availability"

    headers = {
        "accept": "application/json",
        "API-Key": LINKTWIST_API_KEY
    }

    params = {
        "from": "2026-04-06T00:00:00",
        "to": "2026-04-06T23:59:59",
        "pricing": "true"
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    print("========== LINKTWIST RAW (TEST) ==========")
    print(data)
    print("==========================================")

    return data


def extract_prices(pricing_data):
    adult_price = None
    child_price = None
    infant_price = None

    if not isinstance(pricing_data, list):
        return adult_price, child_price, infant_price

    for participant_group in pricing_data:
        alias = str(participant_group.get("participant_type_alias", "")).lower()
        prices = participant_group.get("prices", [])

        if not prices or not isinstance(prices, list):
            continue

        first_price = prices[0]
        price_per_participant = first_price.get("price_per_participant")

        if alias == "perperson6":
            adult_price = price_per_participant
        elif alias == "perchild":
            child_price = price_per_participant
        elif alias == "perinfant":
            infant_price = price_per_participant

    return adult_price, child_price, infant_price


def get_day_availability(product_id, product_option_id, date_str):
    url = f"{LINKTWIST_BASE_URL}/products/{product_id}/options/{product_option_id}/availability"

    headers = {
        "accept": "application/json",
        "API-Key": LINKTWIST_API_KEY
    }

    params = {
        "from": f"{date_str}T00:00:00",
        "to": f"{date_str}T23:59:59",
        "pricing": "true"
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    print("========== LINKTWIST RAW ==========")
    print(data)
    print("===================================")

    if not data:
        return None

    item = data[0]

    vacancies = item.get("vacancies", 0)
    pricing_data = item.get("pricing", [])
    adult_price, child_price, infant_price = extract_prices(pricing_data)

    return {
        "available": vacancies > 0,
        "vacancies": vacancies,
        "date_time": item.get("date_time"),
        "pricing": pricing_data,
        "adult_price": adult_price,
        "child_price": child_price,
        "infant_price": infant_price,
        "displayable_price": item.get("displayable_price"),
        "displayable_price_discounted": item.get("displayable_price_discounted"),
        "group_size": item.get("group_size"),
    }