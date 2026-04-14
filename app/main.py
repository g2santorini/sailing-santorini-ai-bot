from datetime import date, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ✅ NEW IMPORT
from app.routes.availability_routes import router as availability_router

from app.services.openai_service import get_ai_reply
from app.services.knowledge_service import get_company_knowledge
from app.services.availability_lookup import check_tour_availability
from app.services.reply_builder import build_availability_reply
from app.services.tour_detector import detect_tour_key
from app.services.date_detector import detect_date
from app.services.availability_search import find_available_tours
from app.services.multi_reply_builder import build_multi_availability_reply
from app.services.tour_mapping import build_tour_facts_block
from app.services.chat_logger import init_db, save_chat_log, get_chat_logs
from app.services.intent_service import (
    is_greeting,
    is_discount_request,
    is_contact_request,
    is_availability_request,
    is_followup,
    is_best_choice_question,
    is_capacity_request,
    is_multi_capacity_request,
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

# ✅ NEW LINE
app.include_router(availability_router)
init_db()

print("MAIN WITH HISTORY + MULTILINGUAL KNOWLEDGE + SMARTER WHATSAPP LOADED")


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


BOOKING_LINK = "https://sailingsantorini.link-twist.com/"
WEBSITE_LINK = "https://sailing-santorini.com/"
WHATSAPP_LINK = "https://wa.me/306972805193"


def log_and_return(
    user_message: str,
    reply: str,
    language: str,
    fallback: bool = False,
    detected_tour: str | None = None,
):
    try:
        save_chat_log(
            user_message=user_message,
            bot_reply=reply,
            fallback=fallback,
            detected_tour=detected_tour,
            language=language,
        )
    except Exception as exc:
        print(f"Chat log save error: {exc}")

    return {"reply": reply}


def detect_language(user_message: str) -> str:
    text = user_message.lower()

    greek_chars = any(("α" <= c <= "ω") or ("ά" <= c <= "ώ") for c in text)
    if greek_chars:
        return "el"

    italian_keywords = [
        "ciao",
        "salve",
        "buongiorno",
        "buonasera",
        "grazie",
        "disponibilità",
        "disponibile",
        "privata",
        "tramonto",
        "mattina",
        "persone",
        "crociera",
        "crociere",
        "oggi",
        "domani",
    ]
    if any(word in text for word in italian_keywords):
        return "it"

    portuguese_keywords = [
        "olá",
        "ola",
        "bom dia",
        "boa tarde",
        "boa noite",
        "obrigado",
        "obrigada",
        "disponibilidade",
        "privado",
        "partilhado",
        "pessoas",
        "hoje",
        "amanhã",
        "amanha",
        "passeio",
        "cruzeiro",
    ]
    if any(word in text for word in portuguese_keywords):
        return "pt"

    return "en"


def get_text(key: str, language: str) -> str:
    translations = {
        "empty_reply": {
            "en": "Hello! I’ll be happy to help you with our cruises in Santorini.",
            "el": "Γεια σας! Θα χαρώ να σας βοηθήσω με τις κρουαζιέρες μας στη Σαντορίνη.",
            "it": "Ciao! Sarò felice di aiutarti con le nostre crociere a Santorini.",
            "pt": "Olá! Terei todo o gosto em ajudar com os nossos cruzeiros em Santorini.",
        },
        "greeting_reply": {
            "en": "Hello and welcome! I’ll be happy to help you with our cruises in Santorini. Feel free to ask me about availability, prices, shared or private options.",
            "el": "Γεια σας και καλώς ήρθατε! Θα χαρώ να σας βοηθήσω με τις κρουαζιέρες μας στη Σαντορίνη. Μπορείτε να με ρωτήσετε για διαθεσιμότητα, τιμές, κοινές ή ιδιωτικές επιλογές.",
            "it": "Ciao e benvenuto! Sarò felice di aiutarti con le nostre crociere a Santorini. Puoi chiedermi disponibilità, prezzi e opzioni condivise o private.",
            "pt": "Olá e bem-vindo! Terei todo o gosto em ajudar com os nossos cruzeiros em Santorini. Pode perguntar sobre disponibilidade, preços e opções partilhadas ou privadas.",
        },
        "discount_reply": {
            "en": f"For special rate requests, please contact us via WhatsApp: {WHATSAPP_LINK}",
            "el": f"Για ειδικά αιτήματα τιμών, παρακαλούμε επικοινωνήστε μαζί μας μέσω WhatsApp: {WHATSAPP_LINK}",
            "it": f"Per richieste di tariffe speciali, ti preghiamo di contattarci via WhatsApp: {WHATSAPP_LINK}",
            "pt": f"Para pedidos de tarifas especiais, por favor contacte-nos via WhatsApp: {WHATSAPP_LINK}",
        },
        "cruise_passenger_reply": {
            "en": f"For cruise ship guests, we kindly recommend contacting us directly via WhatsApp so we can assist you based on your ship schedule:\n{WHATSAPP_LINK}",
            "el": f"Για επισκέπτες κρουαζιερόπλοιου, σας προτείνουμε να επικοινωνήσετε απευθείας μαζί μας μέσω WhatsApp, ώστε να σας βοηθήσουμε βάσει του προγράμματος του πλοίου σας:\n{WHATSAPP_LINK}",
            "it": f"Per gli ospiti delle navi da crociera, consigliamo gentilmente di contattarci direttamente via WhatsApp così potremo assistervi in base all’orario della vostra nave:\n{WHATSAPP_LINK}",
            "pt": f"Para passageiros de cruzeiro, recomendamos gentilmente que nos contacte diretamente via WhatsApp para que possamos ajudar de acordo com o horário do seu navio:\n{WHATSAPP_LINK}",
        },
        "contact_reply": {
            "en": f"You can contact our reservations team directly on WhatsApp and we’ll be happy to assist you:\n{WHATSAPP_LINK}",
            "el": f"Μπορείτε να επικοινωνήσετε απευθείας με το τμήμα κρατήσεων μέσω WhatsApp και θα χαρούμε να σας εξυπηρετήσουμε:\n{WHATSAPP_LINK}",
            "it": f"Puoi contattare direttamente il nostro team prenotazioni su WhatsApp e saremo felici di aiutarti:\n{WHATSAPP_LINK}",
            "pt": f"Pode contactar diretamente a nossa equipa de reservas via WhatsApp e teremos todo o gosto em ajudar:\n{WHATSAPP_LINK}",
        },
        "irrelevant_reply": {
            "en": "I can assist only with questions related to our cruises in Santorini.",
            "el": "Μπορώ να βοηθήσω μόνο με ερωτήσεις που σχετίζονται με τις κρουαζιέρες μας στη Σαντορίνη.",
            "it": "Posso aiutare solo con domande relative alle nostre crociere a Santorini.",
            "pt": "Só posso ajudar com questões relacionadas com os nossos cruzeiros em Santorini.",
        },
        "availability_fallback": {
            "en": f"The best way to check the latest availability is through our booking page:\n{BOOKING_LINK}\n\nSimply select your preferred date and you’ll see all available options instantly.\n\nFor any clarification, feel free to contact us on WhatsApp:\n{WHATSAPP_LINK}",
            "el": f"Ο καλύτερος τρόπος για να δείτε την πιο πρόσφατη διαθεσιμότητα είναι μέσω της σελίδας κρατήσεών μας:\n{BOOKING_LINK}\n\nΑπλώς επιλέξτε την ημερομηνία που προτιμάτε και θα δείτε άμεσα όλες τις διαθέσιμες επιλογές.\n\nΓια οποιαδήποτε διευκρίνιση, μπορείτε να επικοινωνήσετε μαζί μας στο WhatsApp:\n{WHATSAPP_LINK}",
            "it": f"Il modo migliore per controllare la disponibilità più aggiornata è tramite la nostra pagina di prenotazione:\n{BOOKING_LINK}\n\nTi basta selezionare la data che preferisci e vedrai subito tutte le opzioni disponibili.\n\nPer qualsiasi chiarimento, puoi contattarci su WhatsApp:\n{WHATSAPP_LINK}",
            "pt": f"A melhor forma de verificar a disponibilidade mais atualizada é através da nossa página de reservas:\n{BOOKING_LINK}\n\nBasta selecionar a data pretendida e verá imediatamente todas as opções disponíveis.\n\nPara qualquer esclarecimento, contacte-nos via WhatsApp:\n{WHATSAPP_LINK}",
        },
        "spots_fallback": {
            "en": "I’m sorry, I could not identify the exact cruise from the previous message. Please tell me the cruise name and date, and I’ll gladly check the number of available spots for you.",
            "el": "Λυπάμαι, δεν μπόρεσα να εντοπίσω ακριβώς ποια κρουαζιέρα εννοείτε από το προηγούμενο μήνυμα. Πείτε μου το όνομα της κρουαζιέρας και την ημερομηνία και θα ελέγξω ευχαρίστως τις διαθέσιμες θέσεις.",
            "it": "Mi dispiace, non sono riuscito a identificare con precisione la crociera dal messaggio precedente. Indicami il nome della crociera e la data e controllerò con piacere i posti disponibili.",
            "pt": "Lamento, não consegui identificar exatamente o cruzeiro a partir do mensagem anterior. Diga-me o nome do cruzeiro e a data e verificarei com todo o gosto os lugares disponíveis.",
        },
        "booking_details_reply": {
            "en": f"I can’t see personal booking details here. Please check your booking confirmation, or contact us on WhatsApp and we’ll gladly assist you directly:\n{WHATSAPP_LINK}",
            "el": f"Δεν μπορώ να δω προσωπικά στοιχεία κράτησης εδώ. Παρακαλούμε ελέγξτε την επιβεβαίωση της κράτησής σας ή επικοινωνήστε μαζί μας στο WhatsApp και θα χαρούμε να σας εξυπηρετήσουμε:\n{WHATSAPP_LINK}",
            "it": f"Non posso vedere qui i dettagli personali della prenotazione. Ti preghiamo di controllare la conferma della prenotazione oppure di contattarci su WhatsApp e saremo lieti di aiutarti:\n{WHATSAPP_LINK}",
            "pt": f"Não consigo ver aqui os dados pessoais da reserva. Por favor consulte a confirmação da sua reserva ou contacte-nos via WhatsApp e teremos todo o gosto em ajudar:\n{WHATSAPP_LINK}",
        },
        "whatsapp_uncertain_reply": {
            "en": f"I don’t have that exact detail here, but our team can assist you directly on WhatsApp:\n{WHATSAPP_LINK}",
            "el": f"Δεν έχω αυτή την ακριβή πληροφορία εδώ, αλλά η ομάδα μας μπορεί να σας βοηθήσει απευθείας στο WhatsApp:\n{WHATSAPP_LINK}",
            "it": f"Non ho qui questo dettaglio preciso, ma il nostro team può aiutarti direttamente su WhatsApp:\n{WHATSAPP_LINK}",
            "pt": f"Não tenho aqui esse detalhe exato, mas a nossa equipa pode ajudar diretamente via WhatsApp:\n{WHATSAPP_LINK}",
        },
        "morning_unavailable_reply": {
            "en": f"Morning cruises are available only until 24 October 2026, so the requested morning cruise is not available on that date.\n\nDuring that period, only sunset cruises are operating.\n\nYou can check availability here:\n{BOOKING_LINK}\n\nFor any clarification, feel free to contact us on WhatsApp:\n{WHATSAPP_LINK}",
            "el": f"Οι πρωινές κρουαζιέρες είναι διαθέσιμες μόνο έως τις 24 Οκτωβρίου 2026, επομένως η ζητούμενη πρωινή κρουαζιέρα δεν είναι διαθέσιμη για εκείνη την ημερομηνία.\n\nΚατά την περίοδο αυτή πραγματοποιούνται μόνο απογευματινές κρουαζιέρες ηλιοβασιλέματος.\n\nΜπορείτε να δείτε τη διαθεσιμότητα εδώ:\n{BOOKING_LINK}\n\nΓια οποιαδήποτε διευκρίνιση, επικοινωνήστε μαζί μας στο WhatsApp:\n{WHATSAPP_LINK}",
            "it": f"Le crociere mattutine sono disponibili solo fino al 24 ottobre 2026, quindi la crociera mattutina richiesta non è disponibile in quella data.\n\nDurante quel periodo operano solo le crociere al tramonto.\n\nPuoi controllare la disponibilità qui:\n{BOOKING_LINK}\n\nPer qualsiasi chiarimento, puoi contattarci su WhatsApp:\n{WHATSAPP_LINK}",
            "pt": f"Os cruzeiros da manhã estão disponíveis apenas até 24 de outubro de 2026, por isso o cruzeiro da manhã solicitado não está disponível nessa data.\n\nDurante esse período operam apenas os cruzeiros ao pôr do sol.\n\nPode verificar a disponibilidade aqui:\n{BOOKING_LINK}\n\nPara qualquer esclarecimento, contacte-nos via WhatsApp:\n{WHATSAPP_LINK}",
        },
        "sunset_only_reply": {
            "en": f"During that period, we operate sunset cruises only.\n\nThe sunset cruise is a beautiful experience, as you can enjoy the famous Santorini sunset from the sea.\n\nYou can check availability here:\n{BOOKING_LINK}\n\nIf you need help choosing, feel free to contact us on WhatsApp:\n{WHATSAPP_LINK}",
            "el": f"Κατά την περίοδο αυτή πραγματοποιούνται μόνο απογευματινές κρουαζιέρες ηλιοβασιλέματος.\n\nΗ απογευματινή κρουαζιέρα είναι μια όμορφη εμπειρία, καθώς μπορείτε να απολαύσετε το διάσημο ηλιοβασίλεμα της Σαντορίνης από τη θάλασσα.\n\nΜπορείτε να δείτε τη διαθεσιμότητα εδώ:\n{BOOKING_LINK}\n\nΑν χρειάζεστε βοήθεια για να επιλέξετε, επικοινωνήστε μαζί μας στο WhatsApp:\n{WHATSAPP_LINK}",
            "it": f"Durante quel periodo operano solo le crociere al tramonto.\n\nLa crociera al tramonto è una bellissima esperienza, perché permette di ammirare il famoso tramonto di Santorini dal mare.\n\nPuoi controllare la disponibilità qui:\n{BOOKING_LINK}\n\nSe hai bisogno di aiuto nella scelta, puoi contattarci su WhatsApp:\n{WHATSAPP_LINK}",
            "pt": f"Durante esse período operam apenas os cruzeiros ao pôr do sol.\n\nO cruzeiro ao pôr do sol é uma experiência muito bonita, pois permite apreciar o famoso pôr do sol de Santorini a partir do mar.\n\nPode verificar a disponibilidade aqui:\n{BOOKING_LINK}\n\nSe precisar de ajuda para escolher, contacte-nos via WhatsApp:\n{WHATSAPP_LINK}",
        },
        "off_season_reply": {
            "en": f"Our cruises are not operating during that period, as the season is closed.\n\nWe resume from 15 March 2027.\n\nYou can check available dates here:\n{BOOKING_LINK}\n\nFor any clarification, feel free to contact us on WhatsApp:\n{WHATSAPP_LINK}",
            "el": f"Οι κρουαζιέρες μας δεν πραγματοποιούνται κατά την περίοδο αυτή, καθώς η σεζόν είναι κλειστή.\n\nΞεκινάμε ξανά από τις 15 Μαρτίου 2027.\n\nΜπορείτε να δείτε τις διαθέσιμες ημερομηνίες εδώ:\n{BOOKING_LINK}\n\nΓια οποιαδήποτε διευκρίνιση, επικοινωνήστε μαζί μας στο WhatsApp:\n{WHATSAPP_LINK}",
            "it": f"Le nostre crociere non operano in quel periodo, poiché la stagione è chiusa.\n\nRiprendiamo dal 15 marzo 2027.\n\nPuoi controllare le date disponibili qui:\n{BOOKING_LINK}\n\nPer qualsiasi chiarimento, puoi contattarci su WhatsApp:\n{WHATSAPP_LINK}",
            "pt": f"Os nossos cruzeiros não operam durante esse período, pois a temporada está encerrada.\n\nRetomamos a partir de 15 de março de 2027.\n\nPode verificar as datas disponíveis aqui:\n{BOOKING_LINK}\n\nPara qualquer esclarecimento, contacte-nos via WhatsApp:\n{WHATSAPP_LINK}",
        },
    }

    return translations.get(key, {}).get(
        language, translations.get(key, {}).get("en", "")
    )


def translate_availability_reply(reply_text: str, language: str) -> str:
    if language == "en":
        return reply_text

    replacements = {
        "el": [
            ("Thank you for your message.", "Σας ευχαριστούμε για το μήνυμά σας."),
            (
                "Unfortunately, we do not currently have any",
                "Δυστυχώς, δεν έχουμε αυτή τη στιγμή",
            ),
            ("cruises available for", "διαθέσιμες κρουαζιέρες για"),
            ("available for", "διαθέσιμες για"),
            (
                "You may check other dates here:",
                "Μπορείτε να δείτε άλλες ημερομηνίες εδώ:",
            ),
            ("For ", "Για "),
            ("the following private", "τις παρακάτω ιδιωτικές"),
            ("the following shared", "τις παρακάτω κοινές"),
            ("the following", "τις παρακάτω"),
            (
                "private cruises are available:",
                "ιδιωτικές κρουαζιέρες είναι διαθέσιμες:",
            ),
            ("shared cruises are available:", "κοινές κρουαζιέρες είναι διαθέσιμες:"),
            ("cruises are available:", "κρουαζιέρες είναι διαθέσιμες:"),
            (" is available.", " είναι διαθέσιμη."),
            (" are available.", " είναι διαθέσιμες."),
            ("Shared cruises:", "Κοινές κρουαζιέρες:"),
            ("Private cruises:", "Ιδιωτικές κρουαζιέρες:"),
            (
                "You can proceed directly with your booking here:",
                "Μπορείτε να προχωρήσετε απευθείας στην κράτησή σας εδώ:",
            ),
            (
                "You may proceed with your booking here:",
                "Μπορείτε να προχωρήσετε στην κράτησή σας εδώ:",
            ),
            (
                "Please select the date on the booking page.",
                "Παρακαλούμε επιλέξτε την ημερομηνία στη σελίδα κράτησης.",
            ),
            ("morning", "πρωινές"),
            ("sunset", "απογευματινές"),
        ],
        "it": [
            ("Thank you for your message.", "Grazie per il tuo messaggio."),
            (
                "Unfortunately, we do not currently have any",
                "Purtroppo al momento non abbiamo",
            ),
            ("cruises available for", "crociere disponibili per"),
            ("available for", "disponibili per"),
            ("You may check other dates here:", "Puoi controllare altre date qui:"),
            ("For ", "Per il "),
            ("the following private", "le seguenti private"),
            ("the following shared", "le seguenti condivise"),
            ("the following", "le seguenti"),
            ("private cruises are available:", "crociere private disponibili:"),
            ("shared cruises are available:", "crociere condivise disponibili:"),
            ("cruises are available:", "crociere disponibili:"),
            (" is available.", " è disponibile."),
            (" are available.", " sono disponibili."),
            ("Shared cruises:", "Crociere condivise:"),
            ("Private cruises:", "Crociere private:"),
            (
                "You can proceed directly with your booking here:",
                "Puoi procedere direttamente con la prenotazione qui:",
            ),
            (
                "You may proceed with your booking here:",
                "Puoi procedere con la prenotazione qui:",
            ),
            (
                "Please select the date on the booking page.",
                "Ti preghiamo di selezionare la data nella pagina di prenotazione.",
            ),
        ],
        "pt": [
            ("Thank you for your message.", "Obrigado pela sua mensagem."),
            (
                "Unfortunately, we do not currently have any",
                "Infelizmente, neste momento não temos",
            ),
            ("cruises available for", "cruzeiros disponíveis para"),
            ("available for", "disponíveis para"),
            ("You may check other dates here:", "Pode verificar outras datas aqui:"),
            ("For ", "Para "),
            ("the following private", "os seguintes privados"),
            ("the following shared", "os seguintes partilhados"),
            ("the following", "os seguintes"),
            ("private cruises are available:", "cruzeiros privados disponíveis:"),
            ("shared cruises are available:", "cruzeiros partilhados disponíveis:"),
            ("cruises are available:", "cruzeiros disponíveis:"),
            (" is available.", " está disponível."),
            (" are available.", " estão disponíveis."),
            ("Shared cruises:", "Cruzeiros partilhados:"),
            ("Private cruises:", "Cruzeiros privados:"),
            (
                "You can proceed directly with your booking here:",
                "Pode avançar diretamente com a sua reserva aqui:",
            ),
            (
                "You may proceed with your booking here:",
                "Pode avançar com a sua reserva aqui:",
            ),
            (
                "Please select the date on the booking page.",
                "Por favor selecione a data na página de reservas.",
            ),
        ],
    }

    translated = reply_text
    for source, target in replacements.get(language, []):
        translated = translated.replace(source, target)

    return translated


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
        return get_text("availability_fallback", language)

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


def parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def get_requested_period(tour_key: str | None, period: str | None) -> str | None:
    if tour_key:
        lowered = tour_key.lower()
        if "morning" in lowered:
            return "morning"
        if "sunset" in lowered:
            return "sunset"
    return period


def get_seasonal_reply(
    date_str: str | None,
    language: str,
    tour_key: str | None = None,
    period: str | None = None,
    generic_availability: bool = False,
) -> str | None:
    requested_date = parse_iso_date(date_str)
    if not requested_date:
        return None

    requested_period = get_requested_period(tour_key, period)

    sunset_only_start = date(2026, 10, 25)
    sunset_only_end = date(2026, 11, 15)
    off_season_start = date(2026, 11, 16)
    season_resume = date(2027, 3, 15)

    if off_season_start <= requested_date < season_resume:
        return get_text("off_season_reply", language)

    if sunset_only_start <= requested_date <= sunset_only_end:
        if requested_period == "morning":
            return get_text("morning_unavailable_reply", language)

        if generic_availability and requested_period is None and tour_key is None:
            return get_text("sunset_only_reply", language)

    return None


def safe_check_tour_availability(tour_key: str, date_str: str):
    try:
        return check_tour_availability(tour_key, date_str)
    except Exception as exc:
        print(f"Availability lookup error for {tour_key} on {date_str}: {exc}")
        return None


def safe_find_available_tours(
    effective_date: str,
    period: str | None,
    user_message: str,
    passenger_count: int | None,
):
    try:
        return find_available_tours(
            effective_date, period, user_message, passenger_count
        )
    except Exception as exc:
        print(f"Availability search error for {effective_date}: {exc}")
        return None


@app.get("/")
def root():
    return {"message": "Santorini bot is running"}


@app.get("/admin/logs")
def admin_logs():
    return {"logs": get_chat_logs(200)}


@app.post("/chat")
def chat(request: ChatRequest):
    user_message = request.message.strip()
    history = request.history or []
    language = detect_language(user_message)

    if not user_message:
        reply = get_text("empty_reply", language)
        return log_and_return(
            user_message="",
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=None,
        )

    if is_discount_request(user_message):
        reply = get_text("discount_reply", language)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=None,
        )

    if is_cruise_passenger(user_message):
        reply = get_text("cruise_passenger_reply", language)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=None,
        )

    if is_contact_request(user_message):
        reply = get_text("contact_reply", language)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=None,
        )

    if is_personal_booking_request(user_message):
        reply = get_text("booking_details_reply", language)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=None,
        )

    if is_uncertain_whatsapp_case(user_message):
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
            )
        except Exception:
            reply = get_text("whatsapp_uncertain_reply", language)
            return log_and_return(
                user_message=user_message,
                reply=reply,
                language=language,
                fallback=True,
                detected_tour=None,
            )

    if is_capacity_request(user_message) and is_multi_capacity_request(user_message):
        date_str = detect_date(user_message)
        period = detect_period(user_message)
        passenger_count = detect_passenger_count(user_message, history)
        effective_date = date_str or get_effective_date(user_message, history)

        seasonal_reply = get_seasonal_reply(
            date_str=effective_date,
            language=language,
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
            )

        results = safe_find_available_tours(
            effective_date, period, user_message, passenger_count
        )

        if results:
            reply_text = build_multi_capacity_reply(results, language)
            return log_and_return(
                user_message=user_message,
                reply=reply_text,
                language=language,
                fallback=False,
                detected_tour=None,
            )

        reply = get_text("availability_fallback", language)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=True,
            detected_tour=None,
        )

    if is_capacity_request(user_message):
        last_tour_key, last_date_str = get_last_tour_and_date_from_history(
            user_message, history
        )

        seasonal_reply = get_seasonal_reply(
            date_str=last_date_str,
            language=language,
            tour_key=last_tour_key,
        )
        if seasonal_reply:
            return log_and_return(
                user_message=user_message,
                reply=seasonal_reply,
                language=language,
                fallback=False,
                detected_tour=last_tour_key,
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
                )

            reply = get_text("availability_fallback", language)
            return log_and_return(
                user_message=user_message,
                reply=reply,
                language=language,
                fallback=True,
                detected_tour=last_tour_key,
            )

        reply = get_text("spots_fallback", language)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=True,
            detected_tour=None,
        )

    tour_key = detect_tour_key(user_message)
    date_str = detect_date(user_message)
    period = detect_period(user_message)
    tour_facts = build_tour_facts_block(tour_key) if tour_key else ""
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
            tour_key=effective_tour_key,
        )
        if seasonal_reply:
            return log_and_return(
                user_message=user_message,
                reply=seasonal_reply,
                language=language,
                fallback=False,
                detected_tour=effective_tour_key,
            )

        if effective_tour_key and effective_date_str:
            data = safe_check_tour_availability(effective_tour_key, effective_date_str)
            print("PRICE DATA DEBUG:", data)
            if data:
                availability = data.get("availability", {}) if isinstance(data, dict) else {}

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
                        )

        reply = get_text("availability_fallback", language)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=True,
            detected_tour=effective_tour_key,
        )

    availability_intent = (
        not comparison_intent
        and not price_intent
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

    passenger_count = detect_passenger_count(user_message, history)

    seasonal_reply = get_seasonal_reply(
        date_str=date_str,
        language=language,
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
        )

    if tour_key and date_str:
        data = safe_check_tour_availability(tour_key, date_str)
        if data:
            reply_text = build_availability_reply(data)
            reply_text = translate_availability_reply(reply_text, language)
            return log_and_return(
                user_message=user_message,
                reply=reply_text,
                language=language,
                fallback=False,
                detected_tour=tour_key,
            )

        reply = get_text("availability_fallback", language)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=True,
            detected_tour=tour_key,
        )

    if date_str or availability_intent:
        effective_date = get_effective_date(user_message, history)

        seasonal_reply = get_seasonal_reply(
            date_str=effective_date,
            language=language,
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
            )

        results = safe_find_available_tours(
            effective_date, period, user_message, passenger_count
        )
        if results is None:
            reply = get_text("availability_fallback", language)
            return log_and_return(
                user_message=user_message,
                reply=reply,
                language=language,
                fallback=True,
                detected_tour=tour_key,
            )

        filtered_results = filter_results_by_cruise_type(results, cruise_type_intent)

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
            )

        reply = get_text("availability_fallback", language)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=True,
            detected_tour=tour_key,
        )

    if is_best_choice_question(user_message) and history:
        reply = build_best_choice_reply(
            history=history,
            language=language,
            passenger_count=detect_passenger_count(user_message, history),
        )
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=tour_key,
        )

    if is_greeting(user_message):
        reply = get_text("greeting_reply", language)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=tour_key,
        )

    short_followup = len(user_message.split()) <= 4

    if not is_relevant(user_message) and not is_followup(user_message) and not short_followup:
        reply = get_text("irrelevant_reply", language)
        return log_and_return(
            user_message=user_message,
            reply=reply,
            language=language,
            fallback=False,
            detected_tour=tour_key,
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
    )
