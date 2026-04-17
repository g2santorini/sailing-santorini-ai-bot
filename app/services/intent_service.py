import re


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def contains_any(text: str, keywords: list[str]) -> bool:
    return any(k in text for k in keywords)


def matches_any(text: str, phrases: set[str]) -> bool:
    return text in phrases


def is_greeting(user_message: str) -> bool:
    text = normalize_text(user_message)

    greetings = {
        "hi", "hello", "hey",
        "good morning", "good afternoon", "good evening",
        "hi there", "hello there",
        "γεια", "γειά", "γεια σου", "γειά σου", "γεια σας", "γειά σας",
        "καλημέρα", "καλησπέρα", "καλησπερα", "καληνύχτα", "καληνυχτα",
        "χαίρετε", "χαιρετε",
        "ciao", "salve", "buongiorno", "buonasera",
        "olá", "ola", "bom dia", "boa tarde", "boa noite",
    }

    return matches_any(text, greetings)

def is_sunset_concern(message: str) -> bool:
    message = message.lower()

    keywords = [
        "miss the sunset",
        "see the sunset",
        "sunset time",
        "finish before sunset",
        "cruise ends before sunset",
        "will we see sunset"
    ]

    return any(k in message for k in keywords)

def is_discount_request(user_message: str) -> bool:
    text = normalize_text(user_message)

    keywords = [
        "discount", "better price", "best price", "special price",
        "cheaper", "deal", 
        "εκπτωση", "έκπτωση", "καλύτερη τιμή", "καλυτερη τιμη",
        "καλύτερη προσφορά", "καλυτερη προσφορα", "προσφορά", "προσφορα",
        "sconto", "offerta", "prezzo migliore",
        "desconto", "melhor preço", "melhor preco", "preço especial", "preco especial",
    ]

    return contains_any(text, keywords)


def is_contact_request(user_message: str) -> bool:
    text = normalize_text(user_message)

    keywords = [
        "contact", "contact you", "how can i contact",
        "reservation department", "reservations",
        "phone", "call you", "email", "reach you",
        "whatsapp", "do you have whatsapp",
        "επικοινωνία", "επικοινωνια", "επικοινωνησω", "επικοινωνήσω",
        "πως να επικοινωνησω", "πώς να επικοινωνήσω",
        "τηλέφωνο", "τηλεφωνο", "κρατήσεις", "κρατησεις", "κρατησεων",
        "contattare", "contatto", "telefono", "whatsapp",
        "contactar", "contacto", "telefone", "whatsapp",
    ]

    return contains_any(text, keywords)


def is_availability_request(user_message: str) -> bool:
    text = normalize_text(user_message)

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
        "esta tarde", "esta manhã", "esta manha",
    ]

    return contains_any(text, keywords)


def is_time_comparison(user_message: str) -> bool:
    text = normalize_text(user_message)

    morning_words = [
        "morning", "this morning",
        "πρωί", "πρωι",
        "mattina", "questa mattina",
        "manhã", "manha", "esta manhã", "esta manha",
    ]

    sunset_words = [
        "sunset", "evening",
        "ηλιοβασίλεμα", "ηλιοβασιλεμα", "απόγευμα", "απογευμα",
        "tramonto", "sera", "stasera",
        "pôr do sol", "por do sol", "fim da tarde", "noite",
    ]

    return contains_any(text, morning_words) and contains_any(text, sunset_words)


def is_followup(user_message: str) -> bool:
    text = normalize_text(user_message)

    exact_followups = {
        "yes", "yes please", "ok", "okay", "sure", "please",
        "tell me more", "go ahead", "continue",
        "ναι", "οκ", "εντάξει", "ενταξει", "συνέχισε", "συνεχισε",
        "si", "va bene", "continua",
        "sim", "claro", "continue",
    }

    if matches_any(text, exact_followups):
        return True

    followup_patterns = [
        r"^and\b",
        r"^and for\b",
        r"^what about\b",
        r"^how about\b",
        r"^for the\b",
        r"^what about the\b",
        r"^και\b",
        r"^και για\b",
        r"^τι γίνεται με\b",
        r"^τι γινεται με\b",
        r"^e per\b",
        r"^e per il\b",
        r"^e per la\b",
        r"^che mi dici di\b",
        r"^e para\b",
        r"^e quanto a\b",
        r"^e sobre\b",
    ]

    return any(re.search(pattern, text) for pattern in followup_patterns)


def is_best_choice_question(user_message: str) -> bool:
    text = normalize_text(user_message)

    keywords = [
        "which is the best",
        "which one is the best",
        "which is better",
        "which one is better",
        "what do you recommend",
        "what would you recommend",
        "best option",
        "best for us",
        "ποιο είναι το καλύτερο",
        "ποιο ειναι το καλυτερο",
        "ποιο είναι καλύτερο",
        "ποιο ειναι καλυτερο",
        "τι προτείνεις",
        "τι προτεινεις",
        "τι προτείνετε",
        "τι προτεινετε",
        "qual è il migliore",
        "qual e il migliore",
        "qual è meglio",
        "qual e meglio",
        "cosa consigli",
        "qual é o melhor",
        "qual e o melhor",
        "qual é melhor",
        "qual e melhor",
        "o que recomenda",
        "o que você recomenda",
        "o que voce recomenda",
    ]

    return contains_any(text, keywords)


def is_capacity_request(user_message: str) -> bool:
    text = normalize_text(user_message)

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
        "how many guests",
        "how many people",
        "max guests",
        "maximum guests",
        "max people",
        "maximum people",
        "maximum capacity",
        "max capacity",
        "capacity",
        "up to how many",
        "how many can join",
        "how many passengers",
        "πόσες θέσεις",
        "ποση διαθεσιμοτητα",
        "πόση διαθεσιμότητα",
        "πόσα άτομα μένουν",
        "ποσα ατομα μενουν",
        "πόσα άτομα",
        "ποσα ατομα",
        "μέγιστη χωρητικότητα",
        "μεγιστη χωρητικοτητα",
        "χωρητικότητα",
        "χωρητικοτητα",
        "μέχρι πόσα άτομα",
        "μεχρι ποσα ατομα",
        "quanti posti",
        "posti disponibili",
        "quanti ospiti",
        "quante persone",
        "capacità",
        "capacita",
        "capienza massima",
        "massimo numero di persone",
        "quantos lugares",
        "lugares disponíveis",
        "lugares disponiveis",
        "vagas disponíveis",
        "vagas disponiveis",
        "quantos hóspedes",
        "quantos hospedes",
        "quantas pessoas",
        "capacidade",
        "capacidade máxima",
        "capacidade maxima",
        "máximo de pessoas",
        "maximo de pessoas",
    ]

    return contains_any(text, keywords)


def is_multi_capacity_request(user_message: str) -> bool:
    text = normalize_text(user_message)

    keywords = [
        "all available vessel",
        "all available vessels",
        "all vessels",
        "all available cruises",
        "all available tours",
        "all available options",
        "all available boats",
        "όλα τα σκάφη",
        "ολα τα σκαφη",
        "όλα τα διαθέσιμα σκάφη",
        "ολα τα διαθεσιμα σκαφη",
        "όλες οι διαθέσιμες επιλογές",
        "ολες οι διαθεσιμες επιλογες",
        "tutte le barche",
        "tutte le crociere disponibili",
        "tutte le opzioni disponibili",
        "todos os barcos",
        "todos os cruzeiros disponíveis",
        "todos os cruzeiros disponiveis",
        "todas as opções disponíveis",
        "todas as opcoes disponiveis",
    ]

    return contains_any(text, keywords)


def is_sunset_question(user_message: str) -> bool:
    text = normalize_text(user_message)

    keywords = [
        "will we see the sunset",
        "see the sunset onboard",
        "watch the sunset onboard",
        "sunset onboard",
        "do we see the sunset",
        "θα δούμε το ηλιοβασίλεμα",
        "θα δουμε το ηλιοβασιλεμα",
        "βλέπουμε το ηλιοβασίλεμα",
        "βλεπουμε το ηλιοβασιλεμα",
        "vedremo il tramonto",
        "si vede il tramonto",
        "vamos ver o pôr do sol",
        "vamos ver o por do sol",
        "ver o pôr do sol",
        "ver o por do sol",
    ]

    return contains_any(text, keywords)

def is_pregnancy_question(message: str) -> bool:
    text = message.lower()

    keywords = [
        "pregnant",
        "pregnancy",
        "έγκυος",
        "εγκυος",
        "gravidanza",
        "grávida",
        "gravida",
    ]

    return any(word in text for word in keywords)