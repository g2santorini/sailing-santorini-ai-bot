from app.services.availability_search import find_available_tours
from app.services.multi_reply_builder import build_multi_availability_reply

results = find_available_tours("2026-06-16", "morning")
reply = build_multi_availability_reply(results, "16 June", "morning")
print(reply)