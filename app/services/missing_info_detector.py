from typing import List, Optional


def detect_missing_info(
    message_type: str,
    date: Optional[str],
    tour: Optional[str],
    time: Optional[str],
) -> List[str]:
    """
    Returns list of missing fields:
    ["date", "tour", "time"]
    """

    missing = []

    # 👉 Μας ενδιαφέρει κυρίως για availability
    if message_type == "availability_request":

        # date είναι σχεδόν πάντα required
        if not date:
            missing.append("date")

        # tour μπορεί να είναι optional αν δείξουμε multiple options
        # αλλά στην αρχή το κρατάμε required για καθαρό flow
        if not tour:
            missing.append("tour")

        # time (morning/sunset) optional για τώρα
        # μπορούμε να το βάλουμε μετά πιο strict
        # if not time:
        #     missing.append("time")

    return missing