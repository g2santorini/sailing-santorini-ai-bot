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
        intro = f"For {formatted_date}, the following {period} cruises are available:"
        lines = [intro, ""]
    else:
        labels = [item["reply_label"] for item in results]

        if len(labels) == 1:
            intro = f"For {formatted_date}, {labels[0]} is available."
        elif len(labels) == 2:
            intro = f"For {formatted_date}, {labels[0]} and {labels[1]} are available."
        else:
            intro = f"For {formatted_date}, {', '.join(labels[:-1])} and {labels[-1]} are available."

        lines = [intro, ""]

    if period:
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