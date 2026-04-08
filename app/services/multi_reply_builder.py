from datetime import datetime


def format_date_by_language(date_label: str, language: str) -> str:
    month_names = {
        "en": {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December"
        },
        "el": {
            1: "Ιανουαρίου", 2: "Φεβρουαρίου", 3: "Μαρτίου", 4: "Απριλίου",
            5: "Μαΐου", 6: "Ιουνίου", 7: "Ιουλίου", 8: "Αυγούστου",
            9: "Σεπτεμβρίου", 10: "Οκτωβρίου", 11: "Νοεμβρίου", 12: "Δεκεμβρίου"
        },
        "it": {
            1: "gennaio", 2: "febbraio", 3: "marzo", 4: "aprile",
            5: "maggio", 6: "giugno", 7: "luglio", 8: "agosto",
            9: "settembre", 10: "ottobre", 11: "novembre", 12: "dicembre"
        },
        "pt": {
            1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
            5: "maio", 6: "junho", 7: "julho", 8: "agosto",
            9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
        }
    }

    try:
        dt = datetime.strptime(date_label, "%Y-%m-%d")
        day = dt.day
        month = month_names.get(language, month_names["en"])[dt.month]
        year = dt.year

        if language == "el":
            return f"{day} {month} {year}"

        return f"{day} {month} {year}"
    except:
        return date_label


def build_multi_availability_reply(
    results: list[dict],
    date_label: str,
    period: str | None = None,
    language: str = "en"
) -> str:
    booking_link = "https://sailingsantorini.link-twist.com/"
    formatted_date = format_date_by_language(date_label, language)

    shared = [item for item in results if item.get("tour_type") == "shared"]
    private = [item for item in results if item.get("tour_type") == "private"]

    all_private = bool(results) and len(private) == len(results)
    all_shared = bool(results) and len(shared) == len(results)

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

    if len(results) == 1:
        item = results[0]
        direct_link = item.get("booking_url") or booking_link
        label = item.get("reply_label", "This cruise")

        intro = f"For {formatted_date}, {label} is available."

        lines = [
            intro,
            "",
            "You can proceed directly with your booking here:",
            direct_link,
            "",
            "Please select the date on the booking page."
        ]

        return "\n".join(lines)

    if period:
        if all_private:
            intro = f"For {formatted_date}, the following private {period} cruises are available:"
        elif all_shared:
            intro = f"For {formatted_date}, the following shared {period} cruises are available:"
        else:
            intro = f"For {formatted_date}, the following {period} cruises are available:"

        lines = [intro, ""]

    else:
        labels = [item["reply_label"] for item in results]

        if len(labels) == 2:
            intro = f"For {formatted_date}, {labels[0]} and {labels[1]} are available."
        else:
            intro = f"For {formatted_date}, {', '.join(labels[:-1])} and {labels[-1]} are available."

        lines = [intro, ""]

    if period:
        if all_private:
            for item in private:
                lines.append(f"- {item['reply_label']}")
            lines.append("")

        elif all_shared:
            for item in shared:
                lines.append(f"- {item['reply_label']}")
            lines.append("")

        else:
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