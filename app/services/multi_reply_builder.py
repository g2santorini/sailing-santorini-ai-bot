from datetime import datetime


def build_multi_availability_reply(
    results: list[dict],
    date_label: str,
    period: str | None = None
) -> str:
    booking_link = "https://sailingsantorini.link-twist.com/"

    try:
        formatted_date = datetime.strptime(date_label, "%Y-%m-%d").strftime("%d %B %Y").lstrip("0")
    except:
        formatted_date = date_label

    if not results:
        if period:
            return (
                f"Thank you for your message.\n\n"
                f"Unfortunately, we do not currently have any {period} cruises available for {formatted_date}.\n\n"
                f"You may check other dates here:\n{booking_link}\n\n"
                f"Please select the date on the booking page."
            )

        return (
            f"Thank you for your message.\n\n"
            f"Unfortunately, we do not currently have any cruises available for {formatted_date}.\n\n"
            f"You may check other dates here:\n{booking_link}\n\n"
            f"Please select the date on the booking page."
        )

    shared = [item for item in results if item.get("tour_type") == "shared"]
    private = [item for item in results if item.get("tour_type") == "private"]

    if period:
        intro = f"Great news! The following {period} cruises are currently available for {formatted_date}:"
    else:
        intro = f"Great news! The following cruises are currently available for {formatted_date}:"

    lines = [intro, ""]

    if shared:
        lines.append("Shared cruises:")
        for item in shared:
            lines.append(f"- {item['reply_label']}")
        lines.append("")

    if private:
        lines.append("Private cruises:")
        for item in private:
            lines.append(f"- {item['reply_label']}")
        lines.append("")

    lines.append("You may proceed with your booking here:")
    lines.append(booking_link)
    lines.append("")
    lines.append("Please select the date on the booking page.")

    return "\n".join(lines)