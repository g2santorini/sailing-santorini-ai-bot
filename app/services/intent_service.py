import re


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


def is_contact_request(user_message: str) -> bool:
    text = user_message.lower()

    keywords = [
        "contact", "contact you", "how can i contact",
        "reservation department", "reservations",
        "phone", "call you", "email", "reach you",
        "whatsapp", "do you have whatsapp",
        "επικοινωνία", "επικοινωνησω", "επικοινωνήσω", "πως να επικοινωνησω", "πώς να επικοινωνήσω",
        "τηλέφωνο", "τηλεφωνο", "κρατήσεις", "κρατησεων", "whatsapp",
        "contattare", "contatto", "telefono", "whatsapp",
        "contactar", "contacto", "telefone", "whatsapp"
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


def is_followup(user_message: str) -> bool:
    text = user_message.lower().strip()

    exact_followups = {
        "yes", "yes please", "ok", "okay", "sure", "please",
        "tell me more", "go ahead", "continue",
        "ναι", "οκ", "εντάξει", "συνέχισε",
        "si", "va bene", "continua",
        "sim", "claro", "continue"
    }

    if text in exact_followups:
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
        r"^e sobre\b"
    ]

    return any(re.search(pattern, text) for pattern in followup_patterns)


def is_best_choice_question(user_message: str) -> bool:
    text = user_message.lower().strip()

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
        "o que voce recomenda"
    ]

    return any(k in text for k in keywords)


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
        "πόση διαθεσιμότητα",
        "πόσα άτομα μένουν",
        "πόσα άτομα",
        "μέγιστη χωρητικότητα",
        "χωρητικότητα",
        "μέχρι πόσα άτομα",
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
        "vagas disponíveis",
        "quantos hóspedes",
        "quantas pessoas",
        "capacidade",
        "capacidade máxima",
        "máximo de pessoas",
        "maximo de pessoas"
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