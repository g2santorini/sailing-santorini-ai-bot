from datetime import datetime


def format_price_line(availability: dict) -> str:
    adult_price = availability.get("adult_price")

    if adult_price is None:
        return ""

    return f"Adult price: €{adult_price:.0f}"


def build_availability_reply(data: dict) -> str:
    if not data.get("success"):
        return "Thank you for your message. I am sorry, but I could not identify this cruise."

    label = data["reply_label"]
    url = data["booking_url"]

    availability = data["availability"]
    available = availability["available"]
    spots = availability["vacancies"]

    date_label = availability.get("date_time", "")

    try:
        formatted_date = datetime.strptime(date_label[:10], "%Y-%m-%d").strftime("%d %B %Y").lstrip("0")
    except:
        formatted_date = date_label

    pricing_text = format_price_line(availability)

    if available:
        if spots == 1:
            spots_text = "There is currently 1 spot available."
        elif spots > 20:
            spots_text = "There are currently 20+ spots available."
        else:
            spots_text = f"There are currently {spots} spots available."

        if pricing_text:
            return (
                f"Great news! The {label} is available for {formatted_date}.\n\n"
                f"{spots_text}\n\n"
                f"{pricing_text}\n\n"
                f"You can proceed with your booking using the following link:\n{url}\n\n"
                f"Please select the date on the booking page."
            )

        return (
            f"Great news! The {label} is available for {formatted_date}.\n\n"
            f"{spots_text}\n\n"
            f"You can proceed with your booking using the following link:\n{url}\n\n"
            f"Please select the date on the booking page."
        )

    return (
        f"Unfortunately, the {label} is not available for {formatted_date}.\n\n"
        f"You may check other available dates here:\n{url}\n\n"
        f"If you wish, you may also try another cruise option."
    )