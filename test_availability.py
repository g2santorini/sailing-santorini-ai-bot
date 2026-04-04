from app.services.availability_service import get_day_availability
from app.services.tour_mapping import TOUR_OPTIONS

# παίρνουμε το tour από το mapping
tour = TOUR_OPTIONS["red_morning"]

result = get_day_availability(
    tour["product_id"],
    tour["product_option_id"],
    "2026-04-06"
)

print(tour["reply_label"])
print(result)