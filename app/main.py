import re

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


def detect_language(user_message: str) -> str:
    text = user_message.lower()

    greek_chars = any(
        ("α" <= c <= "ω") or ("ά" <= c <= "ώ") for c in text
    )
    if greek_chars:
        return "el"

    italian_keywords = [
        "ciao", "salve", "buongiorno", "buonasera", "grazie",
        "disponibilità", "disponibile", "privata", "tramonto",
        "mattina", "persone", "crociera", "crociere", "oggi", "domani"
    ]
    if any(word in text for word in italian_keywords):
        return "it"

    portuguese_keywords = [
        "olá", "ola", "bom dia", "boa tarde", "boa noite", "obrigado",
        "obrigada", "disponibilidade", "privado", "partilhado",
        "pessoas", "hoje", "amanhã", "amanha", "passeio", "cruzeiro"
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
        "irrelevant_reply": {
            "en": "I can assist only with questions related to our cruises in Santorini.",
            "el": "Μπορώ να βοηθήσω μόνο με ερωτήσεις που σχετίζονται με τις κρουαζιέρες μας στη Σαντορίνη.",
            "it": "Posso aiutare solo con domande relative alle nostre crociere a Santorini.",
            "pt": "Só posso ajudar com questões relacionadas com os nossos cruzeiros em Santorini.",
        },
        "availability_fallback": {
            "en": f"The best way to check the latest availability is through our booking page:\n{BOOKING_LINK}\n\nSimply select your preferred date and you’ll see all available options instantly.",
            "el": f"Ο καλύτερος τρόπος για να δείτε την πιο πρόσφατη διαθεσιμότητα είναι μέσω της σελίδας κρατήσεών μας:\n{BOOKING_LINK}\n\nΑπλώς επιλέξτε την ημερομηνία που προτιμάτε και θα δείτε άμεσα όλες τις διαθέσιμες επιλογές.",
            "it": f"Il modo migliore per controllare la disponibilità più aggiornata è tramite la nostra pagina di prenotazione:\n{BOOKING_LINK}\n\nTi basta selezionare la data che preferisci e vedrai subito tutte le opzioni disponibili.",
            "pt": f"A melhor forma de verificar a disponibilidade mais atualizada é através da nossa página de reservas:\n{BOOKING_LINK}\n\nBasta selecionar a data pretendida e verá imediatamente todas as opções disponíveis.",
        },
        "spots_fallback": {
            "en": "I’m sorry, I could not identify the exact cruise from the previous message. Please tell me the cruise name and date, and I’ll gladly check the number of available spots for you.",
            "el": "Λυπάμαι, δεν μπόρεσα να εντοπίσω ακριβώς ποια κρουαζιέρα εννοείτε από το προηγούμενο μήνυμα. Πείτε μου το όνομα της κρουαζιέρας και την ημερομηνία και θα ελέγξω ευχαρίστως τις διαθέσιμες θέσεις.",
            "it": "Mi dispiace, non sono riuscito a identificare con precisione la crociera dal messaggio precedente. Indicami il nome della crociera e la data e controllerò con piacere i posti disponibili.",
            "pt": "Lamento, não consegui identificar exatamente o cruzeiro a partir da mensagem anterior. Diga-me o nome do cruzeiro e a data e verificarei com todo o gosto os lugares disponíveis.",
        },
    }

    return translations.get(key, {}).get(language, translations.get(key, {}).get("en", ""))


def translate_availability_reply(reply_text: str, language: str) -> str:
    if language == "en":
        return reply_text

    replacements = {
        "el": [
            ("Thank you for your message.", "Σας ευχαριστούμε για το μήνυμά σας."),
            ("Unfortunately, we do not currently have any", "Δυστυχώς, δεν έχουμε αυτή τη στιγμή"),
            ("cruises available for", "διαθέσιμες κρουαζιέρες για"),
            ("available for", "διαθέσιμες για"),
            ("You may check other dates here:", "Μπορείτε να δείτε άλλες ημερομηνίες εδώ:"),
            ("For ", "Για "),
            ("the following private", "τις παρακάτω ιδιωτικές"),
            ("the following shared", "τις παρακάτω κοινές"),
            ("the following", "τις παρακάτω"),
            ("private cruises are available:", "ιδιωτικές κρουαζιέρες είναι διαθέσιμες:"),
            ("shared cruises are available:", "κοινές κρουαζιέρες είναι διαθέσιμες:"),
            ("cruises are available:", "κρουαζιέρες είναι διαθέσιμες:"),
            (" is available.", " είναι διαθέσιμη."),
            (" are available.", " είναι διαθέσιμες."),
            ("Shared cruises:", "Κοινές κρουαζιέρες:"),
            ("Private cruises:", "Ιδιωτικές κρουαζιέρες:"),
            ("You can proceed directly with your booking here:", "Μπορείτε να προχωρήσετε απευθείας στην κράτησή σας εδώ:"),
            ("You may proceed with your booking here:", "Μπορείτε να προχωρήσετε στην κράτησή σας εδώ:"),
            ("Please select the date on the booking page.", "Παρακαλούμε επιλέξτε την ημερομηνία στη σελίδα κράτησης."),
            ("morning", "πρωινές"),
            ("sunset", "απογευματινές"),
        ],
        "it": [
            ("Thank you for your message.", "Grazie per il tuo messaggio."),
            ("Unfortunately, we do not currently have any", "Purtroppo al momento non abbiamo"),
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
            ("You can proceed directly with your booking here:", "Puoi procedere direttamente con la prenotazione qui:"),
            ("You may proceed with your booking here:", "Puoi procedere con la prenotazione qui:"),
            ("Please select the date on the booking page.", "Ti preghiamo di selezionare la data nella pagina di prenotazione."),
        ],
        "pt": [
            ("Thank you for your message.", "Obrigado pela sua mensagem."),
            ("Unfortunately, we do not currently have any", "Infelizmente, neste momento não temos"),
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
            ("You can proceed directly with your booking here:", "Pode avançar diretamente com a sua reserva aqui:"),
            ("You may proceed with your booking here:", "Pode avançar com a sua reserva aqui:"),
            ("Please select the date on the booking page.", "Por favor selecione a data na página de reservas."),
        ],
    }

    translated = reply_text
    for source, target in replacements.get(language, []):
        translated = translated.replace(source, target)

    return translated


def is_greeting(user_message: str) -> bool:
    text = user_message.lower().strip()

    greetings = {
        "hi", "hello", "hey",
        "good morning", "good afternoon", "good evening",
        "hi there", "hello there",
        "γεια", "γειά", "γεια σου", "γειά σου", "γεια σας", "γειά σας",
        "καλημέρα", "καλησπέρα", "καλησπερα", "καληνύχτα", "καληνυχτα",
        "χαίρετε", "χαιρετε",
        "ciao", "salve", "buongiorno", "buonasera",
        "olá", "ola", "bom dia", "boa tarde", "boa noite"
    }

    return text in greetings


def is_discount_request(user_message: str) -> bool:
    text = user_message.lower()

    keywords = [
        "discount", "better price", "best price", "special price",
        "cheaper", "deal",
        "εκπτωση", "έκπτωση", "καλύτερη τιμή",
        "sconto", "offerta",
        "desconto", "melhor preço", "preço especial"
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

        "crociera", "nave", "porto vecchio",

        "navio de cruzeiro", "passageiro de cruzeiro", "porto antigo"
    ]

    return any(k in text for k in keywords)


def is_availability_request(user_message: str) -> bool:
    text = user_message.lower().strip()

    keywords = [
        "availability", "available", "availabile", "disponibilità",
        "do you have availability", "is there availability", "any availability",
        "what is available", "what tours are available",
        "today", "tomorrow", "tonight", "this afternoon", "this evening", "this morning",
        "for today", "for tomorrow",

        "διαθεσιμότητα", "διαθεσιμοτητα", "διαθέσιμο", "διαθεσιμο",
        "σήμερα", "σημερα", "αύριο", "αυριο", "απόψε", "αποψε",
        "σήμερα το απόγευμα", "σημερα το απογευμα", "σήμερα το πρωί", "σημερα το πρωι",

        "disponibile", "disponibili", "oggi", "domani", "stasera",
        "questo pomeriggio", "questa mattina",

        "disponibilidade", "disponível", "disponivel", "hoje", "amanhã", "amanha",
        "esta tarde", "esta manhã", "esta manha"
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

        "spot", "spots", "seat", "seats", "place", "places", "left", "vessel", "vessels", "all available",

        "κρουαζιέρα", "κρουαζιερες", "τιμή", "διαθεσιμότητα",
        "ιδιωτική", "ηλιοβασίλεμα", "πρωινή", "λιμάνι", "μεταφορά",
        "φαγητό", "ποτό", "ποτά", "μενού",
        "χορτοφαγ", "βίγκαν", "χαλάλ", "αλλεργ",
        "γλουτένη", "χωρίς γλουτένη", "κοιλιοκάκη",
        "άτομα", "άτομο", "είμαστε", "έχουμε",
        "προτείνεις", "προτείνετε", "σύσταση",
        "διαφορά", "σύγκριση",
        "θέσεις", "θέση", "πόσες θέσεις", "πόσα άτομα μένουν", "όλα τα σκάφη", "όλα τα διαθέσιμα",

        "crociera", "crociere", "prezzo", "disponibilità",
        "privata", "tramonto", "mattina",
        "cibo", "bevande", "menu",
        "vegetariano", "vegano", "halal",
        "allergie", "glutine", "senza glutine",
        "persone", "persona", "siamo", "abbiamo",
        "consigli", "raccomandi", "suggerisci",
        "differenza", "confronto",
        "posti", "posto", "quanti posti", "tutte le barche",

        "cruzeiro", "cruzeiros", "preço", "preco", "disponibilidade",
        "privado", "partilhado", "compartilhado",
        "comida", "bebidas", "menu",
        "vegetariano", "vegano", "alergia", "alergias",
        "glúten", "gluten", "sem glúten", "sem gluten",
        "pessoas", "pessoa", "somos", "temos",
        "recomenda", "sugere", "diferença", "comparação", "comparacao",
        "lugares", "quantos lugares", "vagas", "todos os barcos"
    ]

    return any(k in text for k in keywords)


def is_followup(user_message: str) -> bool:
    text = user_message.lower().strip()

    followups = {
        "yes", "yes please", "ok", "okay", "sure", "please",
        "tell me more", "go ahead", "continue",
        "ναι", "οκ", "εντάξει", "συνέχισε",
        "si", "va bene", "continua",
        "sim", "claro", "continue"
    }

    return text in followups


def is_capacity_request(user_message: str) -> bool:
    text = user_message.lower().strip()

    keywords = [
        "how many spots",
        "how many seats",
        "how many places",
        "how many left",
        "spots left",
        "seats left",
        "places left",
        "available spots",
        "available seats",
        "availability left",

        "πόσες θέσεις",
        "πόση διαθεσιμότητα",
        "πόσα άτομα μένουν",

        "quanti posti",
        "posti disponibili",

        "quantos lugares",
        "lugares disponíveis",
        "vagas disponíveis"
    ]

    return any(k in text for k in keywords)


def is_multi_capacity_request(user_message: str) -> bool:
    text = user_message.lower().strip()

    keywords = [
        "all available vessel",
        "all available vessels",
        "all vessels",
        "all available cruises",
        "all available tours",
        "all available options",
        "all available boats",

        "όλα τα σκάφη",
        "όλα τα διαθέσιμα σκάφη",
        "όλες οι διαθέσιμες επιλογές",

        "tutte le barche",
        "tutte le crociere disponibili",
        "tutte le opzioni disponibili",

        "todos os barcos",
        "todos os cruzeiros disponíveis",
        "todas as opções disponíveis"
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


def detect_cruise_type_intent(user_message: str, history: list[dict] | None = None) -> str | None:
    text = user_message.lower()

    private_keywords = [
        "private", "privately", "just for us", "only for us", "for our group only",
        "ιδιωτική", "ιδιωτικη", "μόνο για εμάς", "μονο για εμας",
        "privata", "solo per noi",
        "privado", "privada", "só para nós", "so para nos"
    ]

    shared_keywords = [
        "shared", "semi private", "semi-private", "join", "group cruise",
        "κοινή", "κοινη",
        "condivisa", "di gruppo",
        "partilhado", "compartilhado", "grupo"
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


def detect_passenger_count(user_message: str, history: list[dict] | None = None) -> int | None:
    texts_to_check = [user_message.lower()]

    if history:
        for item in reversed(history[-8:]):
            if item.get("role") == "user":
                previous_text = item.get("content", "").lower()
                if previous_text:
                    texts_to_check.append(previous_text)

    patterns = [
        r"\bwe are (\d+)\b",
        r"\bwe have (\d+)\b",
        r"\bfor (\d+) people\b",
        r"\bfor (\d+) persons\b",
        r"\b(\d+) people\b",
        r"\b(\d+) persons\b",
        r"\b(\d+) guests\b",
        r"\b(\d+) pax\b",
        r"\bparty of (\d+)\b",

        r"\bείμαστε (\d+)\b",
        r"\bειμαστε (\d+)\b",
        r"\bγια (\d+) άτομα\b",
        r"\bγια (\d+) ατομα\b",
        r"\b(\d+) άτομα\b",
        r"\b(\d+) ατομα\b",

        r"\bsiamo (\d+)\b",
        r"\bper (\d+) persone\b",
        r"\b(\d+) persone\b",

        r"\bsomos (\d+)\b",
        r"\bpara (\d+) pessoas\b",
        r"\b(\d+) pessoas\b",
        r"\b(\d+) pessoa(s)?\b"
    ]

    for text in texts_to_check:
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))

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
            "reply_label"
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


def detect_tour_key_from_history_text(text: str) -> str | None:
    detected = detect_tour_key(text)
    if detected:
        return detected

    lowered = text.lower()

    if "diamond sunset" in lowered:
        return "diamondsunset"
    if "diamond morning" in lowered:
        return "diamondmorning"
    if "gems sunset" in lowered:
        return "gemssunset"
    if "gems morning" in lowered:
        return "gemsmorning"
    if "platinum sunset" in lowered:
        return "platinumsunset"
    if "platinum morning" in lowered:
        return "platinummorning"
    if "red sunset" in lowered:
        return "redsunset"
    if "red morning" in lowered:
        return "redmorning"

    return None


def get_last_tour_and_date_from_history(
    user_message: str,
    history: list[dict]
) -> tuple[str | None, str | None]:
    current_tour = detect_tour_key_from_history_text(user_message)
    current_date = detect_date(user_message)

    if current_tour and current_date:
        return current_tour, current_date

    if history:
        for item in reversed(history[-10:]):
            content = item.get("content", "").strip()
            if not content:
                continue

            if not current_tour:
                current_tour = detect_tour_key_from_history_text(content)

            if not current_date:
                current_date = detect_date(content)

            if current_tour and current_date:
                return current_tour, current_date

    return current_tour, current_date


def get_capacity_number(data) -> int | None:
    if not isinstance(data, dict):
        return None

    availability = data.get("availability")

    if isinstance(availability, dict):
        for key in ["available_spots", "spots", "vacancies", "available", "capacity_left"]:
            value = availability.get(key)
            if isinstance(value, int):
                return value
            if isinstance(value, str) and value.isdigit():
                return int(value)

    return None


def build_capacity_reply(data, language: str) -> str:
    spots = get_capacity_number(data)
    cruise_name = data.get("reply_label", "this cruise")
    booking_url = data.get("booking_url", BOOKING_LINK)

    if language == "el":
        if spots == 1:
            return (
                f"Για το {cruise_name} υπάρχει μόνο 1 διαθέσιμη θέση.\n\n"
                f"Μπορείτε να προχωρήσετε στην κράτησή σας εδώ:\n{booking_url}\n\n"
                "Παρακαλούμε επιλέξτε την ημερομηνία στη σελίδα κράτησης."
            )
        if isinstance(spots, int):
            return (
                f"Για το {cruise_name} υπάρχουν {spots} διαθέσιμες θέσεις.\n\n"
                f"Μπορείτε να προχωρήσετε στην κράτησή σας εδώ:\n{booking_url}\n\n"
                "Παρακαλούμε επιλέξτε την ημερομηνία στη σελίδα κράτησης."
            )
        return (
            f"Το {cruise_name} είναι διαθέσιμο για την ημερομηνία που ζητήσατε.\n\n"
            f"Μπορείτε να προχωρήσετε στην κράτησή σας εδώ:\n{booking_url}\n\n"
            "Παρακαλούμε επιλέξτε την ημερομηνία στη σελίδα κράτησης."
        )

    if language == "it":
        if spots == 1:
            return (
                f"Per {cruise_name} è disponibile solo 1 posto.\n\n"
                f"Puoi procedere con la prenotazione qui:\n{booking_url}\n\n"
                "Ti preghiamo di selezionare la data nella pagina di prenotazione."
            )
        if isinstance(spots, int):
            return (
                f"Per {cruise_name} ci sono {spots} posti disponibili.\n\n"
                f"Puoi procedere con la prenotazione qui:\n{booking_url}\n\n"
                "Ti preghiamo di selezionare la data nella pagina di prenotazione."
            )
        return (
            f"{cruise_name} è disponibile per la data richiesta.\n\n"
            f"Puoi procedere con la prenotazione qui:\n{booking_url}\n\n"
            "Ti preghiamo di selezionare la data nella pagina di prenotazione."
        )

    if language == "pt":
        if spots == 1:
            return (
                f"Para {cruise_name} há apenas 1 lugar disponível.\n\n"
                f"Pode avançar com a sua reserva aqui:\n{booking_url}\n\n"
                "Por favor selecione a data na página de reservas."
            )
        if isinstance(spots, int):
            return (
                f"Para {cruise_name} há {spots} lugares disponíveis.\n\n"
                f"Pode avançar com a sua reserva aqui:\n{booking_url}\n\n"
                "Por favor selecione a data na página de reservas."
            )
        return (
            f"{cruise_name} está disponível para a data solicitada.\n\n"
            f"Pode avançar com a sua reserva aqui:\n{booking_url}\n\n"
            "Por favor selecione a data na página de reservas."
        )

    if spots == 1:
        return (
            f"For {cruise_name}, there is only 1 spot available.\n\n"
            f"You can proceed with your booking here:\n{booking_url}\n\n"
            "Please select the date on the booking page."
        )

    if isinstance(spots, int):
        return (
            f"For {cruise_name}, there are {spots} spots available.\n\n"
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


def is_private_result(item: dict) -> bool:
    tour_type = str(item.get("tour_type", "")).lower().strip()
    label = str(item.get("reply_label", "")).lower()

    return tour_type == "private" or "private" in label


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
        lines.append("Ti preghiamo di selezionare la data nella pagina di prenotazione.")
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


@app.get("/")
def root():
    return {"message": "Santorini bot is running"}


@app.post("/chat")
def chat(request: ChatRequest):
    user_message = request.message.strip()
    history = request.history or []
    language = detect_language(user_message)

    if not user_message:
        return {
            "reply": get_text("empty_reply", language)
        }

    if is_discount_request(user_message):
        return {
            "reply": get_text("discount_reply", language)
        }

    if is_cruise_passenger(user_message):
        return {
            "reply": get_text("cruise_passenger_reply", language)
        }

    if is_capacity_request(user_message) and is_multi_capacity_request(user_message):
        date_str = detect_date(user_message)
        period = detect_period(user_message)
        passenger_count = detect_passenger_count(user_message, history)
        effective_date = date_str or detect_date("today")

        results = find_available_tours(
            effective_date,
            period,
            user_message,
            passenger_count
        )

        if results:
            reply_text = build_multi_capacity_reply(results, language)
            return {"reply": reply_text}

        return {"reply": get_text("availability_fallback", language)}

    if is_capacity_request(user_message):
        last_tour_key, last_date_str = get_last_tour_and_date_from_history(user_message, history)

        if last_tour_key and last_date_str:
            data = check_tour_availability(last_tour_key, last_date_str)
            reply_text = build_capacity_reply(data, language)
            return {"reply": reply_text}

        return {"reply": get_text("spots_fallback", language)}

    tour_key = detect_tour_key(user_message)
    date_str = detect_date(user_message)
    period = detect_period(user_message)
    cruise_type_intent = detect_cruise_type_intent(user_message, history)
    availability_intent = is_availability_request(user_message)
    passenger_count = detect_passenger_count(user_message, history)

    if tour_key and date_str:
        data = check_tour_availability(tour_key, date_str)
        reply_text = build_availability_reply(data)
        reply_text = translate_availability_reply(reply_text, language)
        return {"reply": reply_text}

    if date_str or availability_intent:
        effective_date = date_str or detect_date("today")
        results = find_available_tours(
            effective_date,
            period,
            user_message,
            passenger_count
        )
        filtered_results = filter_results_by_cruise_type(results, cruise_type_intent)

        if filtered_results:
            reply_text = build_multi_availability_reply(
                filtered_results,
                effective_date,
                period,
                language
            )
            reply_text = translate_availability_reply(reply_text, language)
            return {"reply": reply_text}

        return {"reply": get_text("availability_fallback", language)}

    if is_greeting(user_message):
        return {
            "reply": get_text("greeting_reply", language)
        }

    if not is_relevant(user_message) and not is_followup(user_message):
        return {
            "reply": get_text("irrelevant_reply", language)
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