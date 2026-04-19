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
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "hi there",
        "hello there",
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
        "will we see sunset",
    ]

    return any(k in message for k in keywords)


def is_discount_request(user_message: str) -> bool:
    text = normalize_text(user_message)

    keywords = [
        "discount",
        "better price",
        "best price",
        "special price",
        "cheaper",
        "deal",
    ]

    return contains_any(text, keywords)


def is_contact_request(user_message: str) -> bool:
    text = normalize_text(user_message)

    keywords = [
        "contact",
        "contact you",
        "how can i contact",
        "reservation department",
        "reservations",
        "phone",
        "call you",
        "email",
        "reach you",
        "whatsapp",
        "do you have whatsapp",
    ]

    return contains_any(text, keywords)


def is_availability_request(user_message: str) -> bool:
    text = normalize_text(user_message)

    keywords = [
        "availability",
        "available",
        "do you have availability",
        "is there availability",
        "any availability",
        "what is available",
        "what tours are available",
        "today",
        "tomorrow",
        "tonight",
        "this afternoon",
        "this evening",
        "this morning",
        "for today",
        "for tomorrow",
    ]

    return contains_any(text, keywords)


def is_time_comparison(user_message: str) -> bool:
    text = normalize_text(user_message)

    morning_words = [
        "morning",
        "this morning",
    ]

    sunset_words = [
        "sunset",
        "evening",
        "afternoon",
        "this afternoon",
        "this evening",
        "tonight",
    ]

    return contains_any(text, morning_words) and contains_any(text, sunset_words)


def is_followup(user_message: str) -> bool:
    text = normalize_text(user_message)

    exact_followups = {
        "yes",
        "yes please",
        "ok",
        "okay",
        "sure",
        "please",
        "tell me more",
        "go ahead",
        "continue",
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
    ]

    return contains_any(text, keywords)


def is_pregnancy_question(message: str) -> bool:
    text = message.lower()

    keywords = [
        "pregnant",
        "pregnancy",
    ]

    return any(word in text for word in keywords)