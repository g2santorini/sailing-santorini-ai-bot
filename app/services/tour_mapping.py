import re

TOUR_OPTIONS = {
    "red_morning": {
        "tour_name": "Red Cruise",
        "option_name": "Morning",
        "product_id": 35,
        "product_option_id": 136,
        "booking_url": "https://sailingsantorini.link-twist.com/product/redtour",
        "public_label": "Red Morning Cruise",
        "reply_label": "Red Morning Cruise",
        "tour_type": "shared",
        "default_departure_time": "09:30",
        "notes": "Large shared catamaran",
        "max_guests": 55,
    },
    "red_morning_no_transfer": {
        "tour_name": "Red Cruise",
        "option_name": "Red Morning Cruise without transfer",
        "product_id": 35,
        "product_option_id": 184,
        "booking_url": "https://sailingsantorini.link-twist.com/product/redtour",
        "public_label": "Red Morning Cruise without transfer",
        "reply_label": "Red Morning Cruise",
        "tour_type": "shared",
        "default_departure_time": "09:30",
        "notes": "Large shared catamaran",
        "max_guests": 55,
    },
    "red_sunset": {
        "tour_name": "Red Cruise",
        "option_name": "Sunset",
        "product_id": 35,
        "product_option_id": 137,
        "booking_url": "https://sailingsantorini.link-twist.com/product/redtour",
        "public_label": "Red Sunset Cruise",
        "reply_label": "Red Sunset Cruise",
        "tour_type": "shared",
        "default_departure_time": "14:30",
        "notes": "Large shared catamaran",
        "max_guests": 55,
    },
    "red_sunset_no_transfer": {
        "tour_name": "Red Cruise",
        "option_name": "Red Sunset Cruise without transfer",
        "product_id": 35,
        "product_option_id": 247,
        "booking_url": "https://sailingsantorini.link-twist.com/product/redtour",
        "public_label": "Red Sunset Cruise without transfer",
        "reply_label": "Red Sunset Cruise",
        "tour_type": "shared",
        "default_departure_time": "14:30",
        "notes": "Large shared catamaran",
        "max_guests": 55,
    },
    "gems_morning": {
        "tour_name": "Santorini Gems Cruise",
        "option_name": "Morning",
        "product_id": 37,
        "product_option_id": 138,
        "booking_url": "https://sailingsantorini.link-twist.com/product/gemstour",
        "public_label": "Gems Morning Cruise",
        "reply_label": "Gems Morning Cruise",
        "tour_type": "shared",
        "default_departure_time": "09:30",
        "notes": "Small group catamaran (up to 20 guests)",
        "max_guests": 20,
    },
    "gems_sunset": {
        "tour_name": "Santorini Gems Cruise",
        "option_name": "Sunset",
        "product_id": 37,
        "product_option_id": 139,
        "booking_url": "https://sailingsantorini.link-twist.com/product/gemstour",
        "public_label": "Gems Sunset Cruise",
        "reply_label": "Gems Sunset Cruise",
        "tour_type": "shared",
        "default_departure_time": "14:30",
        "notes": "Small group catamaran (up to 20 guests)",
        "max_guests": 20,
    },
    "platinum_morning": {
        "tour_name": "Santorini Platinum Cruise",
        "option_name": "Morning",
        "product_id": 39,
        "product_option_id": 140,
        "booking_url": "https://sailingsantorini.link-twist.com/product/platinumtour",
        "public_label": "Platinum Morning Cruise",
        "reply_label": "Platinum Morning Cruise",
        "tour_type": "shared",
        "default_departure_time": "09:30",
        "notes": "Small group catamaran (up to 14 guests)",
        "max_guests": 14,
    },
    "platinum_sunset": {
        "tour_name": "Santorini Platinum Cruise",
        "option_name": "Sunset",
        "product_id": 39,
        "product_option_id": 141,
        "booking_url": "https://sailingsantorini.link-twist.com/product/platinumtour",
        "public_label": "Platinum Sunset Cruise",
        "reply_label": "Platinum Sunset Cruise",
        "tour_type": "shared",
        "default_departure_time": "14:30",
        "notes": "Small group catamaran (up to 14 guests)",
        "max_guests": 14,
    },
    "diamond_morning": {
        "tour_name": "Santorini Diamond Cruise",
        "option_name": "Morning",
        "product_id": 41,
        "product_option_id": 142,
        "booking_url": "https://sailingsantorini.link-twist.com/product/diamondtour",
        "public_label": "Diamond Morning Cruise",
        "reply_label": "Diamond Morning Cruise",
        "tour_type": "shared",
        "default_departure_time": "09:30",
        "notes": "Luxury catamaran (up to 20 guests)",
        "max_guests": 20,

    },
    "diamond_sunset": {
        "tour_name": "Santorini Diamond Cruise",
        "option_name": "Sunset",
        "product_id": 41,
        "product_option_id": 143,
        "booking_url": "https://sailingsantorini.link-twist.com/product/diamondtour",
        "public_label": "Diamond Sunset Cruise",
        "reply_label": "Diamond Sunset Cruise",
        "tour_type": "shared",
        "default_departure_time": "14:30",
        "notes": "Luxury catamaran (up to 20 guests)",
        "max_guests": 20,
    },
    "lagoon_380_400_morning": {
        "tour_name": "Private Lagoon 380/400 Cruise",
        "option_name": "Morning",
        "product_id": 42,
        "product_option_id": 144,
        "booking_url": "https://sailingsantorini.link-twist.com/product/privatelagoon400",
        "public_label": "Lagoon 380/400 Morning Cruise",
        "reply_label": "Private Lagoon 380/400 Morning Cruise",
        "tour_type": "private",
        "default_departure_time": "10:15",
        "notes": "Private catamaran cruise",
        "max_guests": 14,
    },
    "lagoon_380_400_sunset": {
        "tour_name": "Private Lagoon 380/400 Cruise",
        "option_name": "Sunset",
        "product_id": 42,
        "product_option_id": 145,
        "booking_url": "https://sailingsantorini.link-twist.com/product/privatelagoon400",
        "public_label": "Lagoon 380/400 Sunset Cruise",
        "reply_label": "Private Lagoon 380/400 Sunset Cruise",
        "tour_type": "private",
        "default_departure_time": "15:15",
        "notes": "Private catamaran cruise",
        "max_guests": 14,
    },
    "emily_morning": {
        "tour_name": "Private Emily Cruise",
        "option_name": "Morning",
        "product_id": 44,
        "product_option_id": 146,
        "booking_url": "https://sailingsantorini.link-twist.com/product/privateemily46",
        "public_label": "Emily Morning Cruise",
        "reply_label": "Private Emily Morning Cruise",
        "tour_type": "private",
        "default_departure_time": "10:30",
        "notes": "Private power catamaran cruise",
        "max_guests": 14,
    },
    "emily_sunset": {
        "tour_name": "Private Emily Cruise",
        "option_name": "Sunset",
        "product_id": 44,
        "product_option_id": 147,
        "booking_url": "https://sailingsantorini.link-twist.com/product/privateemily46",
        "public_label": "Emily Sunset Cruise",
        "reply_label": "Private Emily Sunset Cruise",
        "tour_type": "private",
        "default_departure_time": "15:30",
        "notes": "Private power catamaran cruise",
        "max_guests": 14,
    },
    "ferretti_731_morning": {
        "tour_name": "Private Ferretti 731 Cruise",
        "option_name": "Morning",
        "product_id": 48,
        "product_option_id": 150,
        "booking_url": "https://sailingsantorini.link-twist.com/product/privateferretti731",
        "public_label": "Ferretti 731 Morning Cruise",
        "reply_label": "Private Ferretti 731 Morning Cruise",
        "tour_type": "private",
        "default_departure_time": "11:00",
        "notes": "Luxury Ferretti 731 motor yacht",
        "max_guests": 4,
    },
    "ferretti_731_sunset": {
        "tour_name": "Private Ferretti 731 Cruise",
        "option_name": "Sunset",
        "product_id": 48,
        "product_option_id": 151,
        "booking_url": "https://sailingsantorini.link-twist.com/product/privateferretti731",
        "public_label": "Ferretti 731 Sunset Cruise",
        "reply_label": "Private Ferretti 731 Sunset Cruise",
        "tour_type": "private",
        "default_departure_time": "15:00",
        "notes": "Luxury Ferretti 731 motor yacht",
        "max_guests": 4,
    },
    "ferretti_55_morning": {
        "tour_name": "Private Ferretti 55 Cruise",
        "option_name": "Morning",
        "product_id": 65,
        "product_option_id": 189,
        "booking_url": "https://sailingsantorini.link-twist.com/product/privatemyway",
        "public_label": "Ferretti 55 Morning Cruise",
        "reply_label": "Private Ferretti 55 Morning Cruise",
        "tour_type": "private",
        "default_departure_time": "11:00",
        "notes": "Luxury Ferretti 55 motor yacht",
        "max_guests": 6,
    },
    "ferretti_55_sunset": {
        "tour_name": "Private Ferretti 55 Cruise",
        "option_name": "Sunset",
        "product_id": 65,
        "product_option_id": 190,
        "booking_url": "https://sailingsantorini.link-twist.com/product/privatemyway",
        "public_label": "Ferretti 55 Sunset Cruise",
        "reply_label": "Private Ferretti 55 Sunset Cruise",
        "tour_type": "private",
        "default_departure_time": "15:00",
        "notes": "Luxury Ferretti 55 motor yacht",
        "max_guests": 6,
    },
}


def get_tour_option(tour_key: str) -> dict | None:
    return TOUR_OPTIONS.get(tour_key)


def extract_max_guests(option: dict) -> int | None:
    if not option:
        return None

    explicit_max = option.get("max_guests")
    if isinstance(explicit_max, int):
        return explicit_max

    notes = option.get("notes", "")
    match = re.search(r"up to (\d+) guests", notes, re.IGNORECASE)
    if match:
        return int(match.group(1))

    return None


def build_tour_facts_block(tour_key: str) -> str:
    option = get_tour_option(tour_key)
    if not option:
        return ""

    max_guests = extract_max_guests(option)

    lines = [
        f"TOUR KEY: {tour_key}",
        f"TOUR NAME: {option.get('tour_name', '')}",
        f"OPTION NAME: {option.get('option_name', '')}",
        f"PUBLIC LABEL: {option.get('public_label', '')}",
        f"REPLY LABEL: {option.get('reply_label', '')}",
        f"TOUR TYPE: {option.get('tour_type', '')}",
        f"DEFAULT DEPARTURE TIME: {option.get('default_departure_time', '')}",
        f"BOOKING URL: {option.get('booking_url', '')}",
        f"NOTES: {option.get('notes', '')}",
    ]

    if max_guests is not None:
        lines.append(f"MAX GUESTS: {max_guests}")

    return "\n".join(lines)