def build_multi_availability_reply(
    results: list[dict],
    date_label: str,
    period: str | None = None
) -> str:
    if period:
        intro = f"The following {period} cruises are currently available for {date_label}:"
    else:
        intro = f"The following cruises are currently available for {date_label}:"

    if not results:
        if period:
            return (
                f"Unfortunately, we do not currently have any {period} cruises available for {date_label}.\n\n"
                f"You may check other dates here:\nhttps://sailingsantorini.link-twist.com/"
            )
        return (
            f"Unfortunately, we do not currently have any cruises available for {date_label}.\n\n"
            f"You may check other dates here:\nhttps://sailingsantorini.link-twist.com/"
        )

    shared = [item for item in results if item.get("tour_type") == "shared"]
    private = [item for item in results if item.get("tour_type") == "private"]

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

    lines.append("Please use our booking page to proceed:")
    lines.append("https://sailingsantorini.link-twist.com/")
    lines.append("")
    lines.append("Please select the date at the booking page.")

    return "\n".join(lines)