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
        "cheaper", "deal",
        "εκπτωση", "έκπτωση", "καλύτερη τιμή",
        "sconto", "offerta"
    ]

    return any(k in text for k in keywords)


def is_cruise_passenger(user_message: str) -> bool:
    text = user_message.lower()

    keywords = [
        "cruise ship", "cruise passenger", "ship",
        "old port", "tender", "cable car",
        "from the ship", "coming by cruise",
        "port of fira", "fira port",

        "κρουαζιερόπλοιο", "παλιό λιμάνι", "τελεφερίκ",

        "crociera", "nave", "porto vecchio"
    ]

    return any(k in text for k in keywords)


def is_relevant(user_message: str) -> bool:
    text = user_message.lower()

    keywords = [
        "cruise", "cruises", "tour", "tours", "santorini",
        "price", "availability", "available",
        "private", "shared",
        "sunset", "morning",
        "pickup", "port", "catamaran",
        "booking", "book", "reservation",
        "cancel", "refund", "weather",
        "food", "drinks", "drink", "menu", "meal",
        "vegetarian", "vegan", "halal", "kosher",
        "dietary", "allergy", "allergies",
        "gluten", "gluten free", "gluten-free",
        "celiac", "coeliac",
        "transfer", "hotel", "itinerary",
        "red beach", "white beach", "hot springs",
        "pets", "kids", "group", "guests",

        "people", "persons", "person",
        "we are", "we have",
        "recommend", "suggest", "suggestion",
        "what do you recommend", "what do you suggest",

        "difference", "compare", "comparison",
        "which one", "which is better", "better", "vs", "or",

        "red", "diamond", "gems", "platinum",
        "lagoon", "emily", "ferretti",

        "κρουαζιέρα", "κρουαζιερες", "τιμή", "διαθεσιμότητα",
        "ιδιωτική", "ηλιοβασίλεμα", "πρωινή", "λιμάνι", "μεταφορά",
        "φαγητό", "ποτό", "ποτά", "μενού",
        "χορτοφαγ", "βίγκαν", "χαλάλ", "αλλεργ",
        "γλουτένη", "χωρίς γλουτένη", "κοιλιοκάκη",
        "άτομα", "άτομο", "είμαστε", "έχουμε",
        "προτείνεις", "προτείνετε", "σύσταση",
        "διαφορά", "σύγκριση",

        "crociera", "crociere", "prezzo", "disponibilità",
        "privata", "tramonto", "mattina",
        "cibo", "bevande", "menu",
        "vegetariano", "vegano", "halal",
        "allergie", "glutine", "senza glutine",
        "persone", "persona", "siamo", "abbiamo",
        "consigli", "raccomandi", "suggerisci",
        "differenza", "confronto"
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


def detect_cruise_type_intent(user_message: str, history: list[dict] | None = None) -> str | None:
    text = user_message.lower()

    private_keywords = [
        "private", "privately", "just for us", "only for us", "for our group only",
        "ιδιωτική", "ιδιωτικη", "μόνο για εμάς", "μονο για εμας",
        "privata", "solo per noi"
    ]

    shared_keywords = [
        "shared", "semi private", "semi-private", "join", "group cruise",
        "κοινή", "κοινη",
        "condivisa", "di gruppo"
    ]

    has_private = any(k in text for k in private_keywords)
    has_shared = any(k in text for k in shared_keywords)

    if has_private and not has_shared:
        return "private"

    if has_shared and not has_private:
        return "shared"

    if history:
        for item in reversed(history[-6:]):
            if item.get("role") != "user":
                continue

            previous_text = item.get("content", "").lower()

            prev_has_private = any(k in previous_text for k in private_keywords)
            prev_has_shared = any(k in previous_text for k in shared_keywords)

            if prev_has_private and not prev_has_shared:
                return "private"

            if prev_has_shared and not prev_has_private:
                return "shared"

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
            "category"
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


@app.get("/")
def root():
    return {"message": "Santorini bot is running"}


@app.post("/chat")
def chat(request: ChatRequest):
    user_message = request.message.strip()
    history = request.history or []

    if not user_message:
        return {
            "reply": "Hello! I’ll be happy to help you with our cruises in Santorini."
        }

    if is_discount_request(user_message):
        return {
            "reply": f"For special rate requests, please contact us via WhatsApp: {WHATSAPP_LINK}"
        }

    if is_cruise_passenger(user_message):
        return {
            "reply": f"For cruise ship guests, we kindly recommend contacting us directly via WhatsApp so we can assist you based on your ship schedule:\n{WHATSAPP_LINK}"
        }

    tour_key = detect_tour_key(user_message)
    date_str = detect_date(user_message)
    period = detect_period(user_message)
    cruise_type_intent = detect_cruise_type_intent(user_message, history)

    if tour_key and date_str:
        data = check_tour_availability(tour_key, date_str)
        return {"reply": build_availability_reply(data)}

    if date_str:
        results = find_available_tours(date_str, period, user_message)
        filtered_results = filter_results_by_cruise_type(results, cruise_type_intent)
        return {
            "reply": build_multi_availability_reply(
                filtered_results,
                date_str,
                period
            )
        }

    if is_greeting(user_message):
        return {
            "reply": "Hello and welcome! I’ll be happy to help you with our cruises in Santorini. Feel free to ask me about availability, prices, shared or private options."
        }

    if not is_relevant(user_message) and not is_followup(user_message):
        return {
            "reply": "I can assist only with questions related to our cruises in Santorini."
        }

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

Your tone:
- Warm, natural and human — never robotic
- Friendly and professional
- Avoid repeating the same phrases in every reply
- Keep replies short (3–5 lines), but helpful

Conversation style:
- Vary your phrasing (do not always say "If you'd like")
- Sound like a real person, not a script
- Adapt naturally to the user's question

Sales approach:
- Gently guide the user, do not push
- Suggest options based on their needs (group size, budget, experience)
- Only include the booking link when it is useful and relevant
- When appropriate, make soft recommendations (e.g. “Diamond is a great choice if you prefer fewer guests”)

Knowledge:
- Use only the company knowledge provided
- Do not invent information
- If something is not available (e.g. halal), say it clearly and suggest alternatives

Special handling:
- Cruise ship guests should be directed to WhatsApp
- Dietary questions should be answered clearly and confidently

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