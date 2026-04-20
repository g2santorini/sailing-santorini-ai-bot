from typing import Any, Dict, List, Optional

from app.services.clarification_builder import (
    build_availability_guidance_reply,
    build_clarification_reply,
)
from app.services.conversation_state import (
    clear_state,
    create_empty_state,
    has_pending_action,
    is_affirmative_followup,
    set_pending_action,
    set_active_topic,
    update_state_with_new_info,
)
from app.services.date_detector import detect_date
from app.services.message_type_detector import detect_message_type
from app.services.missing_info_detector import detect_missing_info
from app.services.tour_detector import detect_tour_key


COMPARISON_FOLLOWUP_PHRASES = [
    "what about",
    "and what about",
    "how about",
    "and",
]


NON_AVAILABILITY_ACTIVE_TOPICS = {
    "drinks",
    "food",
    "inclusions",
    "pickup",
    "meeting_point",
    "policies",
    "pregnancy",
    "accessibility",
    "comparison",
    "recommendation",
    "pricing",
    "general_info",
}


def detect_period(user_message: str) -> Optional[str]:
    text = (user_message or "").lower()

    if "morning" in text:
        return "morning"

    if any(word in text for word in ["sunset", "afternoon", "evening", "tonight"]):
        return "sunset"

    return None


def extract_comparison_candidates(
    user_message: str,
    detected_tour: Optional[str],
    existing_candidates: Optional[List[str]] = None,
) -> List[str]:
    text = (user_message or "").lower()
    candidates: List[str] = list(existing_candidates or [])

    known_tours = {
        "red": "red",
        "diamond": "diamond",
        "gems": "gems",
        "platinum": "platinum",
        "emily": "emily",
        "ferretti 55": "ferretti_55",
        "ferretti 731": "ferretti_731",
        "lagoon 380": "lagoon_380_400",
        "lagoon 400": "lagoon_380_400",
    }

    for label, key in known_tours.items():
        if label in text and key not in candidates:
            candidates.append(key)

    if detected_tour and detected_tour not in candidates:
        candidates.append(detected_tour)

    return candidates


def is_comparison_followup(
    user_message: str,
    state: Optional[Dict[str, Any]],
    detected_tour: Optional[str],
) -> bool:
    if not state:
        return False

    if state.get("pending_action") not in {"comparison", "recommendation"}:
        return False

    text = (user_message or "").strip().lower()

    if detected_tour:
        return True

    return any(text.startswith(phrase) for phrase in COMPARISON_FOLLOWUP_PHRASES)


def should_continue_active_topic(
    user_message: str,
    state: Optional[Dict[str, Any]],
    detected_date: Optional[str],
    detected_time: Optional[str],
) -> bool:
    if not state:
        return False

    active_topic = state.get("active_topic")
    if active_topic not in NON_AVAILABILITY_ACTIVE_TOPICS:
        return False

    message_type = detect_message_type(user_message)

    if message_type != "incomplete_message":
        return False

    if detected_date or detected_time:
        return False

    return True


def route_message(
    user_message: str,
    state: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    current_state = state or create_empty_state()

    detected_date = detect_date(user_message)
    detected_tour = detect_tour_key(user_message)
    detected_time = detect_period(user_message)

    # --------------------------------------------------
    # 1. Pending flow always wins
    # --------------------------------------------------
    if has_pending_action(current_state):
        updated_state = update_state_with_new_info(
            current_state,
            tour=detected_tour,
            date=detected_date,
            time=detected_time,
        )

        pending_action = updated_state.get("pending_action")

        if pending_action == "availability":
            final_date = updated_state.get("pending_date")
            final_tour = updated_state.get("pending_tour")
            final_time = updated_state.get("pending_time")

            missing = detect_missing_info(
                message_type="availability_request",
                date=final_date,
                tour=final_tour,
                time=final_time,
            )

            if missing:
                return {
                    "action": "clarify",
                    "reply": build_clarification_reply(missing),
                    "state": updated_state,
                    "message_type": "availability_request",
                    "date": final_date,
                    "tour": final_tour,
                    "time": final_time,
                    "missing": missing,
                }

            return {
                "action": "continue_pending",
                "reply": None,
                "state": clear_state(),
                "message_type": "availability_request",
                "date": final_date,
                "tour": final_tour,
                "time": final_time,
                "missing": [],
            }

        if pending_action in {"comparison", "recommendation"}:
            comparison_candidates = extract_comparison_candidates(
                user_message=user_message,
                detected_tour=detected_tour,
                existing_candidates=updated_state.get("comparison_candidates") or [],
            )

            updated_state["comparison_candidates"] = comparison_candidates

            return {
                "action": "continue_comparison",
                "reply": None,
                "state": updated_state,
                "message_type": pending_action,
                "date": detected_date,
                "tour": detected_tour,
                "time": detected_time,
                "missing": [],
                "comparison_candidates": comparison_candidates,
            }

    # --------------------------------------------------
    # 2. Fresh detection
    # --------------------------------------------------
    message_type = detect_message_type(user_message)

    # --------------------------------------------------
    # 3. Continue active non-availability topic
    # --------------------------------------------------
    if should_continue_active_topic(
        user_message=user_message,
        state=current_state,
        detected_date=detected_date,
        detected_time=detected_time,
    ):
        new_state = update_state_with_new_info(
            current_state,
            tour=detected_tour,
            date=detected_date,
            time=detected_time,
        )

        return {
            "action": "continue_active_topic",
            "reply": None,
            "state": new_state,
            "message_type": current_state.get("active_topic") or "general_info",
            "date": detected_date or current_state.get("active_date"),
            "tour": detected_tour or current_state.get("active_tour"),
            "time": detected_time or current_state.get("active_time"),
            "missing": [],
            "active_topic": current_state.get("active_topic"),
        }

    # --------------------------------------------------
    # 4. Comparison follow-up without losing context
    # --------------------------------------------------
    if is_comparison_followup(user_message, current_state, detected_tour):
        comparison_candidates = extract_comparison_candidates(
            user_message=user_message,
            detected_tour=detected_tour,
            existing_candidates=current_state.get("comparison_candidates") or [],
        )

        new_state = set_pending_action(
            current_state,
            action=current_state.get("pending_action") or "comparison",
            comparison_candidates=comparison_candidates,
        )
        new_state = set_active_topic(
            new_state,
            topic="comparison",
            tour=detected_tour,
            date=detected_date,
            time=detected_time,
        )

        return {
            "action": "continue_comparison",
            "reply": None,
            "state": new_state,
            "message_type": "comparison_request",
            "date": detected_date,
            "tour": detected_tour,
            "time": detected_time,
            "missing": [],
            "comparison_candidates": comparison_candidates,
            "active_topic": "comparison",
        }

    # --------------------------------------------------
    # 5. Incomplete / short follow-up without pending state
    # --------------------------------------------------
    if message_type == "incomplete_message":
        if detected_date and not detected_tour:
            return {
                "action": "clarify",
                "reply": build_availability_guidance_reply(date=detected_date),
                "state": current_state,
                "message_type": message_type,
                "date": detected_date,
                "tour": detected_tour,
                "time": detected_time,
                "missing": ["tour"],
            }

        if detected_tour and not detected_date:
            comparison_candidates = current_state.get("comparison_candidates") or []
            if comparison_candidates:
                new_candidates = extract_comparison_candidates(
                    user_message=user_message,
                    detected_tour=detected_tour,
                    existing_candidates=comparison_candidates,
                )
                new_state = set_pending_action(
                    current_state,
                    action="comparison",
                    comparison_candidates=new_candidates,
                )
                new_state = set_active_topic(
                    new_state,
                    topic="comparison",
                    tour=detected_tour,
                    date=detected_date,
                    time=detected_time,
                )
                return {
                    "action": "continue_comparison",
                    "reply": None,
                    "state": new_state,
                    "message_type": "comparison_request",
                    "date": detected_date,
                    "tour": detected_tour,
                    "time": detected_time,
                    "missing": [],
                    "comparison_candidates": new_candidates,
                    "active_topic": "comparison",
                }

            active_topic = current_state.get("active_topic")
            if active_topic in NON_AVAILABILITY_ACTIVE_TOPICS:
                new_state = update_state_with_new_info(
                    current_state,
                    tour=detected_tour,
                    date=detected_date,
                    time=detected_time,
                )
                return {
                    "action": "continue_active_topic",
                    "reply": None,
                    "state": new_state,
                    "message_type": active_topic,
                    "date": detected_date or current_state.get("active_date"),
                    "tour": detected_tour or current_state.get("active_tour"),
                    "time": detected_time or current_state.get("active_time"),
                    "missing": [],
                    "active_topic": active_topic,
                }

            return {
                "action": "clarify",
                "reply": build_availability_guidance_reply(tour=detected_tour),
                "state": current_state,
                "message_type": message_type,
                "date": detected_date,
                "tour": detected_tour,
                "time": detected_time,
                "missing": ["date"],
            }

        if is_affirmative_followup(user_message):
            active_topic = current_state.get("active_topic")
            if active_topic in NON_AVAILABILITY_ACTIVE_TOPICS:
                return {
                    "action": "continue_active_topic",
                    "reply": None,
                    "state": current_state,
                    "message_type": active_topic,
                    "date": current_state.get("active_date"),
                    "tour": current_state.get("active_tour"),
                    "time": current_state.get("active_time"),
                    "missing": [],
                    "active_topic": active_topic,
                }

            return {
                "action": "clarify",
                "reply": "Just let me know your preferred date and cruise, and I’ll guide you from there.",
                "state": current_state,
                "message_type": message_type,
                "date": detected_date,
                "tour": detected_tour,
                "time": detected_time,
                "missing": [],
            }

        return {
            "action": "clarify",
            "reply": "Could you tell me a little more so I can help you properly?",
            "state": current_state,
            "message_type": message_type,
            "date": detected_date,
            "tour": detected_tour,
            "time": detected_time,
            "missing": [],
        }

    # --------------------------------------------------
    # 6. Availability flow
    # --------------------------------------------------
    if message_type == "availability_request":
        missing = detect_missing_info(
            message_type=message_type,
            date=detected_date,
            tour=detected_tour,
            time=detected_time,
        )

        if missing:
            new_state = set_pending_action(
                current_state,
                action="availability",
                tour=detected_tour,
                date=detected_date,
                time=detected_time,
            )

            return {
                "action": "clarify",
                "reply": build_clarification_reply(missing),
                "state": new_state,
                "message_type": message_type,
                "date": detected_date,
                "tour": detected_tour,
                "time": detected_time,
                "missing": missing,
                "active_topic": "availability",
            }

        return {
            "action": "availability_ready",
            "reply": None,
            "state": clear_state(),
            "message_type": message_type,
            "date": detected_date,
            "tour": detected_tour,
            "time": detected_time,
            "missing": [],
            "active_topic": "availability",
        }

    # --------------------------------------------------
    # 7. Comparison
    # --------------------------------------------------
    if message_type == "comparison_request":
        comparison_candidates = extract_comparison_candidates(
            user_message=user_message,
            detected_tour=detected_tour,
            existing_candidates=[],
        )

        new_state = set_pending_action(
            current_state,
            action="comparison",
            comparison_candidates=comparison_candidates,
        )
        new_state = set_active_topic(
            new_state,
            topic="comparison",
            tour=detected_tour,
            date=detected_date,
            time=detected_time,
        )

        return {
            "action": "comparison_answer",
            "reply": None,
            "state": new_state,
            "message_type": message_type,
            "date": detected_date,
            "tour": detected_tour,
            "time": detected_time,
            "missing": [],
            "comparison_candidates": comparison_candidates,
            "active_topic": "comparison",
        }

    # --------------------------------------------------
    # 8. Recommendation
    # --------------------------------------------------
    if message_type == "recommendation_request":
        comparison_candidates = extract_comparison_candidates(
            user_message=user_message,
            detected_tour=detected_tour,
            existing_candidates=[],
        )

        new_state = set_pending_action(
            current_state,
            action="recommendation",
            comparison_candidates=comparison_candidates,
        )
        new_state = set_active_topic(
            new_state,
            topic="recommendation",
            tour=detected_tour,
            date=detected_date,
            time=detected_time,
        )

        return {
            "action": "recommendation_answer",
            "reply": None,
            "state": new_state,
            "message_type": message_type,
            "date": detected_date,
            "tour": detected_tour,
            "time": detected_time,
            "missing": [],
            "comparison_candidates": comparison_candidates,
            "active_topic": "recommendation",
        }

    # --------------------------------------------------
    # 9. Booking intent only
    # --------------------------------------------------
    if message_type == "booking_intent_only":
        if detected_date or detected_tour or detected_time:
            missing = detect_missing_info(
                message_type="availability_request",
                date=detected_date,
                tour=detected_tour,
                time=detected_time,
            )

            if missing:
                new_state = set_pending_action(
                    current_state,
                    action="availability",
                    tour=detected_tour,
                    date=detected_date,
                    time=detected_time,
                )

                return {
                    "action": "clarify",
                    "reply": build_clarification_reply(missing),
                    "state": new_state,
                    "message_type": "availability_request",
                    "date": detected_date,
                    "tour": detected_tour,
                    "time": detected_time,
                    "missing": missing,
                    "active_topic": "availability",
                }

            return {
                "action": "availability_ready",
                "reply": None,
                "state": clear_state(),
                "message_type": "availability_request",
                "date": detected_date,
                "tour": detected_tour,
                "time": detected_time,
                "missing": [],
                "active_topic": "availability",
            }

        return {
            "action": "booking_guidance",
            "reply": "I’ll be happy to help. Just let me know your preferred date and cruise, and I’ll guide you with the next step.",
            "state": current_state,
            "message_type": message_type,
            "date": detected_date,
            "tour": detected_tour,
            "time": detected_time,
            "missing": [],
        }

    # --------------------------------------------------
    # 10. Default = general answer
    # --------------------------------------------------
    new_state = set_active_topic(
        current_state,
        topic="general_info",
        tour=detected_tour,
        date=detected_date,
        time=detected_time,
    )

    return {
        "action": "general_answer",
        "reply": None,
        "state": new_state,
        "message_type": message_type,
        "date": detected_date,
        "tour": detected_tour,
        "time": detected_time,
        "missing": [],
        "active_topic": "general_info",
    }