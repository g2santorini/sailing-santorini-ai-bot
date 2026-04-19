from datetime import datetime

DEFAULT_BOOKING_LINK = "https://sailingsantorini.link-twist.com/"


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


def is_private_label(label: str) -> bool:
    return "private" in (label or "").lower()


def format_guest_text(count: int) -> str:
    return "1 guest" if count == 1 else f"{count} guests"


def build_capacity_mismatch_reply(
    label: str,
    formatted_date: str,
    requested_group_size: int,
    capacity: int,
    alternative_tours: list[dict],
    fallback_url: str,
) -> str:
    guest_text = format_guest_text(requested_group_size)
    capacity_text = format_guest_text(capacity)
    alternatives_text = format_alternative_tours(alternative_tours)

    if alternatives_text:
        return (
            f"The {label} is available for {formatted_date}, however it can accommodate up to {capacity_text}, "
            f"so it would not be suitable for your group of {guest_text}.\n\n"
            "For your group size, you may consider these other available options:\n"
            f"{alternatives_text}\n\n"
            f"You may explore the available options here:\n{fallback_url}\n\n"
            "Please select the date on the booking page."
        )

    return (
        f"The {label} is available for {formatted_date}, however it can accommodate up to {capacity_text}, "
        f"so it would not be suitable for your group of {guest_text}.\n\n"
        f"You may explore other suitable options here:\n{fallback_url}\n\n"
        "Please select the date on the booking page."
    )


def build_availability_reply(data: dict) -> str:
    if not data.get("success"):
        return "Thank you for your message. I am sorry, but I could not identify this cruise."

    label = data["reply_label"]
    requested_url = data["booking_url"]
    fallback_url = data.get("general_booking_url") or DEFAULT_BOOKING_LINK

    availability = data["availability"]
    available = availability.get("available", False)
    spots = availability.get("vacancies", 0)

    alternative_tours = data.get("alternative_tours", [])
    requested_group_size = data.get("requested_group_size")

    date_label = availability.get("date_time", "")

    try:
        formatted_date = datetime.strptime(date_label[:10], "%Y-%m-%d").strftime("%d %B %Y").lstrip("0")
    except (ValueError, TypeError):
        formatted_date = date_label

    pricing_text = format_price_line(availability)
    is_private = is_private_label(label)

    if available:
        if is_private:
            capacity = spots if isinstance(spots, int) and spots > 0 else None

            if (
                isinstance(requested_group_size, int)
                and requested_group_size > 0
                and isinstance(capacity, int)
                and requested_group_size > capacity
            ):
                return build_capacity_mismatch_reply(
                    label=label,
                    formatted_date=formatted_date,
                    requested_group_size=requested_group_size,
                    capacity=capacity,
                    alternative_tours=alternative_tours,
                    fallback_url=fallback_url,
                )

            if capacity == 1:
                capacity_text = "It can accommodate up to 1 guest."
            else:
                capacity_text = f"It can accommodate up to {capacity} guests."

            if pricing_text:
                return (
                    f"The {label} is available for {formatted_date}.\n\n"
                    f"{capacity_text}\n\n"
                    f"{pricing_text}\n\n"
                    f"You can proceed with your booking here:\n{requested_url}\n\n"
                    "Please select the date on the booking page."
                )

            return (
                f"The {label} is available for {formatted_date}.\n\n"
                f"{capacity_text}\n\n"
                f"You can proceed with your booking here:\n{requested_url}\n\n"
                "Please select the date on the booking page."
            )

        if spots == 1:
            spots_text = "There is currently 1 spot available."
        elif isinstance(spots, int) and spots > 20:
            spots_text = "There are currently 20+ spots available."
        else:
            spots_text = f"There are currently {spots} spots available."

        if pricing_text:
            return (
                f"The {label} is available for {formatted_date}.\n\n"
                f"{spots_text}\n\n"
                f"{pricing_text}\n\n"
                f"You can proceed with your booking here:\n{requested_url}\n\n"
                "Please select the date on the booking page."
            )

        return (
            f"The {label} is available for {formatted_date}.\n\n"
            f"{spots_text}\n\n"
            f"You can proceed with your booking here:\n{requested_url}\n\n"
            "Please select the date on the booking page."
        )

    alternatives_text = format_alternative_tours(alternative_tours)

    if alternatives_text:
        return (
            f"Unfortunately, the {label} is not available for {formatted_date}.\n\n"
            "However, there are other available options for the same date:\n"
            f"{alternatives_text}\n\n"
            f"You may explore the available options here:\n{fallback_url}\n\n"
            "Please select the date on the booking page."
        )

    return (
        f"Unfortunately, the {label} is not available for {formatted_date}.\n\n"
        f"You may check other available dates here:\n{fallback_url}\n\n"
        "Please select the date on the booking page."
    )