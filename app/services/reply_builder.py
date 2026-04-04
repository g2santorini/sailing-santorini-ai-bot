def build_availability_reply(data: dict) -> str:
    if not data.get("success"):
        return "Sorry, I could not find this cruise."

    label = data["reply_label"]
    url = data["booking_url"]

    availability = data["availability"]
    available = availability["available"]
    spots = availability["vacancies"]

    if available:
        return (
            f"Yes, the {label} is available.\n"
            f"There are currently {spots} spots available.\n\n"
            f"Please use the following link to proceed with your booking:\n{url}\n\n"
            f"Please select the date at the booking page."
        )

    return (
        f"Unfortunately, the {label} is not available on the selected date.\n\n"
        f"You may check other available dates here:\n{url}"
    )