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

print("MAIN WITH MULTILINGUAL KNOWLEDGE + SINGLE & MULTI AVAILABILITY LOADED")


class ChatRequest(BaseModel):
    message: str


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


def is_relevant(user_message: str) -> bool:
    text = user_message.lower()

    keywords = [
        "cruise", "cruises", "santorini", "price", "prices", "rate", "rates",
        "availability", "available", "private", "shared", "sunset", "morning",
        "pickup", "pick-up", "port", "ports", "catamaran", "booking", "book",
        "reservation", "reserve", "cancellation", "cancel", "refund", "weather",
        "food", "drinks", "bbq", "transfer", "meeting point", "hotel", "itinerary",
        "red beach", "white beach", "hot springs", "pet", "pets", "dog", "cat",
        "animal", "animals", "on board", "aboard", "children", "child", "kids",
        "group", "capacity", "people", "guests",

        "κρουαζιέρα", "κρουαζιερα", "κρουαζιέρες", "κρουαζιερες",
        "σαντορίνη", "σαντορινη",
        "τιμή", "τιμη", "τιμές", "τιμες", "κόστος", "κοστος", "κοστίζει", "κοστιζει",
        "διαθεσιμότητα", "διαθεσιμοτητα", "διαθέσιμο", "διαθεσιμο", "διαθέσιμη", "διαθεσιμη",
        "ιδιωτική", "ιδιωτικη", "ιδιωτικό", "ιδιωτικο",
        "κοινή", "κοινη", "ομαδική", "ομαδικη",
        "ηλιοβασίλεμα", "ηλιοβασιλεμα", "πρωινή", "πρωινη",
        "παραλαβή", "παραλαβη", "μεταφορά", "μεταφορα",
        "λιμάνι", "λιμανι", "λιμάνια", "λιμανια",
        "καταμαράν", "καταμαραν",
        "κράτηση", "κρατηση", "κλείσω", "κλεισω", "κλείσιμο", "κλεισιμο",
        "ακύρωση", "ακυρωση", "ακυρώσω", "ακυρωσω",
        "επιστροφή", "επιστροφη", "refund",
        "καιρός", "καιρος",
        "φαγητό", "φαγητο", "ποτά", "ποτα",
        "ξενοδοχείο", "ξενοδοχειο",
        "δρομολόγιο", "δρομολογιο", "στάσεις", "στασεις",
        "κόκκινη παραλία", "κοκκινη παραλια",
        "λευκή παραλία", "λευκη παραλια",
        "θερμές πηγές", "θερμες πηγες",
        "κατοικίδιο", "κατοικιδιο", "κατοικίδια", "κατοικιδια",
        "σκύλος", "σκυλος", "γάτα", "γατα",
        "παιδί", "παιδι", "παιδιά", "παιδια",
        "ομάδα", "ομαδα", "γκρουπ",
        "άτομα", "ατομα", "επισκέπτες", "επισκεπτες",

        "crociera", "crociere", "santorini",
        "prezzo", "prezzi", "costo", "costi", "quanto costa",
        "disponibilità", "disponibilita", "disponibile",
        "privata", "privato", "condivisa", "condiviso",
        "tramonto", "mattina",
        "pick up", "pickup", "trasferimento", "transfer",
        "porto", "porti",
        "catamarano",
        "prenotazione", "prenotare", "prenoto",
        "cancellazione", "cancellare", "rimborso",
        "meteo", "tempo",
        "cibo", "bevande", "bbq",
        "hotel", "itinerario",
        "red beach", "white beach", "hot springs",
        "animale", "animali", "cane", "gatto",
        "bambino", "bambini", "ragazzi",
        "gruppo", "persone", "ospiti", "capacità", "capacita"
    ]

    return any(keyword in text for keyword in keywords)


def detect_period(user_message: str) -> str | None:
    text = user_message.lower()

    if "morning" in text or "πρωιν" in text or "mattina" in text:
        return "morning"

    if "sunset" in text or "afternoon" in text or "ηλιοβασ" in text or "tramonto" in text:
        return "sunset"

    return None


@app.get("/")
def root():
    return {"message": "Santorini bot is running"}


@app.get("/test-availability")
def test_availability():
    data = check_tour_availability("red_morning", "2026-04-06")
    reply = build_availability_reply(data)
    return {"reply": reply}


@app.post("/chat")
def chat(request: ChatRequest):
    user_message = request.message.strip()

    if not user_message:
        return {
            "reply": (
                f"Hello! I will be happy to help you with our cruises in Santorini. "
                f"You may check availability and book here: {BOOKING_LINK}"
            )
        }

    # 1. Single tour live availability
    tour_key = detect_tour_key(user_message)
    date_str = detect_date(user_message)

    if tour_key and date_str:
        data = check_tour_availability(tour_key, date_str)
        reply = build_availability_reply(data)
        return {"reply": reply}

    # 2. Multi-tour live availability
    period = detect_period(user_message)

    if not tour_key and date_str and period:
        results = find_available_tours(date_str, period)
        date_label = date_str
        reply = build_multi_availability_reply(results, date_label, period)
        return {"reply": reply}

    # 3. Greeting handling
    if is_greeting(user_message):
        prompt = f"""
You are the Sunset Oia digital assistant.

Reply in the same language as the user.
If the user writes in Greek, reply in Greek.
If the user writes in Italian, reply in Italian.
If the user writes in English, reply in English.
Keep the answer short, warm and welcoming.

User message:
{user_message}

Base message to adapt to the user's language:
Hello and welcome!

I’ll be happy to help you with anything related to our cruises in Santorini.

You may book directly here: {BOOKING_LINK}
Or, if you prefer, I can help you choose between a private or a shared cruise.
"""
        reply = get_ai_reply(prompt)
        return {"reply": reply}

    # 4. Off-topic handling
    if not is_relevant(user_message):
        prompt = f"""
You are the Sunset Oia digital assistant.

Reply in the same language as the user.
If the user writes in Greek, reply in Greek.
If the user writes in Italian, reply in Italian.
If the user writes in English, reply in English.
Keep the answer short, polite and professional.

User message:
{user_message}

Base message to adapt to the user's language:
I am the Sunset Oia digital assistant and I can assist only with questions related to our cruises in Santorini, such as availability, private or shared options, departure points, inclusions and cancellation policy.

I would be happy to help you find the ideal cruise for your stay.
"""
        reply = get_ai_reply(prompt)
        return {"reply": reply}

    # 5. Load company knowledge
    knowledge = get_company_knowledge()
    print("KNOWLEDGE LENGTH:", len(knowledge))

    # 6. Build grounded prompt
    prompt = f"""
You are the Sunset Oia digital assistant.

Follow these rules:

- Be warm, polite and professional.
- Keep answers short, usually 3 to 5 lines.
- Do not invent information.
- Use only the company knowledge provided below.
- The company knowledge is written as Q&A pairs.
- Reply in the same language as the user message.
- If the user writes in Greek, reply in Greek.
- If the user writes in Italian, reply in Italian.
- If the user writes in English, reply in English.
- If the user mixes languages, reply in the main language of the message.
- Do not give exact prices unless they are clearly provided in the company knowledge.
- Do not confirm exact availability unless it has been verified by the booking system or the team.
- Minor spelling mistakes from the user should not make you reject a relevant cruise question.
- Questions about pets or animals on board are relevant to the cruise policy.
- If the guest wants to book or check live availability, guide them primarily to this booking link:

{BOOKING_LINK}

- If useful, tell the guest to select the date at the booking page.
- You may also mention the website when appropriate:

{WEBSITE_LINK}

- If the question cannot be answered with certainty based on the provided company knowledge, say politely that you would not like to provide inaccurate information and direct the guest to WhatsApp:

{WHATSAPP_LINK}

- Do not answer unrelated questions such as sports, politics, coding, or general knowledge.
- If the guest asks something outside Sunset Oia cruises in Santorini, politely explain that you can assist only with cruise-related questions.
- Keep the tone natural and helpful.

COMPANY KNOWLEDGE (Q&A):

{knowledge}

USER QUESTION:

{user_message}
"""

    reply = get_ai_reply(prompt)
    return {"reply": reply}