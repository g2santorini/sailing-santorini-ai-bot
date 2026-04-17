from datetime import datetime
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.services.language_service import detect_language
from app.services.season_service import get_seasonal_reply
from app.routes.availability_routes import router as availability_router
from app.services.translation_service import get_text, translate_availability_reply
from app.services.openai_service import get_ai_reply
from app.services.knowledge_service import get_company_knowledge
from app.services.alternative_service import (
    prepare_alternative_results,
    build_unavailable_alternatives_reply,
    filter_by_capacity,
)
from app.services.reply_builder import (
    build_availability_reply,
    build_time_comparison_reply,
)
from app.services.availability_safe_service import (
    safe_check_tour_availability,
    safe_find_available_tours,
)
from app.services.tour_detector import detect_tour_key
from app.services.date_detector import detect_date
from app.services.multi_reply_builder import build_multi_availability_reply
from app.services.tour_mapping import build_tour_facts_block
from app.services.chat_logger import (
    init_db,
    save_chat_log,
    get_chat_logs,
    get_chat_sessions,
)
from app.services.intent_service import (
    is_greeting,
    is_discount_request,
    is_contact_request,
    is_availability_request,
    is_followup,
    is_best_choice_question,
    is_capacity_request,
    is_multi_capacity_request,
    is_sunset_question,
    is_sunset_concern,
    is_pregnancy_question,
    is_time_comparison,
)
from app.services.context_service import (
    has_recent_availability_context,
    get_last_tour_and_date_from_history,
    get_effective_date,
)
from app.services.request_parser_service import (
    detect_cruise_type_intent,
    detect_passenger_count,
)

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(availability_router)
init_db()

print("MAIN WITH HISTORY + MULTILINGUAL KNOWLEDGE + SMARTER WHATSAPP LOADED")


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = Field(default_factory=list)
    session_id: str | None = None


BOOKING_LINK = "https://sailingsantorini.link-twist.com/"
WEBSITE_LINK = "https://sailing-santorini.com/"
WHATSAPP_LINK = "https://wa.me/306972805193"


def log_and_return(
    user_message: str,
    reply: str,
    language: str,
    fallback: bool = False,
    detected_tour: str | None = None,
    session_id: str | None = None,
):
    try:
        save_chat_log(
            user_message=user_message,
            bot_reply=reply,
            fallback=fallback,
            detected_tour=detected_tour,
            language=language,
            session_id=session_id,
        )
    except Exception as exc:
        print(f"Chat log save error: {exc}")

    return {"reply": reply}


def build_sunset_reassurance_reply(language: str) -> str:
    if language == "el":
        return (
            "Μην ανησυχείτε καθόλου ότι θα χάσετε το ηλιοβασίλεμα.\n\n"
            "Παρότι η αναχώρηση παραμένει σταθερή, η διάρκεια της κρουαζιέρας προσαρμόζεται ανάλογα με την ώρα του ηλιοβασιλέματος.\n"
            "Κατά τους καλοκαιρινούς μήνες η κρουαζιέρα διαρκεί περισσότερο, ώστε να απολαύσετε πλήρως το ηλιοβασίλεμα εν πλω.\n\n"
            "Όλες οι sunset cruises είναι σχεδιασμένες έτσι ώστε να απολαμβάνετε το ηλιοβασίλεμα από το καταμαράν."
        )

    if language == "it":
        return (
            "Non si preoccupi affatto di perdere il tramonto.\n\n"
            "Anche se l’orario di partenza rimane fisso, la durata della crociera si adatta in base all’orario del tramonto.\n"
            "Durante i mesi estivi la crociera dura più a lungo, così da permetterle di godersi pienamente il tramonto a bordo.\n\n"
            "Tutte le crociere al tramonto sono organizzate in modo da farvi vivere il tramonto dal catamarano."
        )

    if language == "pt":
        return (
            "Não se preocupe de forma alguma em perder o pôr do sol.\n\n"
            "Embora a hora de partida permaneça fixa, a duração do cruzeiro é ajustada de acordo com a hora do pôr do sol.\n"
            "Durante os meses de verão, o cruzeiro dura mais para que possa desfrutar plenamente do pôr do sol a bordo.\n\n"
            "Todos os cruzeiros ao pôr do sol são planeados para que os hóspedes apreciem o pôr do sol a partir do catamarã."
        )

    return (
        "Please do not worry about missing the sunset.\n\n"
        "Although the departure time remains fixed, the cruise duration is adjusted depending on the sunset time each day.\n"
        "During the summer months, the cruise lasts longer so that you can fully enjoy the sunset on board.\n\n"
        "All sunset cruises are designed so that guests enjoy the sunset from the catamaran."
    )


def is_clearly_irrelevant(message: str) -> bool:
    msg = message.lower()

    unrelated_keywords = [
        "football",
        "aek",
        "nba",
        "bitcoin",
        "recipe",
        "politics",
    ]

    return any(word in msg for word in unrelated_keywords)


def is_cruise_passenger(user_message: str) -> bool:
    text = user_message.lower()

    keywords = [
        "cruise ship",
        "cruise passenger",
        "ship",
        "old port",
        "tender",
        "cable car",
        "from the ship",
        "coming by cruise",
        "port of fira",
        "fira port",
        "κρουαζιερόπλοιο",
        "παλιό λιμάνι",
        "τελεφερίκ",
        "crociera",
        "nave",
        "porto vecchio",
        "navio de cruzeiro",
        "passageiro de cruzeiro",
        "porto antigo",
    ]

    return any(k in text for k in keywords)


def is_personal_booking_request(user_message: str) -> bool:
    text = user_message.lower().strip()

    keywords = [
        "my pickup",
        "my pick-up",
        "pick up time",
        "pickup time",
        "pick-up time",
        "my booking",
        "my reservation",
        "my transfer",
        "my ticket",
        "can you check my booking",
        "can you see my booking",
        "can you confirm my booking",
        "can you check my reservation",
        "can you see my reservation",
        "booking number",
        "reservation number",
        "confirm my transfer",
        "η κράτησή μου",
        "η κρατηση μου",
        "το booking μου",
        "η παραλαβή μου",
        "η παραλαβη μου",
        "ώρα παραλαβής",
        "ωρα παραλαβης",
        "επιβεβαίωση κράτησης",
        "επιβεβαιωση κρατησης",
        "la mia prenotazione",
        "il mio transfer",
        "orario di pick-up",
        "numero di prenotazione",
        "a minha reserva",
        "o meu transfer",
        "hora do pickup",
        "número da reserva",
        "numero da reserva",
    ]

    return any(k in text for k in keywords)


def is_uncertain_whatsapp_case(user_message: str) -> bool:
    text = user_message.lower()

    keywords = [
        "wheelchair",
        "accessible",
        "accessibility",
        "mobility",
        "bring beverages",
        "bring drinks",
        "bring alcohol",
        "bring wine",
        "bring beer",
        "what beer do you have",
        "which beer do you have",
        "beer brand",
        "beer brands",
        "special request",
        "special arrangement",
        "custom request",
        "proposal",
        "fireworks",
        "καρότσι",
        "καροτσι",
        "αναπηρικό",
        "αναπηρικο",
        "προσβάσιμο",
        "προσβασιμο",
        "να φέρω ποτά",
        "να φερω ποτα",
        "τι μπίρα έχετε",
        "τι μπυρα εχετε",
        "ειδικό αίτημα",
        "ειδικο αιτημα",
        "sedia a rotelle",
        "accessibile",
        "portare bevande",
        "quale birra avete",
        "richiesta speciale",
        "cadeira de rodas",
        "acessível",
        "acessivel",
        "trazer bebidas",
        "que cerveja têm",
        "pedido especial",
    ]

    return any(k in text for k in keywords)


def is_relevant(user_message: str) -> bool:
    text = user_message.lower()

    keywords = [
        "cruise",
        "cruises",
        "tour",
        "tours",
        "santorini",
        "price",
        "availability",
        "available",
        "private",
        "shared",
        "sunset",
        "morning",
        "pickup",
        "pick-up",
        "port",
        "catamaran",
        "booking",
        "book",
        "reservation",
        "cancel",
        "refund",
        "weather",
        "food",
        "drinks",
        "drink",
        "beverage",
        "beverages",
        "beer",
        "menu",
        "meal",
        "vegetarian",
        "vegan",
        "halal",
        "kosher",
        "dietary",
        "allergy",
        "allergies",
        "gluten",
        "gluten free",
        "gluten-free",
        "celiac",
        "coeliac",
        "transfer",
        "hotel",
        "itinerary",
        "red beach",
        "white beach",
        "hot springs",
        "pets",
        "pet",
        "dog",
        "dogs",
        "animal",
        "animals",
        "kids",
        "group",
        "guests",
        "people",
        "persons",
        "person",
        "we are",
        "we have",
        "recommend",
        "suggest",
        "suggestion",
        "what do you recommend",
        "what do you suggest",
        "difference",
        "compare",
        "comparison",
        "which one",
        "which is better",
        "which is the best",
        "best",
        "best option",
        "better",
        "vs",
        "or",
        "red",
        "diamond",
        "gems",
        "platinum",
        "lagoon",
        "emily",
        "ferretti",
        "spot",
        "spots",
        "seat",
        "seats",
        "place",
        "places",
        "left",
        "vessel",
        "vessels",
        "all available",
        "onboard",
        "on board",
        "bring",
        "wear",
        "clothes",
        "clothing",
        "shoes",
        "swimwear",
        "towel",
        "towels",
        "snorkeling",
        "snorkel",
        "wheelchair",
        "accessible",
        "accessibility",
        "mobility",
        "contact",
        "whatsapp",
        "phone",
        "email",
        "reservation department",
        "κρουαζιέρα",
        "κρουαζιερες",
        "τιμή",
        "διαθεσιμότητα",
        "ιδιωτική",
        "ηλιοβασίλεμα",
        "πρωινή",
        "λιμάνι",
        "μεταφορά",
        "φαγητό",
        "ποτό",
        "ποτά",
        "μενού",
        "μπίρα",
        "μπυρα",
        "αναψυκτικά",
        "αναψυκτικα",
        "χορτοφαγ",
        "βίγκαν",
        "χαλάλ",
        "αλλεργ",
        "γλουτένη",
        "χωρίς γλουτένη",
        "κοιλιοκάκη",
        "άτομα",
        "άτομο",
        "είμαστε",
        "έχουμε",
        "προτείνεις",
        "προτείνετε",
        "σύσταση",
        "διαφορά",
        "σύγκριση",
        "ποιο είναι καλύτερο",
        "ποιο ειναι καλυτερο",
        "ποιο είναι το καλύτερο",
        "ποιο ειναι το καλυτερο",
        "καλύτερο",
        "καλυτερο",
        "θέσεις",
        "θέση",
        "πόσες θέσεις",
        "πόσα άτομα μένουν",
        "όλα τα σκάφη",
        "όλα τα διαθέσιμα",
        "κατοικίδιο",
        "κατοικιδιο",
        "κατοικίδια",
        "κατοικιδια",
        "σκύλος",
        "σκυλος",
        "σκυλιά",
        "σκυλια",
        "ζώο",
        "ζωο",
        "ζώα",
        "ζωα",
        "να φέρω",
        "να φερω",
        "τι να φορέσω",
        "τι να φορεσω",
        "πετσέτα",
        "πετσετα",
        "καρότσι",
        "καροτσι",
        "αναπηρικό",
        "αναπηρικο",
        "προσβάσιμο",
        "προσβασιμο",
        "επικοινωνία",
        "επικοινωνησω",
        "επικοινωνήσω",
        "τηλέφωνο",
        "τηλεφωνο",
        "whatsapp",
        "crociera",
        "crociere",
        "prezzo",
        "disponibilità",
        "privata",
        "tramonto",
        "mattina",
        "cibo",
        "bevande",
        "birra",
        "menu",
        "vegetariano",
        "vegano",
        "halal",
        "allergie",
        "glutine",
        "senza glutine",
        "persone",
        "persona",
        "siamo",
        "abbiamo",
        "consigli",
        "raccomandi",
        "suggerisci",
        "differenza",
        "confronto",
        "qual è meglio",
        "qual e meglio",
        "qual è il migliore",
        "qual e il migliore",
        "migliore",
        "posti",
        "posto",
        "quanti posti",
        "tutte le barche",
        "cane",
        "cani",
        "animale",
        "animali",
        "portare",
        "indossare",
        "asciugamano",
        "sedia a rotelle",
        "accessibile",
        "contattare",
        "contatto",
        "telefono",
        "whatsapp",
        "cruzeiro",
        "cruzeiros",
        "preço",
        "preco",
        "disponibilidade",
        "privado",
        "partilhado",
        "compartilhado",
        "comida",
        "bebidas",
        "cerveja",
        "menu",
        "vegetariano",
        "vegano",
        "alergia",
        "alergias",
        "glúten",
        "gluten",
        "sem glúten",
        "sem gluten",
        "pessoas",
        "pessoa",
        "somos",
        "temos",
        "recomenda",
        "sugere",
        "diferença",
        "comparação",
        "comparacao",
        "qual é melhor",
        "qual e melhor",
        "qual é o melhor",
        "qual e o melhor",
        "melhor",
        "lugares",
        "quantos lugares",
        "vagas",
        "todos os barcos",
        "cão",
        "cao",
        "cães",
        "caes",
        "animal",
        "animais",
        "trazer",
        "vestir",
        "toalha",
        "cadeira de rodas",
        "acessível",
        "acessivel",
        "contactar",
        "contacto",
        "telefone",
        "whatsapp",
        "wheelchair",
        "accessible",
        "accessibility",
        "mobility",
        "pregnant",
        "pregnancy",
        "έγκυος",
        "εγκυος",
        "gravidanza",
        "grávida",
        "gravida",
    ]

    return any(k in text for k in keywords)


def detect_period(user_message: str) -> str | None:
    text = user_message.lower()

    if (
        "morning" in text
        or "this morning" in text
        or "πρωιν" in text
        or "mattina" in text
        or "questa mattina" in text
        or "manhã" in text
        or "manha" in text
    ):
        return "morning"

    if (
        "sunset" in text
        or "this afternoon" in text
        or "this evening" in text
        or "tonight" in text
        or "afternoon" in text
        or "evening" in text
        or "ηλιοβασ" in text
        or "απόγευμα" in text
        or "απογευμα" in text
        or "απόψε" in text
        or "αποψε" in text
        or "tramonto" in text
        or "pomeriggio" in text
        or "stasera" in text
        or "tarde" in text
        or "fim do dia" in text
    ):
        return "sunset"

    return None


def extract_result_text(item) -> str:
    if isinstance(item, dict):
        parts = []
        for key in [
            "tour_name",
            "name",
            "title",
            "tour",
            "product_name",
            "option_name",
            "type",
            "category",
            "reply_label",
        ]:
            value = item.get(key)
            if value:
                parts.append(str(value))
        return " ".join(parts).lower()

    return str(item).lower()


def filter_results_by_cruise_type(results, cruise_type: str | None):
    if not cruise_type or not isinstance(results, list) or not results:
        return results

    private_matches = []
    shared_matches = []

    for item in results:
        searchable_text = extract_result_text(item)

        is_private_result = "private" in searchable_text
        is_shared_result = (
            "shared" in searchable_text
            or "semi private" in searchable_text
            or "semi-private" in searchable_text
        )

        if is_private_result:
            private_matches.append(item)
        elif is_shared_result:
            shared_matches.append(item)

    if cruise_type == "private":
        return private_matches if private_matches else results

    if cruise_type == "shared":
        return shared_matches if shared_matches else results

    return results


def get_capacity_number(data) -> int | None:
    if not isinstance(data, dict):
        return None

    availability = data.get("availability")

    if isinstance(availability, dict):
        for key in [
            "available_spots",
            "spots",
            "vacancies",
            "available",
            "capacity_left",
        ]:
            value = availability.get(key)
            if isinstance(value, int):
                return value
            if isinstance(value, str) and value.isdigit():
                return int(value)

    return None


def is_private_result(item: dict) -> bool:
    tour_type = str(item.get("tour_type", "")).lower().strip()
    label = str(item.get("reply_label", "")).lower()

    return tour_type == "private" or "private" in label


def build_capacity_reply(data, language: str) -> str:
    if not isinstance(data, dict):
        return get_text("availability_fallback", language, BOOKING_LINK, WHATSAPP_LINK)

    spots = get_capacity_number(data)
    cruise_name = data.get("reply_label", "this cruise")
    booking_url = data.get("booking_url", BOOKING_LINK)

    is_private = is_private_result(data)

    if isinstance(spots, int) and not is_private and spots > 20:
        spots_display = "20+"
    else:
        spots_display = str(spots) if isinstance(spots, int) else None

    if language == "el":
        if spots_display == "1":
            return (
                f"Για το {cruise_name} υπάρχει μόνο 1 διαθέσιμη θέση.\n\n"
                f"Μπορείτε να προχωρήσετε στην κράτησή σας εδώ:\n{booking_url}\n\n"
                "Παρακαλούμε επιλέξτε την ημερομηνία στη σελίδα κράτησης."
            )
        if spots_display:
            return (
                f"Για το {cruise_name} υπάρχουν {spots_display} διαθέσιμες θέσεις.\n\n"
                f"Μπορείτε να προχωρήσετε στην κράτησή σας εδώ:\n{booking_url}\n\n"
                "Παρακαλούμε επιλέξτε την ημερομηνία στη σελίδα κράτησης."
            )
        return (
            f"Το {cruise_name} είναι διαθέσιμο για την ημερομηνία που ζητήσατε.\n\n"
            f"Μπορείτε να προχωρήσετε στην κράτησή σας εδώ:\n{booking_url}\n\n"
            "Παρακαλούμε επιλέξτε την ημερομηνία στη σελίδα κράτησης."
        )

    if language == "it":
        if spots_display == "1":
            return (
                f"Per {cruise_name} è disponibile solo 1 posto.\n\n"
                f"Puoi procedere con la prenotazione qui:\n{booking_url}\n\n"
                "Ti preghiamo di selezionare la data nella pagina di prenotazione."
            )
        if spots_display:
            return (
                f"Per {cruise_name} ci sono {spots_display} posti disponibili.\n\n"
                f"Puoi procedere con la prenotazione qui:\n{booking_url}\n\n"
                "Ti preghiamo di selezionare la data nella pagina di prenotazione."
            )
        return (
            f"{cruise_name} è disponibile per la data richiesta.\n\n"
            f"Puoi procedere con la prenotazione qui:\n{booking_url}\n\n"
            "Ti preghiamo di selezionare la data nella pagina di prenotazione."
        )

    if language == "pt":
        if spots_display == "1":
            return (
                f"Para {cruise_name} há apenas 1 lugar disponível.\n\n"
                f"Pode avançar com a sua reserva aqui:\n{booking_url}\n\n"
                "Por favor selecione a data na página de reservas."
            )
        if spots_display:
            return (
                f"Para {cruise_name} há {spots_display} lugares disponíveis.\n\n"
                f"Pode avançar com a sua reserva aqui:\n{booking_url}\n\n"
                "Por favor selecione a data na página de reservas."
            )
        return (
            f"{cruise_name} está disponível para a data solicitada.\n\n"
            f"Pode avançar com a sua reserva aqui:\n{booking_url}\n\n"
            "Por favor selecione a data na página de reservas."
        )

    if spots_display == "1":
        return (
            f"For {cruise_name}, there is only 1 spot available.\n\n"
            f"You can proceed with your booking here:\n{booking_url}\n\n"
            "Please select the date on the booking page."
        )

    if spots_display:
        return (
            f"For {cruise_name}, there are {spots_display} spots available.\n\n"
            f"You can proceed with your booking here:\n{booking_url}\n\n"
            "Please select the date on the booking page."
        )

    return (
        f"{cruise_name} is available for the requested date.\n\n"
        f"You can proceed with your booking here:\n{booking_url}\n\n"
        "Please select the date on the booking page."
    )


def format_shared_vacancies(vacancies) -> str:
    try:
        value = int(vacancies)
        if value > 20:
            return "20+"
        return str(value)
    except (TypeError, ValueError):
        return str(vacancies)


def build_multi_capacity_reply(results: list[dict], language: str) -> str:
    if language == "el":
        lines = ["Οι διαθέσιμες επιλογές για το ζητούμενο χρονικό διάστημα είναι:"]
        for item in results:
            label = item.get("reply_label", "Κρουαζιέρα")

            if is_private_result(item):
                lines.append(f"- {label}: διαθέσιμη")
            else:
                vacancies_text = format_shared_vacancies(item.get("vacancies"))
                if vacancies_text == "1":
                    lines.append(f"- {label}: 1 διαθέσιμη θέση")
                else:
                    lines.append(f"- {label}: {vacancies_text} διαθέσιμες θέσεις")
        lines.append("")
        lines.append("Μπορείτε να προχωρήσετε στην κράτησή σας εδώ:")
        lines.append(BOOKING_LINK)
        lines.append("")
        lines.append("Παρακαλούμε επιλέξτε την ημερομηνία στη σελίδα κράτησης.")
        return "\n".join(lines)

    if language == "it":
        lines = ["Ecco le opzioni disponibili per l’orario richiesto:"]
        for item in results:
            label = item.get("reply_label", "Crociera")

            if is_private_result(item):
                lines.append(f"- {label}: disponibile")
            else:
                vacancies_text = format_shared_vacancies(item.get("vacancies"))
                if vacancies_text == "1":
                    lines.append(f"- {label}: 1 posto disponibile")
                else:
                    lines.append(f"- {label}: {vacancies_text} posti disponibili")
        lines.append("")
        lines.append("Puoi procedere con la prenotazione qui:")
        lines.append(BOOKING_LINK)
        lines.append("")
        lines.append(
            "Ti preghiamo di selezionare la data nella pagina di prenotazione."
        )
        return "\n".join(lines)

    if language == "pt":
        lines = ["Aqui estão as opções disponíveis para o horário solicitado:"]
        for item in results:
            label = item.get("reply_label", "Cruzeiro")

            if is_private_result(item):
                lines.append(f"- {label}: disponível")
            else:
                vacancies_text = format_shared_vacancies(item.get("vacancies"))
                if vacancies_text == "1":
                    lines.append(f"- {label}: 1 lugar disponível")
                else:
                    lines.append(f"- {label}: {vacancies_text} lugares disponíveis")
        lines.append("")
        lines.append("Pode avançar com a sua reserva aqui:")
        lines.append(BOOKING_LINK)
        lines.append("")
        lines.append("Por favor selecione a data na página de reservas.")
        return "\n".join(lines)

    lines = ["Here are the available options for the requested time:"]
    for item in results:
        label = item.get("reply_label", "Cruise")

        if is_private_result(item):
            lines.append(f"- {label}: available")
        else:
            vacancies_text = format_shared_vacancies(item.get("vacancies"))
            if vacancies_text == "1":
                lines.append(f"- {label}: 1 spot available")
            else:
                lines.append(f"- {label}: {vacancies_text} spots available")
    lines.append("")
    lines.append("You can proceed with your booking here:")
    lines.append(BOOKING_LINK)
    lines.append("")
    lines.append("Please select the date on the booking page.")
    return "\n".join(lines)


def build_best_choice_reply(
    history: list[dict], language: str, passenger_count: int | None = None
) -> str:
    recent_text = " ".join(
        item.get("content", "")
        for item in history[-10:]
        if item.get("role") in {"user", "assistant"}
    ).lower()

    mentions_red = "red" in recent_text
    mentions_diamond = "diamond" in recent_text
    mentions_gems = "gems" in recent_text
    group_large = isinstance(passenger_count, int) and passenger_count >= 10

    if language == "el":
        if mentions_red and mentions_diamond:
            if group_large:
                return (
                    f"Για {passenger_count} άτομα, το Red Cruise είναι συνήθως η καλύτερη επιλογή "
                    "αν προτιμάτε πιο ζωντανή ατμόσφαιρα και πολύ καλή σχέση αξίας.\n\n"
                    "Αν προτιμάτε κάτι πιο premium και πιο χαλαρό, τότε το Diamond είναι η καλύτερη επιλογή.\n\n"
                    "Με απλά λόγια:\n"
                    "Red = καλύτερη αξία για μεγαλύτερη παρέα\n"
                    "Diamond = πιο premium συνολική εμπειρία"
                )
            return (
                "Το Red Cruise είναι συνήθως η καλύτερη επιλογή αν προτιμάτε πιο ζωντανή ατμόσφαιρα και πολύ καλή σχέση αξίας.\n\n"
                "Αν προτιμάτε κάτι πιο premium και πιο χαλαρό, τότε το Diamond είναι η καλύτερη επιλογή.\n\n"
                "Με απλά λόγια:\n"
                "Red = καλύτερη αξία\n"
                "Diamond = πιο premium εμπειρία"
            )

        if mentions_red and mentions_gems:
            return (
                "Το Red Cruise είναι συνήθως η καλύτερη επιλογή αν θέλετε πιο ζωντανή ατμόσφαιρα και καλύτερη αξία.\n\n"
                "Το Gems είναι καλύτερο αν προτιμάτε πιο άνετη και πιο refined εμπειρία.\n\n"
                "Με απλά λόγια:\n"
                "Red = καλύτερη αξία\n"
                "Gems = πιο ισορροπημένη και πιο άνετη εμπειρία"
            )

        if mentions_diamond:
            return "Το Diamond είναι η καλύτερη επιλογή αν προτεραιότητά σας είναι μια πιο premium και πιο ξεχωριστή εμπειρία."

        return (
            "Εξαρτάται από το τι προτιμάτε περισσότερο.\n\n"
            "Για καλύτερη αξία και πιο ζωντανή ατμόσφαιρα, το Red είναι συνήθως η πιο δυνατή επιλογή.\n"
            "Για πιο premium και πιο χαλαρή εμπειρία, το Diamond ή το Gems είναι συνήθως καλύτερα."
        )

    if language == "it":
        if mentions_red and mentions_diamond:
            if group_large:
                return (
                    f"Per {passenger_count} persone, la Red Cruise è di solito la scelta migliore "
                    "se preferite un’atmosfera più vivace e un ottimo rapporto qualità-prezzo.\n\n"
                    "Se invece desiderate qualcosa di più premium e più rilassato, allora Diamond è la scelta migliore.\n\n"
                    "In breve:\n"
                    "Red = migliore valore per un gruppo più grande\n"
                    "Diamond = esperienza complessiva più premium"
                )
            return (
                "La Red Cruise è di solito la scelta migliore se preferite un’atmosfera più vivace e un ottimo rapporto qualità-prezzo.\n\n"
                "Se invece desiderate qualcosa di più premium e più rilassato, allora Diamond è la scelta migliore.\n\n"
                "In breve:\n"
                "Red = migliore valore\n"
                "Diamond = esperienza più premium"
            )

        return (
            "Dipende dal tipo di esperienza che preferite.\n\n"
            "Per un’atmosfera più vivace e un ottimo rapporto qualità-prezzo, Red è di solito la scelta migliore.\n"
            "Per un’esperienza più premium e rilassata, Diamond o Gems sono generalmente opzioni migliori."
        )

    if language == "pt":
        if mentions_red and mentions_diamond:
            if group_large:
                return (
                    f"Para {passenger_count} pessoas, o Red Cruise costuma ser a melhor opção "
                    "se preferirem um ambiente mais animado e uma excelente relação qualidade-preço.\n\n"
                    "Se preferirem algo mais premium e mais tranquilo, então o Diamond é a melhor escolha.\n\n"
                    "Em resumo:\n"
                    "Red = melhor valor para um grupo maior\n"
                    "Diamond = experiência geral mais premium"
                )
            return (
                "O Red Cruise costuma ser a melhor opção se preferirem um ambiente mais animado e uma excelente relação qualidade-preço.\n\n"
                "Se preferirem algo mais premium e mais tranquilo, então o Diamond é a melhor escolha.\n\n"
                "Em resumo:\n"
                "Red = melhor valor\n"
                "Diamond = experiência mais premium"
            )

        return (
            "Depende do tipo de experiência que preferem.\n\n"
            "Para um ambiente mais animado e melhor valor, o Red costuma ser a melhor opção.\n"
            "Para uma experiência mais premium e mais tranquila, Diamond ou Gems costumam ser melhores escolhas."
        )

    if mentions_red and mentions_diamond:
        if group_large:
            return (
                f"For {passenger_count} people, Red Cruise is usually the best choice if you prefer a more lively atmosphere and very good value.\n\n"
                "If you prefer a more premium and more relaxed experience, Diamond is the stronger option.\n\n"
                "In simple terms:\n"
                "Red = best value for a larger group\n"
                "Diamond = more premium overall experience"
            )
        return (
            "Red Cruise is usually the best choice if you prefer a more lively atmosphere and very good value.\n\n"
            "If you prefer a more premium and more relaxed experience, Diamond is the stronger option.\n\n"
            "In simple terms:\n"
            "Red = best value\n"
            "Diamond = more premium overall experience"
        )

    if mentions_red and mentions_gems:
        return (
            "Red Cruise is usually the best choice if you prefer a more lively atmosphere and better value.\n\n"
            "Gems is the stronger option if you prefer a more comfortable and more refined experience.\n\n"
            "In simple terms:\n"
            "Red = best value\n"
            "Gems = more balanced and more comfortable experience"
        )

    if mentions_diamond:
        return "Diamond is the best choice if your priority is a more premium and more distinctive experience."

    return (
        "It depends on the kind of experience you prefer.\n\n"
        "For better value and a more lively atmosphere, Red is usually the strongest choice.\n"
        "For a more premium and more relaxed experience, Diamond or Gems are usually better options."
    )


BASE_TOUR_KEYS = {
    "red",
    "gems",
    "platinum",
    "diamond",
    "lagoon_380_400",
    "emily",
    "ferretti_731",
    "ferretti_55",
}


def is_base_tour_key(tour_key: str | None) -> bool:
    return bool(tour_key and tour_key in BASE_TOUR_KEYS)


def is_available_result(data) -> bool:
    return (
        isinstance(data, dict)
        and data.get("success")
        and isinstance(data.get("availability"), dict)
        and data["availability"].get("available") is True
    )


def format_pretty_date(date_str: str) -> str:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d %B %Y")
    except ValueError:
        return date_str


def build_dual_period_reply(
    morning_data,
    sunset_data,
    date_str: str,
    language: str,
) -> str | None:
    morning_available = is_available_result(morning_data)
    sunset_available = is_available_result(sunset_data)

    if not morning_available and not sunset_available:
        return None

    if morning_available != sunset_available:
        return None

    morning_label = (
        morning_data.get("reply_label", "Morning Cruise")
        if isinstance(morning_data, dict)
        else "Morning Cruise"
    )
    sunset_label = (
        sunset_data.get("reply_label", "Sunset Cruise")
        if isinstance(sunset_data, dict)
        else "Sunset Cruise"
    )

    booking_url = (
        (morning_data.get("booking_url") if isinstance(morning_data, dict) else None)
        or (sunset_data.get("booking_url") if isinstance(sunset_data, dict) else None)
        or BOOKING_LINK
    )

    pretty_date = format_pretty_date(date_str)

    if language == "el":
        return (
            f"Για τις {pretty_date}, οι παρακάτω επιλογές είναι διαθέσιμες:\n\n"
            f"- {morning_label}\n"
            f"- {sunset_label}\n\n"
            f"Μπορείτε να προχωρήσετε στην κράτησή σας εδώ:\n{booking_url}\n\n"
            "Παρακαλούμε επιλέξτε την ημερομηνία στη σελίδα κράτησης."
        )

    if language == "it":
        return (
            f"Per il {pretty_date}, sono disponibili le seguenti opzioni:\n\n"
            f"- {morning_label}\n"
            f"- {sunset_label}\n\n"
            f"Puoi procedere con la prenotazione qui:\n{booking_url}\n\n"
            "Ti preghiamo di selezionare la data nella pagina di prenotazione."
        )

    if language == "pt":
        return (
            f"Para {pretty_date}, as seguintes opções estão disponíveis:\n\n"
            f"- {morning_label}\n"
            f"- {sunset_label}\n\n"
            f"Pode avançar com a sua reserva aqui:\n{booking_url}\n\n"
            "Por favor selecione a data na página de reservas."
        )

    return (
        f"For {pretty_date}, the following options are available:\n\n"
        f"- {morning_label}\n"
        f"- {sunset_label}\n\n"
        f"You can proceed with your booking here:\n{booking_url}\n\n"
        "Please select the date on the booking page."
    )


@app.get("/")
def root():
    return {"message": "Santorini bot is running"}


@app.get("/admin/logs")
def admin_logs():
    return {"logs": get_chat_logs(200)}


@app.get("/admin/sessions")
def admin_sessions(
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
):
    return {
        "sessions": get_chat_sessions(
            1000,
            from_date=from_date,
            to_date=to_date,
        )
    }


@app.post("/chat")
def chat(request: ChatRequest):
    user_message = request.message.strip()
    history = request.history or []
    language = detect_language(user_message)
    session_id = request.session_id

    tour_key = detect_tour_key(user_message)
    date_str = detect_date(user_message)
    period = detect_period(user_message)
    tour_facts = build_tour_facts_block(tour_key) if tour_key else ""
    passenger_count = detect_passenger_count(user_message, history)

    if not user_message:
        reply = get_text("empty_reply", language, BOOKING_LINK, WHATSAPP_LINK)
        return log_and_return(
            user_message="",
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=None,
            session_id=session_id,
        )

    if is_discount_request(user_message):
        reply = get_text("discount_reply", language, BOOKING_LINK, WHATSAPP_LINK)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=None,
            session_id=session_id,
        )

    if is_cruise_passenger(user_message):
        reply = get_text(
            "cruise_passenger_reply", language, BOOKING_LINK, WHATSAPP_LINK
        )
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=None,
            session_id=session_id,
        )

    if is_contact_request(user_message):
        reply = get_text("contact_reply", language, BOOKING_LINK, WHATSAPP_LINK)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=None,
            session_id=session_id,
        )

    if is_personal_booking_request(user_message):
        reply = get_text("booking_details_reply", language, BOOKING_LINK, WHATSAPP_LINK)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=None,
            session_id=session_id,
        )

    if is_pregnancy_question(user_message):
        reply = get_text("pregnancy_reply", language, BOOKING_LINK, WHATSAPP_LINK)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=None,
            session_id=session_id,
        )

    if (
        is_uncertain_whatsapp_case(user_message)
        and "pick up" not in user_message.lower()
        and "pickup" not in user_message.lower()
        and "pick-up" not in user_message.lower()
        and "transfer" not in user_message.lower()
    ):
        conversation_history = ""
        if history:
            lines = []
            for item in history[-8:]:
                role = item.get("role", "")
                content = item.get("content", "")
                if role == "user":
                    lines.append(f"User: {content}")
                elif role == "assistant":
                    lines.append(f"Assistant: {content}")
            conversation_history = "\n".join(lines)

        knowledge = get_company_knowledge()

        prompt = f"""
You are the Sunset Oia digital assistant.

IMPORTANT LANGUAGE RULE:
- Always reply in the same language as the user's latest message.

Your tone:
- Warm, natural and human — never robotic
- Friendly and professional
- Keep replies short (3–5 lines)
- Avoid repetitive phrases like "Great news"

Conversation style:
- Answer exactly what the user asked — no more, no less
- Be clear, direct and helpful
- Do NOT add unnecessary explanations
- Do NOT introduce new cruise options unless the user explicitly asks
- If the user mentions specific cruises (e.g. Red vs Diamond), ONLY talk about those
- Do NOT expand to a third option (e.g. Platinum) unless explicitly requested

Sales approach:
- Guide naturally, do not push
- Help the user decide ONLY based on what they asked
- If the user is comparing → explain differences clearly, no upselling
- If the user asks for recommendation → suggest ONE best option, not multiple
- Only include booking link when it is useful

Knowledge:
- Use only the company knowledge provided
- Do not invent information
- If something is not available, say it clearly and suggest alternatives
- Always assume the user is asking about the onboard cruise experience when relevant
- Never say that you cannot check availability if it can be handled
- Treat follow-ups as continuation of previous context
- Do not use markdown bold with asterisks
- Avoid words like cheap — use better value, more premium, more relaxed, etc.
- Never mix details between Red, Gems, Platinum, Diamond, or private cruises
- For factual answers, prioritize STRUCTURED TOUR FACTS

Special handling:
- Cruise ship guests → direct to WhatsApp
- Dietary questions → answer clearly
- Personal booking details → do not invent
- Sensitive or uncertain cases → give best safe answer + suggest WhatsApp

STRICT RULES:
- Answer only the user's exact question
- Do not mention any cruise that the user did not ask about
- If the conversation is about Red and Diamond, mention only Red and Diamond
- If the user asks by budget, answer only in terms of the cruises already under discussion
- Do not introduce Gems, Platinum, or any other cruise unless the user explicitly asks
- No upselling unless asked
- No adding “you may also like…” style sentences
- Do not end the reply with extra offers such as "I can also help you choose..."
- Stay focused on the exact question

BOOKING LINK:
{BOOKING_LINK}

COMPANY KNOWLEDGE:
{knowledge}

STRUCTURED TOUR FACTS:
{tour_facts}

CONVERSATION HISTORY:
{conversation_history}

USER MESSAGE:
{user_message}
"""
        try:
            reply = get_ai_reply(prompt)
            return log_and_return(
                user_message=user_message,
                reply=reply,
                language=language,
                fallback=False,
                detected_tour=None,
                session_id=session_id,
            )
        except Exception as e:
            print("OPENAI ERROR:", e)

            reply = get_text(
                "whatsapp_uncertain_reply", language, BOOKING_LINK, WHATSAPP_LINK
            )

        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=True,
            detected_tour=None,
            session_id=session_id,
        )

    if is_capacity_request(user_message) and is_multi_capacity_request(user_message):
        date_str = detect_date(user_message)
        period = detect_period(user_message)
        effective_date = date_str or get_effective_date(user_message, history)

        seasonal_reply = get_seasonal_reply(
            date_str=effective_date,
            language=language,
            booking_link=BOOKING_LINK,
            whatsapp_link=WHATSAPP_LINK,
            tour_key=tour_key,
            period=period,
            generic_availability=True,
        )
        if seasonal_reply:
            return log_and_return(
                user_message=user_message,
                reply=seasonal_reply,
                language=language,
                fallback=False,
                detected_tour=None,
                session_id=session_id,
            )

        results = safe_find_available_tours(
            effective_date, period, user_message, passenger_count
        )

        if results:
            capacity_filtered = filter_by_capacity(results, passenger_count)
            if capacity_filtered:
                reply_text = build_multi_capacity_reply(capacity_filtered, language)
                return log_and_return(
                    user_message=user_message,
                    reply=reply_text,
                    language=language,
                    fallback=False,
                    detected_tour=None,
                    session_id=session_id,
                )

        reply = get_text("availability_fallback", language, BOOKING_LINK, WHATSAPP_LINK)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=True,
            detected_tour=None,
            session_id=session_id,
        )

    if is_capacity_request(user_message):
        last_tour_key, last_date_str = get_last_tour_and_date_from_history(
            user_message, history
        )

        seasonal_reply = get_seasonal_reply(
            date_str=last_date_str,
            language=language,
            booking_link=BOOKING_LINK,
            whatsapp_link=WHATSAPP_LINK,
            tour_key=last_tour_key,
        )
        if seasonal_reply:
            return log_and_return(
                user_message=user_message,
                reply=seasonal_reply,
                language=language,
                fallback=False,
                detected_tour=last_tour_key,
                session_id=session_id,
            )

        if last_tour_key and last_date_str:
            data = safe_check_tour_availability(last_tour_key, last_date_str)
            if data:
                reply_text = build_capacity_reply(data, language)
                return log_and_return(
                    user_message=user_message,
                    reply=reply_text,
                    language=language,
                    fallback=False,
                    detected_tour=last_tour_key,
                    session_id=session_id,
                )

            reply = get_text(
                "availability_fallback", language, BOOKING_LINK, WHATSAPP_LINK
            )
            return log_and_return(
                user_message=user_message,
                reply=reply,
                language=language,
                fallback=True,
                detected_tour=last_tour_key,
                session_id=session_id,
            )

        reply = get_text("spots_fallback", language, BOOKING_LINK, WHATSAPP_LINK)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=True,
            detected_tour=None,
            session_id=session_id,
        )

    cruise_type_intent = detect_cruise_type_intent(user_message, history)
    user_message_lower = user_message.lower()

    price_intent = any(
        keyword in user_message_lower
        for keyword in [
            "price",
            "rate",
            "cost",
            "how much",
            "how much does it cost",
            "how much is",
            "what is the price",
            "τιμή",
            "ποσο κοστιζει",
            "πόσο κοστίζει",
            "quanto custa",
            "prezzo",
        ]
    )

    comparison_intent = (
        "difference" in user_message_lower
        or "compare" in user_message_lower
        or "comparison" in user_message_lower
        or "which is better" in user_message_lower
        or "best option" in user_message_lower
        or "recommend" in user_message_lower
        or is_best_choice_question(user_message)
    )

    time_comparison_intent = is_time_comparison(user_message)

    if time_comparison_intent:
        reply = build_time_comparison_reply(language)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=tour_key,
            session_id=session_id,
        )

    if is_sunset_concern(user_message):
        reply = build_sunset_reassurance_reply(language)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=tour_key,
            session_id=session_id,
        )

    if is_sunset_question(user_message):
        reply = get_text("sunset_reply", language, BOOKING_LINK, WHATSAPP_LINK)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=tour_key,
            session_id=session_id,
        )

    if price_intent:
        effective_tour_key = tour_key
        effective_date_str = date_str

        if not effective_tour_key or not effective_date_str:
            last_tour_key, last_date_str = get_last_tour_and_date_from_history(
                user_message, history
            )

            if not effective_tour_key:
                effective_tour_key = last_tour_key
            if not effective_date_str:
                effective_date_str = last_date_str

        seasonal_reply = get_seasonal_reply(
            date_str=effective_date_str,
            language=language,
            booking_link=BOOKING_LINK,
            whatsapp_link=WHATSAPP_LINK,
            tour_key=effective_tour_key,
        )
        if seasonal_reply:
            return log_and_return(
                user_message=user_message,
                reply=seasonal_reply,
                language=language,
                fallback=False,
                detected_tour=effective_tour_key,
                session_id=session_id,
            )

        if effective_tour_key and effective_date_str:
            data = safe_check_tour_availability(effective_tour_key, effective_date_str)
            print("PRICE DATA DEBUG:", data)
            if data:
                availability = (
                    data.get("availability", {}) if isinstance(data, dict) else {}
                )

                if not isinstance(availability, dict):
                    availability = {}

                reply_label = data.get("reply_label", "this cruise")
                booking_url = data.get("booking_url", BOOKING_LINK)

                amount = availability.get("adult_price")
                currency = "EUR"

                if amount is not None:
                    if language == "el":
                        reply = (
                            f"Η τιμή για το {reply_label} είναι {amount} {currency} ανά άτομο.\n\n"
                            f"Μπορείτε να προχωρήσετε στην κράτησή σας εδώ:\n{booking_url}\n\n"
                            "Παρακαλούμε επιλέξτε την ημερομηνία στη σελίδα κράτησης."
                        )
                    elif language == "it":
                        reply = (
                            f"Il prezzo per {reply_label} è {amount} {currency} a persona.\n\n"
                            f"Puoi procedere con la prenotazione qui:\n{booking_url}\n\n"
                            "Ti preghiamo di selezionare la data nella pagina di prenotazione."
                        )
                    elif language == "pt":
                        reply = (
                            f"O preço para {reply_label} é {amount} {currency} por pessoa.\n\n"
                            f"Pode avançar com a sua reserva aqui:\n{booking_url}\n\n"
                            "Por favor selecione a data na página de reservas."
                        )
                    else:
                        reply = (
                            f"The price for {reply_label} is {amount} {currency} per person.\n\n"
                            f"You can proceed with your booking here:\n{booking_url}\n\n"
                            "Please select the date on the booking page."
                        )

                    return log_and_return(
                        user_message=user_message,
                        reply=reply,
                        language=language,
                        fallback=False,
                        detected_tour=effective_tour_key,
                        session_id=session_id,
                    )

        reply = get_text("availability_fallback", language, BOOKING_LINK, WHATSAPP_LINK)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=True,
            detected_tour=effective_tour_key,
            session_id=session_id,
        )

    availability_intent = (
        not comparison_intent
        and not price_intent
        and not time_comparison_intent
        and not is_sunset_concern(user_message)
        and (
            is_availability_request(user_message)
            or (
                is_followup(user_message)
                and has_recent_availability_context(
                    history,
                    is_availability_request_fn=is_availability_request,
                    detect_period_fn=detect_period,
                )
            )
            or (
                period is not None
                and has_recent_availability_context(
                    history,
                    is_availability_request_fn=is_availability_request,
                    detect_period_fn=detect_period,
                )
            )
        )
    )

    seasonal_reply = get_seasonal_reply(
        date_str=date_str,
        language=language,
        booking_link=BOOKING_LINK,
        whatsapp_link=WHATSAPP_LINK,
        tour_key=tour_key,
        period=period,
        generic_availability=availability_intent,
    )
    if seasonal_reply:
        return log_and_return(
            user_message=user_message,
            reply=seasonal_reply,
            language=language,
            fallback=False,
            detected_tour=tour_key,
            session_id=session_id,
        )

    if is_base_tour_key(tour_key) and date_str:
        morning_key = f"{tour_key}_morning"
        sunset_key = f"{tour_key}_sunset"

        morning_data = safe_check_tour_availability(morning_key, date_str)
        sunset_data = safe_check_tour_availability(sunset_key, date_str)

        dual_period_reply = build_dual_period_reply(
            morning_data=morning_data,
            sunset_data=sunset_data,
            date_str=date_str,
            language=language,
        )

        if dual_period_reply:
            return log_and_return(
                user_message=user_message,
                reply=dual_period_reply,
                language=language,
                fallback=False,
                detected_tour=tour_key,
                session_id=session_id,
            )

        if is_available_result(morning_data):
            reply_text = build_availability_reply(morning_data)
            reply_text = translate_availability_reply(reply_text, language)
            return log_and_return(
                user_message=user_message,
                reply=reply_text,
                language=language,
                fallback=False,
                detected_tour=morning_key,
                session_id=session_id,
            )

        if is_available_result(sunset_data):
            reply_text = build_availability_reply(sunset_data)
            reply_text = translate_availability_reply(reply_text, language)
            return log_and_return(
                user_message=user_message,
                reply=reply_text,
                language=language,
                fallback=False,
                detected_tour=sunset_key,
                session_id=session_id,
            )

        reply = get_text("availability_fallback", language, BOOKING_LINK, WHATSAPP_LINK)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=True,
            detected_tour=tour_key,
            session_id=session_id,
        )

    if tour_key and date_str:
        data = safe_check_tour_availability(tour_key, date_str)

        is_available = is_available_result(data)

        if is_available:
            reply_text = build_availability_reply(data)
            reply_text = translate_availability_reply(reply_text, language)
            return log_and_return(
                user_message=user_message,
                reply=reply_text,
                language=language,
                fallback=False,
                detected_tour=tour_key,
                session_id=session_id,
            )

        alternative_results = safe_find_available_tours(
            date_str,
            period,
            user_message,
            passenger_count,
            ignore_requested_tours=True,
        )
        print("RAW ALTERNATIVE RESULTS:", alternative_results)

        capacity_filtered = filter_by_capacity(
            alternative_results or [],
            passenger_count,
        )
        print("CAPACITY FILTERED RESULTS:", capacity_filtered)

        prepared_alternatives = prepare_alternative_results(
            results=capacity_filtered,
            requested_tour_key=tour_key,
            passenger_count=passenger_count,
        )
        print("PREPARED ALTERNATIVES:", prepared_alternatives)

        alternative_reply = build_unavailable_alternatives_reply(
            requested_tour_key=tour_key,
            alternatives=prepared_alternatives,
            language=language,
            booking_link=BOOKING_LINK,
        )
        print("ALTERNATIVE REPLY:", alternative_reply)

        if alternative_reply:
            return log_and_return(
                user_message=user_message,
                reply=alternative_reply,
                language=language,
                fallback=False,
                detected_tour=tour_key,
                session_id=session_id,
            )

        if data and isinstance(data.get("availability"), dict):
            fallback_data = {
                **data,
                "alternative_tours": prepared_alternatives,
            }
            print("FALLBACK DATA:", fallback_data)

            reply_text = build_availability_reply(fallback_data)
            print("FINAL FALLBACK REPLY:", reply_text)

            reply_text = translate_availability_reply(reply_text, language)
            return log_and_return(
                user_message=user_message,
                reply=reply_text,
                language=language,
                fallback=False,
                detected_tour=tour_key,
                session_id=session_id,
            )

        reply = get_text("availability_fallback", language, BOOKING_LINK, WHATSAPP_LINK)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=True,
            detected_tour=tour_key,
            session_id=session_id,
        )

    if date_str or availability_intent:
        effective_date = get_effective_date(user_message, history)

        seasonal_reply = get_seasonal_reply(
            date_str=effective_date,
            language=language,
            booking_link=BOOKING_LINK,
            whatsapp_link=WHATSAPP_LINK,
            tour_key=tour_key,
            period=period,
            generic_availability=True,
        )
        if seasonal_reply:
            return log_and_return(
                user_message=user_message,
                reply=seasonal_reply,
                language=language,
                fallback=False,
                detected_tour=tour_key,
                session_id=session_id,
            )

        results = safe_find_available_tours(
            effective_date, period, user_message, passenger_count
        )
        if results is None:
            reply = get_text(
                "availability_fallback", language, BOOKING_LINK, WHATSAPP_LINK
            )
            return log_and_return(
                user_message=user_message,
                reply=reply,
                language=language,
                fallback=True,
                detected_tour=tour_key,
                session_id=session_id,
            )

        capacity_filtered = filter_by_capacity(results, passenger_count)

        filtered_results = filter_results_by_cruise_type(
            capacity_filtered,
            cruise_type_intent,
        )

        if filtered_results:
            reply_text = build_multi_availability_reply(
                filtered_results, effective_date, period, language
            )
            reply_text = translate_availability_reply(reply_text, language)
            return log_and_return(
                user_message=user_message,
                reply=reply_text,
                language=language,
                fallback=False,
                detected_tour=tour_key,
                session_id=session_id,
            )

        reply = get_text("availability_fallback", language, BOOKING_LINK, WHATSAPP_LINK)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=True,
            detected_tour=tour_key,
            session_id=session_id,
        )

    recent_text = " ".join(
        item.get("content", "")
        for item in history[-10:]
        if item.get("role") in {"user", "assistant"}
    ).lower()

    budget_followup = (
        "budget" in user_message.lower() or "value" in user_message.lower()
    )

    if budget_followup and history:
        mentions_red = "red" in recent_text
        mentions_diamond = "diamond" in recent_text
        mentions_gems = "gems" in recent_text

        if mentions_red and mentions_diamond and not mentions_gems:
            if language == "el":
                reply = (
                    "Αν η βασική προτεραιότητα είναι ο προϋπολογισμός, το Red Cruise είναι η καλύτερη επιλογή σε αξία.\n\n"
                    "Το Diamond είναι η πιο premium επιλογή, με μικρότερο group και περισσότερες παροχές onboard."
                )
            elif language == "it":
                reply = (
                    "Se il budget è la priorità principale, la Red Cruise è l’opzione con il miglior rapporto qualità-prezzo.\n\n"
                    "Diamond è la scelta più premium, con un gruppo più piccolo e più servizi a bordo."
                )
            elif language == "pt":
                reply = (
                    "Se o orçamento for a prioridade principal, o Red Cruise é a opção com melhor valor.\n\n"
                    "Diamond é a escolha mais premium, com um grupo mais pequeno e mais extras a bordo."
                )
            else:
                reply = (
                    "If budget is the main priority, Red Cruise is the better value option.\n\n"
                    "Diamond is the more premium choice, with a smaller group and more onboard extras."
                )

            return log_and_return(
                user_message=user_message,
                reply=reply,
                language=language,
                fallback=False,
                detected_tour=tour_key,
                session_id=session_id,
            )

        if mentions_red and mentions_gems and not mentions_diamond:
            if language == "el":
                reply = (
                    "Αν η βασική προτεραιότητα είναι ο προϋπολογισμός, το Red Cruise είναι συνήθως η καλύτερη επιλογή σε αξία.\n\n"
                    "Το Gems είναι πιο άνετο και πιο refined, αλλά συνήθως όχι η πιο οικονομική επιλογή."
                )
            elif language == "it":
                reply = (
                    "Se il budget è la priorità principale, la Red Cruise è di solito l’opzione con il miglior valore.\n\n"
                    "Gems è più comoda e più raffinata, ma di solito non è l’opzione più economica."
                )
            elif language == "pt":
                reply = (
                    "Se o orçamento for a prioridade principal, o Red Cruise costuma ser a opção com melhor valor.\n\n"
                    "Gems é mais confortável e mais refinado, mas normalmente não é a opção mais económica."
                )
            else:
                reply = (
                    "If budget is the main priority, Red Cruise is usually the better value option.\n\n"
                    "Gems is more comfortable and more refined, but usually not the lower-priced option."
                )

            return log_and_return(
                user_message=user_message,
                reply=reply,
                language=language,
                fallback=False,
                detected_tour=tour_key,
                session_id=session_id,
            )

    if is_best_choice_question(user_message) and history:
        reply = build_best_choice_reply(
            history=history,
            language=language,
            passenger_count=passenger_count,
        )
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=tour_key,
            session_id=session_id,
        )

    if is_greeting(user_message):
        reply = get_text("greeting_reply", language, BOOKING_LINK, WHATSAPP_LINK)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=tour_key,
            session_id=session_id,
        )

    short_followup = len(user_message.split()) <= 4

    if (
        not is_followup(user_message)
        and not short_followup
        and is_clearly_irrelevant(user_message)
    ):
        reply = get_text("irrelevant_reply", language, BOOKING_LINK, WHATSAPP_LINK)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=tour_key,
            session_id=session_id,
        )

    conversation_history = ""
    if history:
        lines = []
        for item in history[-8:]:
            role = item.get("role", "")
            content = item.get("content", "")
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
        conversation_history = "\n".join(lines)

    knowledge = get_company_knowledge()

    prompt = f"""
You are the Sunset Oia digital assistant.

IMPORTANT LANGUAGE RULE:
- Always reply in the same language as the user's latest message.
- If the user writes in Greek, reply in Greek.
- If the user writes in English, reply in English.
- If the user writes in Italian, reply in Italian.
- If the user writes in Portuguese, reply in Portuguese.

Your tone:
- Warm, natural and human — never robotic
- Friendly and professional
- Avoid repeating the same phrases in every reply
- Keep replies short (3–5 lines), but helpful

Conversation style:
- Vary your phrasing
- Sound like a real person, not a script
- Adapt naturally to the user's question

Sales approach:
- Gently guide the user, do not push
- Suggest options based on their needs (group size, budget, experience)
- Only include the booking link when it is useful and relevant
- When appropriate, make soft recommendations

Knowledge:
- Use only the company knowledge provided
- Do not invent information
- If something is not available, say it clearly and suggest alternatives when possible
- Always assume the user is asking about the onboard cruise experience if the question can logically relate to it
- Never say that you cannot check live availability if the bot can route the request to the booking or availability flow
- For follow-up questions such as "and for sunset?" or "what about the morning one?", treat them as a continuation of the previous cruise/availability context when relevant
- Do not use markdown bold with asterisks in your replies
- Do not use words like cheap or cheaper for cruise recommendations; prefer phrases such as better value, very good value, more premium, more relaxed, or more lively
- If STRUCTURED TOUR FACTS are provided, treat them as higher priority than general knowledge
- Never mix details between Red, Gems, Platinum, Diamond, or private cruises
- For factual questions about a specific cruise, use the structured tour facts first

Special handling:
- Cruise ship guests should be directed to WhatsApp
- Dietary questions should be answered clearly and confidently
- Personal booking details should not be invented
- When a question is relevant but sensitive, uncertain, or case-specific, give the safest helpful reply and suggest WhatsApp

BOOKING LINK:
{BOOKING_LINK}

COMPANY KNOWLEDGE:
{knowledge}

STRUCTURED TOUR FACTS:
{tour_facts}

CONVERSATION HISTORY:
{conversation_history}

USER MESSAGE:
{user_message}
"""

    reply = get_ai_reply(prompt)
    return log_and_return(
        user_message=user_message,
        reply=reply,
        language=language,
        fallback=False,
        detected_tour=tour_key,
        session_id=session_id,
    )