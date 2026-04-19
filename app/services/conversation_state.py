from typing import Any, Dict, List, Optional


def create_empty_state() -> Dict[str, Optional[Any]]:
    return {
        "pending_action": None,
        "pending_tour": None,
        "pending_date": None,
        "pending_time": None,
        "comparison_candidates": [],
    }


def has_pending_action(state: Optional[Dict[str, Any]]) -> bool:
    if not state:
        return False
    return bool(state.get("pending_action"))


def set_pending_action(
    state: Optional[Dict[str, Any]],
    action: str,
    tour: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None,
    comparison_candidates: Optional[List[str]] = None,
) -> Dict[str, Optional[Any]]:
    new_state = create_empty_state()

    if state:
        new_state.update(state)

    new_state["pending_action"] = action
    new_state["pending_tour"] = tour
    new_state["pending_date"] = date
    new_state["pending_time"] = time
    new_state["comparison_candidates"] = comparison_candidates or []

    return new_state


def update_state_with_new_info(
    state: Optional[Dict[str, Any]],
    tour: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None,
    comparison_candidates: Optional[List[str]] = None,
) -> Dict[str, Optional[Any]]:
    new_state = create_empty_state()

    if state:
        new_state.update(state)

    if tour:
        new_state["pending_tour"] = tour

    if date:
        new_state["pending_date"] = date

    if time:
        new_state["pending_time"] = time

    if comparison_candidates:
        existing = new_state.get("comparison_candidates") or []
        merged = list(dict.fromkeys(existing + comparison_candidates))
        new_state["comparison_candidates"] = merged

    return new_state


def clear_state() -> Dict[str, Optional[Any]]:
    return create_empty_state()


def is_affirmative_followup(message: str) -> bool:
    text = (message or "").strip().lower()

    affirmative_messages = {
        "yes",
        "yes please",
        "yes sure",
        "sure",
        "ok",
        "okay",
        "please",
        "go ahead",
        "continue",
    }

    return text in affirmative_messages