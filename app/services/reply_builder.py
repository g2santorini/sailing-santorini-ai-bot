from datetime import datetime


def format_price_line(availability: dict) -> str:
    adult_price = availability.get("adult_price")

    if adult_price is None:
        return ""

    return f"Adult price: €{adult_price:.0f}"


def format_alternative_tours(alternative_tours: list[dict]) -> str:
    if not alternative_tours:
        return ""

    lines = []
    for tour in alternative_tours:
        label = tour.get("reply_label") or tour.get("label")
        if label:
            lines.append(f"- {label}")

    if not lines:
        return ""

    return "\n".join(lines)


def build_time_comparison_reply(language="en") -> str:
    if language == "en":
        return (
            "Great question — both options are beautiful, but it depends on the experience you're looking for.\n\n"
            "Morning cruises are more relaxed, with fewer crowds and more time for swimming.\n"
            "Sunset cruises offer a more romantic atmosphere, ending with the famous Santorini sunset.\n\n"
            "If you prefer calm and sunshine, go for morning.\n"
            "If you want a more scenic and memorable vibe, sunset is usually the favorite."
        )

    elif language == "el":
        return (
            "Πολύ καλή ερώτηση — και οι δύο επιλογές είναι υπέροχες, εξαρτάται τι εμπειρία θέλετε.\n\n"
            "Οι πρωινές εκδρομές είναι πιο χαλαρές, με λιγότερο κόσμο και περισσότερο χρόνο για μπάνιο.\n"
            "Οι απογευματινές καταλήγουν στο ηλιοβασίλεμα και έχουν πιο ρομαντική ατμόσφαιρα.\n\n"
            "Αν θέλετε χαλάρωση και ήλιο, προτιμήστε πρωινό.\n"
            "Αν θέλετε εμπειρία με θέα και ηλιοβασίλεμα, το sunset είναι το πιο δημοφιλές."
        )

    return (
        "Both morning and sunset cruises are beautiful. "
        "Morning is more relaxed, while sunset is more scenic and romantic."
    )


def build_availability_reply(data: dict) -> str:
    if not data.get("success"):
        return "Thank you for your message. I am sorry, but I could not identify this cruise."

    label = data["reply_label"]
    url = data["booking_url"]

    availability = data["availability"]
    available = availability["available"]
    spots = availability["vacancies"]

    alternative_tours = data.get("alternative_tours", [])

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
                f"The {label} is available for {formatted_date}.\n\n"
                f"{spots_text}\n\n"
                f"{pricing_text}\n\n"
                f"You can proceed with your booking using the following link:\n{url}\n\n"
                "Please select the date on the booking page."
            )

        return (
            f"The {label} is available for {formatted_date}.\n\n"
            f"{spots_text}\n\n"
            f"You can proceed with your booking using the following link:\n{url}\n\n"
            "Please select the date on the booking page."
        )

    alternatives_text = format_alternative_tours(alternative_tours)

    if alternatives_text:
        return (
            f"Unfortunately, the {label} is not available for {formatted_date}.\n\n"
            f"However, there are other available options for the same date:\n"
            f"{alternatives_text}\n\n"
            f"You may explore the available options here:\n{url}\n\n"
            "Please select the date on the booking page."
        )

    return (
        f"Unfortunately, the {label} is not available for {formatted_date}.\n\n"
        f"You may check other available dates here:\n{url}\n\n"
        "Please select the date on the booking page."
    )