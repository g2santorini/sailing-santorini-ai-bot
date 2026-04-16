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