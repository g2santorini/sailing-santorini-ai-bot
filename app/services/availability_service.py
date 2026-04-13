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

    return {
        "available": vacancies > 0,
        "vacancies": vacancies,
        "date_time": item.get("date_time"),
        "pricing": item.get("pricing"),
        "price": item.get("price"),
        "discounted_price": item.get("discounted_price"),
        "currency": item.get("currency"),
    }