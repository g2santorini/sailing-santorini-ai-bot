from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.openai_service import get_ai_reply
from app.services.knowledge_service import get_company_knowledge
from app.services.availability_lookup import check_tour_availability
from app.services.reply_builder import build_availability_reply
from app.services.tour_detector import detect_tour_key
from app.services.date_detector import detect_date
from app.services.availability_search import find_available_tours
from app.services.multi_reply_builder import build_multi_availability_reply

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("MAIN WITH HISTORY + MULTILINGUAL KNOWLEDGE LOADED")


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


BOOKING_LINK = "https://sailingsantorini.link-twist.com/"
WEBSITE_LINK = "https://sailing-santorini.com/"
WHATSAPP_LINK = "https://wa.me/306972805193"


def is_greeting(user_message: str) -> bool:
    text = user_message.lower().strip()

    greetings = {
        "hi", "hello", "hey",
        "good morning", "good afternoon", "good evening",
        "hi there", "hello there",
        "γεια", "γειά", "γεια σου", "γειά σου", "γεια σας", "γειά σας",
        "καλημέρα", "καλησπέρα", "καλησπερα", "καληνύχτα", "καληνυχτα",
        "χαίρετε", "χαιρετε",
        "ciao", "salve", "buongiorno", "buonasera"
    }

    return text in greetings


def is_discount_request(user_message: str) -> bool:
    text = user_message.lower()

    keywords = [
        "discount", "better price", "best price", "special price",
        "offer", "cheaper", "deal",
        "εκπτωση", "έκπτωση", "καλύτερη τιμή",
        "sconto", "offerta"
    ]

    return any(k in text for k in keywords)


def is_relevant(user_message: str) -> bool:
    text = user_message.lower()

    keywords = [
        "cruise", "santorini", "price", "availability", "private", "shared",
        "sunset", "morning", "pickup", "port", "catamaran", "booking",
        "reservation", "cancel", "refund", "weather", "food", "drinks",
        "transfer", "hotel", "itinerary", "red beach", "white beach",
        "hot springs", "pets", "kids", "group", "guests",

        "κρουαζιέρα", "τιμή", "διαθεσιμότητα", "ιδιωτική",
        "ηλιοβασίλεμα", "πρωινή", "λιμάνι", "μεταφορά",

        "crociera", "prezzo", "disponibilità", "privata",
        "tramonto", "mattina"
    ]

    return any(k in text for k in keywords)


def is_followup(user_message: str) -> bool:
    text = user_message.lower().strip()

    followups = {
        "yes", "yes please", "ok", "okay", "sure", "please",
        "tell me more", "go ahead", "continue",
        "ναι", "οκ", "εντάξει", "συνέχισε",
        "si", "va bene", "continua"
    }

    return text in followups


def detect_period(user_message: str) -> str | None:
    text = user_message.lower()

    if "morning" in text or "πρωιν" in text or "mattina" in text:
        return "morning"

    if "sunset" in text or "ηλιοβασ" in text or "tramonto" in text:
        return "sunset"

    return None


@app.get("/")
def root():
    return {"message": "Santorini bot is running"}


@app.post("/chat")
def chat(request: ChatRequest):
    user_message = request.message.strip()
    history = request.history or []

    if not user_message:
        return {
            "reply": f"Hello! You may book directly here: {BOOKING_LINK}"
        }

    # Discount handling
    if is_discount_request(user_message):
        return {
            "reply": f"For special rate requests, please contact us via WhatsApp: {WHATSAPP_LINK}"
        }

    # Detect structured queries
    tour_key = detect_tour_key(user_message)
    date_str = detect_date(user_message)
    period = detect_period(user_message)

    if tour_key and date_str:
        data = check_tour_availability(tour_key, date_str)
        return {"reply": build_availability_reply(data)}

    if date_str:
        results = find_available_tours(date_str, period)
        return {"reply": build_multi_availability_reply(results, date_str, period)}

    # Greeting
    if is_greeting(user_message):
        return {
            "reply": f"Hello and welcome! I’ll be happy to help you with our cruises in Santorini. You may book here: {BOOKING_LINK}"
        }

    # Off-topic
    if not is_relevant(user_message) and not is_followup(user_message):
        return {
            "reply": "I can assist only with questions related to our cruises in Santorini."
        }

    # Build conversation history
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

Follow these rules:
- Be warm, professional and short (3–5 lines).
- Use only the company knowledge.
- Use conversation history when needed.
- If user says "yes", treat it as continuation.
- Suggest the best cruise based on user needs.

BOOKING LINK:
{BOOKING_LINK}

COMPANY KNOWLEDGE:
{knowledge}

CONVERSATION HISTORY:
{conversation_history}

USER MESSAGE:
{user_message}
"""

    reply = get_ai_reply(prompt)
    return {"reply": reply}