from typing import List, Optional


def build_clarification_reply(missing_fields: List[str]) -> str:
    missing_set = set(missing_fields)

    if missing_set == {"date", "tour"}:
        return "Just let me know which cruise you’re interested in and your preferred date, and I’ll check availability for you."

    if missing_set == {"date"}:
        return "For which date would you like me to check?"

    if missing_set == {"tour"}:
        return "Which cruise would you like me to check for you?"

    if missing_set == {"time"}:
        return "Would you prefer the morning or the sunset cruise?"

    if missing_set == {"date", "time"}:
        return "Just let me know your preferred date and whether you’re interested in the morning or sunset cruise, and I’ll check it for you."

    if missing_set == {"tour", "time"}:
        return "Just let me know which cruise you’re interested in and whether you prefer morning or sunset, and I’ll guide you from there."

    if missing_set == {"date", "tour", "time"}:
        return "Just let me know your preferred date, which cruise you’re interested in, and whether you prefer morning or sunset, and I’ll help you from there."

    return "Could you share a little more detail so I can help you properly?"


def build_availability_guidance_reply(
    date: Optional[str] = None,
    tour: Optional[str] = None,
) -> str:
    if date and not tour:
        return f"Just let me know which cruise you’re interested in and I’ll check availability for {date}."

    if tour and not date:
        return f"Just let me know your preferred date and I’ll check availability for the {tour} cruise."

    return "If you’d like, send me your preferred date and cruise and I’ll check availability for you."