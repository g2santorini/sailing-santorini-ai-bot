from app.services.tour_mapping import get_tour_option, extract_max_guests

def filter_by_capacity(results: list[dict], passenger_count: int | None):
    if not passenger_count or not isinstance(results, list):
        return results

    filtered = []

    for item in results:
        tour_key = item.get("tour_key")
        if not tour_key:
            filtered.append(item)
            continue

        option = get_tour_option(tour_key)
        max_guests = extract_max_guests(option)

        # αν δεν ξέρουμε capacity → το κρατάμε (safe fallback)
        if max_guests is None:
            filtered.append(item)
            continue

        if passenger_count <= max_guests:
            filtered.append(item)

    return filtered

def get_requested_tour_type(tour_key: str | None) -> str | None:
    if not tour_key:
        return None

    option = get_tour_option(tour_key)
    if not option:
        return None

    return option.get("tour_type")


def get_requested_reply_label(tour_key: str | None) -> str | None:
    if not tour_key:
        return None

    option = get_tour_option(tour_key)
    if not option:
        return None

    return option.get("reply_label")


def filter_same_type_alternatives(
    results: list[dict],
    requested_tour_key: str | None,
) -> list[dict]:
    if not results:
        return []

    requested_type = get_requested_tour_type(requested_tour_key)
    if not requested_type:
        return results

    filtered = []
    for item in results:
        item_type = str(item.get("tour_type", "")).lower().strip()
        if item_type == requested_type:
            filtered.append(item)

    return filtered


def remove_requested_tour(
    results: list[dict],
    requested_tour_key: str | None,
) -> list[dict]:
    if not results or not requested_tour_key:
        return results or []

    requested_option = get_tour_option(requested_tour_key)
    if not requested_option:
        return results

    requested_label = str(requested_option.get("reply_label", "")).lower().strip()
    requested_product_id = requested_option.get("product_id")
    requested_option_id = requested_option.get("product_option_id")

    filtered = []
    for item in results:
        item_label = str(item.get("reply_label", "")).lower().strip()
        item_product_id = item.get("product_id")
        item_option_id = item.get("product_option_id")

        same_by_ids = (
            requested_product_id == item_product_id
            and requested_option_id == item_option_id
        )
        same_by_label = requested_label and item_label == requested_label

        if same_by_ids or same_by_label:
            continue

        filtered.append(item)

    return filtered


def filter_capacity_suitable_alternatives(
    results: list[dict],
    passenger_count: int | None,
) -> list[dict]:
    if not results or not isinstance(passenger_count, int):
        return results or []

    filtered = []

    for item in results:
        max_guests = item.get("max_guests")

        if isinstance(max_guests, int):
            if max_guests >= passenger_count:
                filtered.append(item)
            continue

        # Αν δεν ξέρουμε max_guests, το κρατάμε προς το παρόν
        filtered.append(item)

    return filtered


def limit_alternatives(results: list[dict], limit: int = 3) -> list[dict]:
    if not results:
        return []

    return results[:limit]


def prepare_alternative_results(
    results: list[dict],
    requested_tour_key: str | None,
    passenger_count: int | None = None,
) -> list[dict]:
    if not results:
        return []

    filtered = filter_same_type_alternatives(results, requested_tour_key)
    filtered = remove_requested_tour(filtered, requested_tour_key)
    filtered = filter_capacity_suitable_alternatives(filtered, passenger_count)
    filtered = limit_alternatives(filtered, limit=3)

    return filtered


def build_unavailable_alternatives_reply(
    requested_tour_key: str | None,
    alternatives: list[dict],
    language: str,
    booking_link: str,
) -> str | None:
    if not alternatives:
        return None

    requested_label = get_requested_reply_label(requested_tour_key) or "this cruise"
    requested_type = get_requested_tour_type(requested_tour_key) or ""

    alt_labels = [item.get("reply_label", "Cruise") for item in alternatives]

    if language == "el":
        type_text = "ιδιωτικές" if requested_type == "private" else "shared"
        lines = [f"Το {requested_label} δεν είναι διαθέσιμο για την ημερομηνία που ζητήσατε.", ""]
        lines.append(f"Ωστόσο, οι παρακάτω {type_text} επιλογές είναι διαθέσιμες:")
        for label in alt_labels:
            lines.append(f"- {label}")
        lines.append("")
        lines.append("Μπορείτε να προχωρήσετε στην κράτησή σας εδώ:")
        lines.append(booking_link)
        return "\n".join(lines)

    if language == "it":
        type_text = "private" if requested_type == "private" else "condivise"
        lines = [f"{requested_label} non è disponibile per la data richiesta.", ""]
        lines.append(f"Tuttavia, sono disponibili le seguenti opzioni {type_text}:")
        for label in alt_labels:
            lines.append(f"- {label}")
        lines.append("")
        lines.append("Puoi procedere con la prenotazione qui:")
        lines.append(booking_link)
        return "\n".join(lines)

    if language == "pt":
        type_text = "privadas" if requested_type == "private" else "partilhadas"
        lines = [f"{requested_label} não está disponível para a data solicitada.", ""]
        lines.append(f"No entanto, as seguintes opções {type_text} estão disponíveis:")
        for label in alt_labels:
            lines.append(f"- {label}")
        lines.append("")
        lines.append("Pode avançar com a sua reserva aqui:")
        lines.append(booking_link)
        return "\n".join(lines)

    type_text = "private" if requested_type == "private" else "shared"
    lines = [f"The {requested_label} is not available for the selected date.", ""]
    lines.append(f"However, you may consider the following {type_text} options:")
    for label in alt_labels:
        lines.append(f"- {label}")
    lines.append("")
    lines.append("You may proceed with your booking here:")
    lines.append(booking_link)
    return "\n".join(lines)


def build_capacity_alternatives_reply(
    requested_tour_key: str | None,
    passenger_count: int | None,
    alternatives: list[dict],
    language: str,
) -> str | None:
    if not alternatives or not isinstance(passenger_count, int):
        return None

    requested_option = get_tour_option(requested_tour_key) if requested_tour_key else None
    requested_label = (
        requested_option.get("reply_label", "this cruise")
        if requested_option
        else "this cruise"
    )
    max_guests = extract_max_guests(requested_option) if requested_option else None

    alt_labels = [item.get("reply_label", "Cruise") for item in alternatives]

    if language == "el":
        if isinstance(max_guests, int):
            lines = [
                f"Το {requested_label} είναι κατάλληλο για έως {max_guests} άτομα, οπότε δεν είναι κατάλληλο για {passenger_count} άτομα.",
                "",
                "Για την παρέα σας, θα πρότεινα τις εξής επιλογές:",
            ]
        else:
            lines = [
                f"Το {requested_label} δεν φαίνεται να είναι η κατάλληλη επιλογή για {passenger_count} άτομα.",
                "",
                "Για την παρέα σας, θα πρότεινα τις εξής επιλογές:",
            ]

        for label in alt_labels:
            lines.append(f"- {label}")

        return "\n".join(lines)

    if language == "it":
        if isinstance(max_guests, int):
            lines = [
                f"{requested_label} è adatto fino a {max_guests} ospiti, quindi non è adatto per {passenger_count} persone.",
                "",
                "Per il vostro gruppo, consiglierei le seguenti opzioni:",
            ]
        else:
            lines = [
                f"{requested_label} non sembra essere l’opzione più adatta per {passenger_count} persone.",
                "",
                "Per il vostro gruppo, consiglierei le seguenti opzioni:",
            ]

        for label in alt_labels:
            lines.append(f"- {label}")

        return "\n".join(lines)

    if language == "pt":
        if isinstance(max_guests, int):
            lines = [
                f"{requested_label} é adequado até {max_guests} pessoas, por isso não é adequado para {passenger_count} pessoas.",
                "",
                "Para o seu grupo, eu recomendaria as seguintes opções:",
            ]
        else:
            lines = [
                f"{requested_label} não parece ser a opção mais adequada para {passenger_count} pessoas.",
                "",
                "Para o seu grupo, eu recomendaria as seguintes opções:",
            ]

        for label in alt_labels:
            lines.append(f"- {label}")

        return "\n".join(lines)

    if isinstance(max_guests, int):
        lines = [
            f"{requested_label} is suitable for up to {max_guests} guests, so it would not be suitable for {passenger_count} people.",
            "",
            "For your group, I would recommend the following options:",
        ]
    else:
        lines = [
            f"{requested_label} does not seem to be the most suitable option for {passenger_count} people.",
            "",
            "For your group, I would recommend the following options:",
        ]

    for label in alt_labels:
        lines.append(f"- {label}")

    return "\n".join(lines)