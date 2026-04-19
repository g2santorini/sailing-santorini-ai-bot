import urllib.parse
from datetime import datetime

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.routes.availability_routes import router as availability_router
from app.services.alternative_service import (
    build_unavailable_alternatives_reply,
    filter_by_capacity,
    prepare_alternative_results,
)
from app.services.availability_safe_service import (
    safe_check_tour_availability,
    safe_find_available_tours,
)
from app.services.chat_logger import (
    get_chat_logs,
    get_chat_sessions,
    init_db,
    save_chat_log,
)
from app.services.context_service import (
    get_effective_date,
    get_last_tour_and_date_from_history,
    has_recent_availability_context,
)
from app.services.conversation_state import create_empty_state
from app.services.date_detector import detect_date
from app.services.intent_service import (
    is_availability_request,
    is_best_choice_question,
    is_capacity_request,
    is_contact_request,
    is_discount_request,
    is_followup,
    is_greeting,
    is_multi_capacity_request,
    is_pregnancy_question,
    is_sunset_concern,
    is_sunset_question,
    is_time_comparison,
)
from app.services.knowledge_service import get_company_knowledge
from app.services.multi_reply_builder import build_multi_availability_reply
from app.services.openai_service import get_ai_reply
from app.services.reply_builder import (
    build_availability_reply,
    build_time_comparison_reply,
)
from app.services.request_parser_service import (
    detect_cruise_type_intent,
    detect_passenger_count,
)
from app.services.response_router import route_message
from app.services.season_service import get_seasonal_reply
from app.services.tour_detector import detect_tour_key
from app.services.tour_mapping import build_tour_facts_block
from app.services.translation_service import get_text

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

print("MAIN WITH HISTORY + ENGLISH-ONLY MODE LOADED")


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = Field(default_factory=list)
    session_id: str | None = None


BOOKING_LINK = "https://sailingsantorini.link-twist.com/"
WEBSITE_LINK = "https://sailing-santorini.com/"
WHATSAPP_LINK = "https://wa.me/306972805193"
DEFAULT_LANGUAGE = "en"

# --------------------------------------------------
# Simple in-memory conversation state
# --------------------------------------------------
SESSION_STATES: dict[str, dict] = {}


def get_session_state(session_id: str | None) -> dict:
    if not session_id:
        return create_empty_state()

    return SESSION_STATES.get(session_id, create_empty_state())


def save_session_state(session_id: str | None, state: dict) -> None:
    if not session_id:
        return

    SESSION_STATES[session_id] = state


def clear_session_state(session_id: str | None) -> None:
    if not session_id:
        return

    SESSION_STATES[session_id] = create_empty_state()


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


def build_sunset_reassurance_reply() -> str:
    return (
        "Please do not worry about missing the sunset.\n\n"
        "Although the departure time remains fixed, the cruise duration is adjusted depending on the sunset time each day.\n"
        "During the summer months, the cruise lasts longer so that you can fully enjoy the sunset on board.\n\n"
        "All sunset cruises are designed so that guests enjoy the sunset from the catamaran."
    )


def build_date_clarification_reply() -> str:
    return "For which date would you like me to check availability?"


def build_conversation_history(history: list[dict]) -> str:
    if not history:
        return ""

    lines = []
    for item in history[-8:]:
        role = item.get("role", "")
        content = item.get("content", "")
        if role == "user":
            lines.append(f"User: {content}")
        elif role == "assistant":
            lines.append(f"Assistant: {content}")

    return "\n".join(lines)


def build_comparison_recommendation_prompt(
    user_message: str,
    conversation_history: str,
    knowledge: str,
    tour_facts: str,
) -> str:
    return f"""
You are the Sunset Oia digital assistant.

IMPORTANT LANGUAGE RULE:
- Always reply in English.

TONE:
- Warm, natural and human
- Friendly and professional
- Keep replies short (3–5 lines)
- Avoid repetitive phrasing

CRITICAL RULE:
If the user asks for comparison, recommendation, or guidance
(e.g. "which is better", "which tour is the best", "what do you recommend", "morning or sunset"):

→ Answer the question directly
→ Do NOT ask for a date
→ Do NOT mention availability
→ Do NOT redirect to booking unless truly helpful
→ Do NOT turn the reply into an availability flow

CONTEXT RULE:
- Answer ONLY based on the cruises or options mentioned by the user
- If the user asks about morning vs sunset, answer as an experience comparison
- If the user adds another option in a follow-up (e.g. "and what about Gems?"), continue the same comparison/recommendation context

STYLE:
- Be clear, short, and useful
- Sound like a good sales assistant, not a form
- Soft recommendation is welcome when useful
- No markdown bold with asterisks

KNOWLEDGE USAGE:
- Use only provided company knowledge
- Do not invent information
- Never mix details between different cruises
- If STRUCTURED TOUR FACTS are provided, use them as higher priority

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


def build_whatsapp_link(message: str) -> str:
    encoded = urllib.parse.quote(message)
    return f"{WHATSAPP_LINK}?text={encoded}"


def format_human_date(date_str: str | None) -> str | None:
    if not date_str:
        return None

    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d %B %Y").lstrip("0")
    except ValueError:
        return date_str


def format_period_label(period: str | None) -> str | None:
    if period == "morning":
        return "morning"
    if period == "sunset":
        return "sunset"
    return None


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
    ]

    return any(k in text for k in keywords)


def is_full_day_request(user_message: str) -> bool:
    text = user_message.lower()

    keywords = [
        "full day",
        "full-day",
        "whole day",
        "all day",
        "day trip",
        "full day cruise",
        "full-day cruise",
    ]

    return any(k in text for k in keywords)


def is_large_private_request(
    user_message: str,
    passenger_count: int | None,
    cruise_type_intent: str | None,
) -> bool:
    if not isinstance(passenger_count, int) or passenger_count <= 15:
        return False

    text = user_message.lower()

    private_keywords = [
        "private",
        "just for us",
        "only for us",
        "for our group only",
        "private cruise",
        "private tour",
        "private yacht",
        "private catamaran",
    ]

    return cruise_type_intent == "private" or any(k in text for k in private_keywords)


def build_full_day_whatsapp_reply(
    date_str: str | None = None,
    passenger_count: int | None = None,
) -> str:
    pretty_date = format_human_date(date_str)

    if isinstance(passenger_count, int) and pretty_date:
        prefilled_message = (
            f"Hello, we are {passenger_count} guests and interested in a full-day private cruise on {pretty_date}."
        )
    elif isinstance(passenger_count, int):
        prefilled_message = (
            f"Hello, we are {passenger_count} guests and interested in a full-day private cruise."
        )
    elif pretty_date:
        prefilled_message = (
            f"Hello, we are interested in a full-day private cruise on {pretty_date}."
        )
    else:
        prefilled_message = "Hello, we are interested in a full-day private cruise."

    whatsapp_link = build_whatsapp_link(prefilled_message)

    return (
        "A full-day private cruise is a fantastic choice for a more complete experience around the island.\n\n"
        "These options are not available for direct online booking, as they are tailored to each request.\n\n"
        "Our team will be happy to assist you and suggest the best option for your date.\n\n"
        f"You can contact us directly on WhatsApp here:\n{whatsapp_link}"
    )


def build_large_private_whatsapp_reply(
    passenger_count: int,
    date_str: str | None = None,
    period: str | None = None,
) -> str:
    pretty_date = format_human_date(date_str)
    period_label = format_period_label(period)

    if pretty_date and period_label:
        prefilled_message = (
            f"Hello, we are {passenger_count} guests and interested in a private {period_label} cruise on {pretty_date}."
        )
    elif pretty_date:
        prefilled_message = (
            f"Hello, we are {passenger_count} guests and interested in a private cruise on {pretty_date}."
        )
    else:
        prefilled_message = (
            f"Hello, we are {passenger_count} guests and interested in a private cruise."
        )

    whatsapp_link = build_whatsapp_link(prefilled_message)

    return (
        f"For a group of {passenger_count} guests, we can arrange a private cruise tailored to your needs.\n\n"
        "These options are not available through the standard booking system, as they require custom planning.\n\n"
        "Our team will be happy to assist you with the best available solution.\n\n"
        f"You can contact us directly on WhatsApp here:\n{whatsapp_link}"
    )


def build_cruise_passenger_whatsapp_reply(
    date_str: str | None = None,
    period: str | None = None,
) -> str:
    pretty_date = format_human_date(date_str)
    period_label = format_period_label(period)

    if pretty_date and period_label:
        prefilled_message = (
            f"Hello, we are arriving by cruise ship and would like advice for a {period_label} cruise on {pretty_date}."
        )
    elif pretty_date:
        prefilled_message = (
            f"Hello, we are arriving by cruise ship and would like advice for a cruise on {pretty_date}."
        )
    elif period_label:
        prefilled_message = (
            f"Hello, we are arriving by cruise ship and would like advice for a {period_label} cruise."
        )
    else:
        prefilled_message = (
            "Hello, we are arriving by cruise ship and would like advice for a cruise."
        )

    whatsapp_link = build_whatsapp_link(prefilled_message)

    return (
        "Thank you for your interest!\n\n"
        "Since you are arriving by cruise ship, timing and logistics are very important, and we want to ensure everything is perfectly arranged for you.\n\n"
        "Our team will be happy to guide you and recommend the most suitable option.\n\n"
        f"You can contact us directly on WhatsApp here:\n{whatsapp_link}"
    )


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
        "check my transfer",
        "reconfirm",
        "re-confirm",
        "reconfirm my tour",
        "reconfirm booking",
        "reconfirm reservation",
        "can i reconfirm",
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
        "pregnant",
        "pregnancy",
        "full day",
        "full-day",
    ]

    return any(k in text for k in keywords)


def detect_period(user_message: str) -> str | None:
    text = user_message.lower()

    if "morning" in text or "this morning" in text:
        return "morning"

    if (
        "sunset" in text
        or "this afternoon" in text
        or "this evening" in text
        or "tonight" in text
        or "afternoon" in text
        or "evening" in text
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

        is_private_result_flag = "private" in searchable_text
        is_shared_result_flag = (
            "shared" in searchable_text
            or "semi private" in searchable_text
            or "semi-private" in searchable_text
        )

        if is_private_result_flag:
            private_matches.append(item)
        elif is_shared_result_flag:
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


def build_capacity_reply(data) -> str:
    if not isinstance(data, dict):
        return get_text(
            "availability_fallback",
            DEFAULT_LANGUAGE,
            BOOKING_LINK,
            WHATSAPP_LINK,
        )

    spots = get_capacity_number(data)
    cruise_name = data.get("reply_label", "this cruise")
    booking_url = data.get("booking_url", BOOKING_LINK)
    is_private = is_private_result(data)

    if isinstance(spots, int) and not is_private and spots > 20:
        spots_display = "20+"
    else:
        spots_display = str(spots) if isinstance(spots, int) else None

    if is_private:
        if spots_display == "1":
            return (
                f"The {cruise_name} is available for the requested date.\n\n"
                "It can accommodate up to 1 guest.\n\n"
                f"You can proceed with your booking here:\n{booking_url}\n\n"
                "Please select the date on the booking page."
            )

        if spots_display:
            return (
                f"The {cruise_name} is available for the requested date.\n\n"
                f"It can accommodate up to {spots_display} guests.\n\n"
                f"You can proceed with your booking here:\n{booking_url}\n\n"
                "Please select the date on the booking page."
            )

        return (
            f"The {cruise_name} is available for the requested date.\n\n"
            f"You can proceed with your booking here:\n{booking_url}\n\n"
            "Please select the date on the booking page."
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


def build_multi_capacity_reply(results: list[dict]) -> str:
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
    history: list[dict], passenger_count: int | None = None
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


def normalize_to_base_tour_key(tour_key: str | None) -> str | None:
    if not tour_key:
        return None

    if tour_key in BASE_TOUR_KEYS:
        return tour_key

    for suffix in ("_morning", "_sunset"):
        if tour_key.endswith(suffix):
            candidate = tour_key[: -len(suffix)]
            if candidate in BASE_TOUR_KEYS:
                return candidate

    return tour_key


def get_locked_followup_context(history: list[dict]) -> tuple[str | None, str | None]:
    """
    For short follow-up availability questions like:
    'and for the morning?'
    lock to the MOST RECENT relevant user availability context,
    instead of allowing an older date from history to leak in.
    """
    for item in reversed(history):
        if item.get("role") != "user":
            continue

        content = (item.get("content") or "").strip()
        if not content:
            continue

        hist_tour = detect_tour_key(content)
        hist_date = detect_date(content)
        hist_period = detect_period(content)

        if hist_tour or hist_date or hist_period or is_availability_request(content):
            return hist_tour, hist_date

    return None, None


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

    return (
        f"For {pretty_date}, the following options are available:\n\n"
        f"- {morning_label}\n"
        f"- {sunset_label}\n\n"
        f"You can proceed with your booking here:\n{booking_url}\n\n"
        "Please select the date on the booking page."
    )


@app.get("/")
def root(request: Request):
    host = request.headers.get("host", "").lower()

    if host.startswith("pricelist."):
        return FileResponse("app/static/availability-pricing.html")

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
    language = DEFAULT_LANGUAGE
    session_id = request.session_id

    current_state = get_session_state(session_id)

    tour_key = detect_tour_key(user_message)
    date_str = detect_date(user_message)
    period = detect_period(user_message)
    tour_facts = build_tour_facts_block(tour_key) if tour_key else ""
    passenger_count = detect_passenger_count(user_message, history)
    cruise_type_intent = detect_cruise_type_intent(user_message, history)

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
        clear_session_state(session_id)
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
        clear_session_state(session_id)
        reply = build_cruise_passenger_whatsapp_reply(
            date_str=date_str,
            period=period,
        )
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=None,
            session_id=session_id,
        )

    if is_full_day_request(user_message):
        clear_session_state(session_id)
        reply = build_full_day_whatsapp_reply(
            date_str=date_str,
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

    if is_large_private_request(user_message, passenger_count, cruise_type_intent):
        clear_session_state(session_id)
        reply = build_large_private_whatsapp_reply(
            passenger_count=passenger_count,
            date_str=date_str,
            period=period,
        )
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=tour_key,
            session_id=session_id,
        )

    if is_contact_request(user_message):
        clear_session_state(session_id)
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
        clear_session_state(session_id)
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
        clear_session_state(session_id)
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
        clear_session_state(session_id)
        conversation_history = build_conversation_history(history)
        knowledge = get_company_knowledge()

        prompt = f"""
You are the Sunset Oia digital assistant.

IMPORTANT LANGUAGE RULE:
- Always reply in English.

TONE:
- Warm, natural, human
- Friendly and professional
- Keep replies short (3–5 lines)
- Avoid repeating phrases like “Great choice” or “Great news”

CORE BEHAVIOR:
- Always assume the user refers to the cruise experience
- Never reject a question if it can relate to the cruise
- Do not invent information
- If unsure, give a safe, general answer

CRITICAL RULE (VERY IMPORTANT):
If the user asks about comparison, value, experience, or recommendation
(e.g. “which is better”, “difference”, “worth it”, “which should I choose”):

→ You MUST answer the question directly
→ DO NOT mention booking
→ DO NOT mention availability
→ DO NOT redirect to WhatsApp

CONTEXT RULE:
- Answer ONLY based on the cruises mentioned in the question
- NEVER introduce other cruises unless the user asks
- Example:
  If user asks “Ferretti 55 vs 731” → ONLY talk about these two
  DO NOT mention Red, Diamond, Gems, etc.

CONVERSATION STYLE:
- Be clear and direct
- Do not over-explain
- Do not add unnecessary suggestions
- Avoid ending every reply with “If you'd like, I can help...”

SALES APPROACH:
- Guide naturally, not aggressively
- Suggest only when relevant
- Booking link only when useful (NOT in comparison questions)

KNOWLEDGE USAGE:
- Use only provided company knowledge
- Do not mix details between different cruises
- For private cruises:
  → NEVER mention “spots available”
  → ALWAYS describe capacity

WHEN INFORMATION IS UNKNOWN:
Say:
“I don't have that exact detail here, but I'll be happy to check it for you.

You can also reach our team directly on WhatsApp:
{WHATSAPP_LINK}”

PERSONAL BOOKINGS:
“I can't see personal booking details here. Please check your booking confirmation, or contact us on WhatsApp:
{WHATSAPP_LINK}”

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
        clear_session_state(session_id)
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
                reply_text = build_multi_capacity_reply(capacity_filtered)
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
        clear_session_state(session_id)
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
                reply_text = build_capacity_reply(data)
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

    # --------------------------------------------------
    # New flow layer
    # --------------------------------------------------
    routing_decision = route_message(user_message, current_state)
    routing_action = routing_decision.get("action")

    # --------------------------------------------------
    # FORCE availability if user explicitly asks for it
    # (even after comparison flow)
    # --------------------------------------------------
    if is_availability_request(user_message):
        routing_action = "availability_ready"
        routing_decision["action"] = "availability_ready"

    if routing_action == "clarify":
        save_session_state(
            session_id,
            routing_decision.get("state", create_empty_state()),
        )
        reply = (
            routing_decision.get("reply")
            or "Could you share a little more detail so I can help you properly?"
        )
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=routing_decision.get("tour"),
            session_id=session_id,
        )

    if routing_action == "booking_guidance":
        clear_session_state(session_id)
        reply = routing_decision.get("reply") or (
            "I’ll be happy to help. Just let me know your preferred date and cruise, and I’ll guide you with the next step."
        )
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=routing_decision.get("tour"),
            session_id=session_id,
        )

    if routing_action in {
        "comparison_answer",
        "recommendation_answer",
        "continue_comparison",
    }:
        save_session_state(
            session_id,
            routing_decision.get("state", create_empty_state()),
        )
        conversation_history = build_conversation_history(history)
        knowledge = get_company_knowledge()

        prompt = build_comparison_recommendation_prompt(
            user_message=user_message,
            conversation_history=conversation_history,
            knowledge=knowledge,
            tour_facts=tour_facts,
        )

        try:
            reply = get_ai_reply(prompt)
            return log_and_return(
                user_message=user_message,
                reply=reply,
                language=language,
                fallback=False,
                detected_tour=tour_key,
                session_id=session_id,
            )
        except Exception as e:
            print("OPENAI ERROR:", e)

    forced_availability_flow = routing_action in {
        "availability_ready",
        "continue_pending",
    } or is_availability_request(user_message)

    if forced_availability_flow:
        clear_session_state(session_id)

        routed_tour = routing_decision.get("tour")
        routed_date = routing_decision.get("date")
        routed_time = routing_decision.get("time")

        if routed_tour:
            tour_key = routed_tour
        if routed_date:
            date_str = routed_date
        if routed_time:
            period = routed_time

        tour_facts = build_tour_facts_block(tour_key) if tour_key else ""

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
        clear_session_state(session_id)
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
        clear_session_state(session_id)
        reply = build_sunset_reassurance_reply()
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=tour_key,
            session_id=session_id,
        )

    if is_sunset_question(user_message):
        clear_session_state(session_id)
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
        clear_session_state(session_id)
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
        forced_availability_flow
        or (
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
    )

    if availability_intent and tour_key and not date_str:
        reply = build_date_clarification_reply()
        save_session_state(
            session_id,
            {
                "pending_action": "availability",
                "pending_tour": tour_key,
                "pending_date": None,
                "pending_time": period,
                "comparison_candidates": [],
            },
        )
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=tour_key,
            session_id=session_id,
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
        clear_session_state(session_id)
        return log_and_return(
            user_message=user_message,
            reply=seasonal_reply,
            language=language,
            fallback=False,
            detected_tour=tour_key,
            session_id=session_id,
        )

    if is_base_tour_key(tour_key) and date_str:
        clear_session_state(session_id)
        morning_key = f"{tour_key}_morning"
        sunset_key = f"{tour_key}_sunset"

        morning_data = safe_check_tour_availability(morning_key, date_str)
        sunset_data = safe_check_tour_availability(sunset_key, date_str)

        dual_period_reply = build_dual_period_reply(
            morning_data=morning_data,
            sunset_data=sunset_data,
            date_str=date_str,
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
            if morning_data and isinstance(morning_data, dict):
                morning_data["requested_group_size"] = passenger_count
                morning_data["general_booking_url"] = BOOKING_LINK

            reply_text = build_availability_reply(morning_data)
            return log_and_return(
                user_message=user_message,
                reply=reply_text,
                language=language,
                fallback=False,
                detected_tour=morning_key,
                session_id=session_id,
            )

        if is_available_result(sunset_data):
            if sunset_data and isinstance(sunset_data, dict):
                sunset_data["requested_group_size"] = passenger_count
                sunset_data["general_booking_url"] = BOOKING_LINK

            reply_text = build_availability_reply(sunset_data)
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
        clear_session_state(session_id)
        data = safe_check_tour_availability(tour_key, date_str)

        is_available = is_available_result(data)

        if is_available:
            alternative_results = safe_find_available_tours(
                date_str,
                period,
                user_message,
                passenger_count,
                ignore_requested_tours=True,
            )

            capacity_filtered = filter_by_capacity(
                alternative_results or [],
                passenger_count,
            )

            prepared_alternatives = prepare_alternative_results(
                results=capacity_filtered,
                requested_tour_key=tour_key,
                passenger_count=passenger_count,
            )

            if data and isinstance(data, dict):
                data["requested_group_size"] = passenger_count
                data["general_booking_url"] = BOOKING_LINK
                data["alternative_tours"] = prepared_alternatives

            reply_text = build_availability_reply(data)
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
                "general_booking_url": BOOKING_LINK,
            }
            print("FALLBACK DATA:", fallback_data)

            reply_text = build_availability_reply(fallback_data)
            print("FINAL FALLBACK REPLY:", reply_text)

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

    if date_str and not tour_key:
        last_tour_key, _ = get_last_tour_and_date_from_history(user_message, history)

        if last_tour_key:
            clear_session_state(session_id)
            if is_base_tour_key(last_tour_key):
                morning_key = f"{last_tour_key}_morning"
                sunset_key = f"{last_tour_key}_sunset"

                morning_data = safe_check_tour_availability(morning_key, date_str)
                sunset_data = safe_check_tour_availability(sunset_key, date_str)

                dual_period_reply = build_dual_period_reply(
                    morning_data=morning_data,
                    sunset_data=sunset_data,
                    date_str=date_str,
                )

                if dual_period_reply:
                    return log_and_return(
                        user_message=user_message,
                        reply=dual_period_reply,
                        language=language,
                        fallback=False,
                        detected_tour=last_tour_key,
                        session_id=session_id,
                    )

                if is_available_result(morning_data):
                    if morning_data and isinstance(morning_data, dict):
                        morning_data["requested_group_size"] = passenger_count
                        morning_data["general_booking_url"] = BOOKING_LINK

                    reply_text = build_availability_reply(morning_data)
                    return log_and_return(
                        user_message=user_message,
                        reply=reply_text,
                        language=language,
                        fallback=False,
                        detected_tour=morning_key,
                        session_id=session_id,
                    )

                if is_available_result(sunset_data):
                    if sunset_data and isinstance(sunset_data, dict):
                        sunset_data["requested_group_size"] = passenger_count
                        sunset_data["general_booking_url"] = BOOKING_LINK

                    reply_text = build_availability_reply(sunset_data)
                    return log_and_return(
                        user_message=user_message,
                        reply=reply_text,
                        language=language,
                        fallback=False,
                        detected_tour=sunset_key,
                        session_id=session_id,
                    )

            else:
                data = safe_check_tour_availability(last_tour_key, date_str)

                if is_available_result(data):
                    if data and isinstance(data, dict):
                        data["requested_group_size"] = passenger_count
                        data["general_booking_url"] = BOOKING_LINK

                    return log_and_return(
                        user_message=user_message,
                        reply=build_availability_reply(data),
                        language=language,
                        fallback=False,
                        detected_tour=last_tour_key,
                        session_id=session_id,
                    )

    if date_str or availability_intent:
        clear_session_state(session_id)
        locked_tour_key = None
        locked_date = None

        if is_followup(user_message) and not date_str:
            locked_tour_key, locked_date = get_locked_followup_context(history)

        effective_tour_key, effective_date = get_last_tour_and_date_from_history(
            user_message,
            history,
        )

        if locked_tour_key:
            effective_tour_key = locked_tour_key

        if locked_date:
            effective_date = locked_date

        if not effective_tour_key:
            effective_tour_key = tour_key

        if not effective_date:
            effective_date = get_effective_date(user_message, history)

        base_effective_tour_key = normalize_to_base_tour_key(effective_tour_key)

        seasonal_reply = get_seasonal_reply(
            date_str=effective_date,
            language=language,
            booking_link=BOOKING_LINK,
            whatsapp_link=WHATSAPP_LINK,
            tour_key=base_effective_tour_key,
            period=period,
            generic_availability=True,
        )
        if seasonal_reply:
            return log_and_return(
                user_message=user_message,
                reply=seasonal_reply,
                language=language,
                fallback=False,
                detected_tour=base_effective_tour_key,
                session_id=session_id,
            )

        if base_effective_tour_key and effective_date and period:
            specific_tour_key = f"{base_effective_tour_key}_{period}"
            data = safe_check_tour_availability(specific_tour_key, effective_date)

            if is_available_result(data):
                alternative_results = safe_find_available_tours(
                    effective_date,
                    period,
                    user_message,
                    passenger_count,
                    ignore_requested_tours=True,
                )

                capacity_filtered = filter_by_capacity(
                    alternative_results or [],
                    passenger_count,
                )

                prepared_alternatives = prepare_alternative_results(
                    results=capacity_filtered,
                    requested_tour_key=specific_tour_key,
                    passenger_count=passenger_count,
                )

                if data and isinstance(data, dict):
                    data["requested_group_size"] = passenger_count
                    data["general_booking_url"] = BOOKING_LINK
                    data["alternative_tours"] = prepared_alternatives

                reply_text = build_availability_reply(data)
                return log_and_return(
                    user_message=user_message,
                    reply=reply_text,
                    language=language,
                    fallback=False,
                    detected_tour=specific_tour_key,
                    session_id=session_id,
                )

            alternative_results = safe_find_available_tours(
                effective_date,
                period,
                user_message,
                passenger_count,
                ignore_requested_tours=True,
            )
            print("FOLLOW-UP RAW ALTERNATIVE RESULTS:", alternative_results)

            capacity_filtered = filter_by_capacity(
                alternative_results or [],
                passenger_count,
            )
            print("FOLLOW-UP CAPACITY FILTERED RESULTS:", capacity_filtered)

            prepared_alternatives = prepare_alternative_results(
                results=capacity_filtered,
                requested_tour_key=specific_tour_key,
                passenger_count=passenger_count,
            )
            print("FOLLOW-UP PREPARED ALTERNATIVES:", prepared_alternatives)

            alternative_reply = build_unavailable_alternatives_reply(
                requested_tour_key=specific_tour_key,
                alternatives=prepared_alternatives,
                language=language,
                booking_link=BOOKING_LINK,
            )
            print("FOLLOW-UP ALTERNATIVE REPLY:", alternative_reply)

            if alternative_reply:
                return log_and_return(
                    user_message=user_message,
                    reply=alternative_reply,
                    language=language,
                    fallback=False,
                    detected_tour=specific_tour_key,
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
                detected_tour=base_effective_tour_key,
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
            return log_and_return(
                user_message=user_message,
                reply=reply_text,
                language=language,
                fallback=False,
                detected_tour=base_effective_tour_key,
                session_id=session_id,
            )

        reply = get_text("availability_fallback", language, BOOKING_LINK, WHATSAPP_LINK)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=True,
            detected_tour=base_effective_tour_key,
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
        clear_session_state(session_id)
        mentions_red = "red" in recent_text
        mentions_diamond = "diamond" in recent_text
        mentions_gems = "gems" in recent_text

        if mentions_red and mentions_diamond and not mentions_gems:
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
        clear_session_state(session_id)
        reply = build_best_choice_reply(
            history=history,
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
        clear_session_state(session_id)
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
        clear_session_state(session_id)
        reply = get_text("irrelevant_reply", language, BOOKING_LINK, WHATSAPP_LINK)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=tour_key,
            session_id=session_id,
        )

    conversation_history = build_conversation_history(history)
    knowledge = get_company_knowledge()

    prompt = f"""
You are the Sunset Oia digital assistant.

IMPORTANT LANGUAGE RULE:
- Always reply in English.

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

    clear_session_state(session_id)
    reply = get_ai_reply(prompt)
    return log_and_return(
        user_message=user_message,
        reply=reply,
        language=language,
        fallback=False,
        detected_tour=tour_key,
        session_id=session_id,
    )