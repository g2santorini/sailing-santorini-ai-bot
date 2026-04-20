import re
from typing import Literal

MessageType = Literal[
    "availability_request",
    "general_question",
    "recommendation_request",
    "comparison_request",
    "booking_intent_only",
    "incomplete_message",
]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower().strip())


def contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def matches_any(text: str, phrases: set[str]) -> bool:
    return text in phrases


def looks_like_question(text: str) -> bool:
    question_starters = [
        "what",
        "which",
        "who",
        "how",
        "when",
        "where",
        "can",
        "could",
        "do",
        "does",
        "is",
        "are",
        "will",
        "would",
        "should",
    ]
    return text.endswith("?") or any(text.startswith(starter + " ") for starter in question_starters)


def has_date_like_signal(text: str) -> bool:
    month_words = [
        "january", "jan",
        "february", "feb",
        "march", "mar",
        "april", "apr",
        "may",
        "june", "jun",
        "july", "jul",
        "august", "aug",
        "september", "sep", "sept",
        "october", "oct",
        "november", "nov",
        "december", "dec",
    ]

    relative_date_words = [
        "today",
        "tomorrow",
        "tonight",
        "this morning",
        "this afternoon",
        "this evening",
        "next week",
        "next monday",
        "next tuesday",
        "next wednesday",
        "next thursday",
        "next friday",
        "next saturday",
        "next sunday",
    ]

    if contains_any(text, month_words):
        return True

    if contains_any(text, relative_date_words):
        return True

    numeric_date_patterns = [
        r"\b\d{1,2}/\d{1,2}\b",
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
        r"\b\d{1,2}-\d{1,2}\b",
        r"\b\d{1,2}-\d{1,2}-\d{2,4}\b",
        r"\b\d{1,2}\s+(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)\b",
    ]

    return any(re.search(pattern, text) for pattern in numeric_date_patterns)


def is_short_followup(text: str) -> bool:
    short_followups = {
        "yes",
        "yes please",
        "ok",
        "okay",
        "sure",
        "please",
        "go ahead",
        "continue",
        "and",
        "what about",
        "how about",
        "for the morning",
        "for the sunset",
        "morning",
        "sunset",
    }
    return matches_any(text, short_followups)


def detect_message_type(user_message: str) -> MessageType:
    text = normalize_text(user_message)

    if not text:
        return "incomplete_message"

    availability_keywords = [
        "availability",
        "available",
        "spots",
        "spot left",
        "spots left",
        "seats left",
        "places left",
        "how many left",
        "book",
        "booking",
        "reserve",
        "reservation",
        "check availability",
        "is there availability",
        "do you have availability",
        "any availability",
        "what is available",
        "what tours are available",
    ]

    comparison_keywords = [
        "difference",
        "differences",
        "compare",
        "comparison",
        "vs",
        "versus",
        "which is better",
        "which one is better",
        "better than",
        "what is the difference between",
        "what's the difference between",
    ]

    recommendation_keywords = [
        "recommend",
        "recommendation",
        "suggest",
        "suggestion",
        "which is the best",
        "which one is the best",
        "best option",
        "best for us",
        "best for me",
        "which cruise is best",
        "what do you recommend",
        "what would you recommend",
        "worth it",
        "is it worth",
        "better to",
        "should i choose",
        "should we choose",
        "which one should i choose",
        "which one should we choose",
        "what is best for",
        "what would be best for",
        "suitable for us",
        "most suitable",
    ]

    booking_only_keywords = [
        "i want to book",
        "we want to book",
        "i would like to book",
        "we would like to book",
        "how can i book",
        "how do i book",
        "book now",
        "proceed with booking",
    ]

    general_cruise_keywords = [
        "duration",
        "itinerary",
        "route",
        "included",
        "include",
        "pickup",
        "pick up",
        "transfer",
        "food",
        "drinks",
        "towel",
        "towels",
        "swimming",
        "swim",
        "snorkeling",
        "private",
        "shared",
        "catamaran",
        "yacht",
        "port",
        "amoudi",
        "vlychada",
        "sunset",
        "morning",
        "cruise",
        "cruises",
        "tour",
        "tours",
    ]

    # 1) Very short follow-up / incomplete
    if is_short_followup(text):
        return "incomplete_message"

    # 2) Date alone should NOT become availability
    if has_date_like_signal(text) and not contains_any(text, availability_keywords):
        if len(text.split()) <= 6:
            return "incomplete_message"

    # 3) Comparison first
    if contains_any(text, comparison_keywords):
        return "comparison_request"

    # 4) Recommendation next
    if contains_any(text, recommendation_keywords):
        return "recommendation_request"

    # 5) Booking intent without enough operational detail
    if contains_any(text, booking_only_keywords):
        return "booking_intent_only"

    # 6) Availability only with explicit signal
    if contains_any(text, availability_keywords):
        return "availability_request"

    # 7) Super short unclear message
    if len(text.split()) <= 3 and not looks_like_question(text):
        return "incomplete_message"

    # 8) Otherwise treat cruise-related questions as general
    if looks_like_question(text) or contains_any(text, general_cruise_keywords):
        return "general_question"

    # 9) Safe fallback
    return "general_question"