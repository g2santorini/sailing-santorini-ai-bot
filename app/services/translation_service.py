def get_text(key: str, language: str, booking_link: str, whatsapp_link: str) -> str:
    translations = {
        "empty_reply": (
            "Hello! I’ll be happy to help you with our cruises in Santorini."
        ),
        "pregnancy_reply": (
            f"In most cases, pregnant guests may join, but it depends on the stage of pregnancy "
            f"and how comfortable you feel during the cruise.\n\n"
            f"For safety, we kindly recommend contacting us on WhatsApp so we can guide you properly:\n"
            f"{whatsapp_link}"
        ),
        "greeting_reply": (
            "Hello and welcome! I’ll be happy to help you with our cruises in Santorini. "
            "Feel free to ask me about availability, prices, shared or private options."
        ),
        "discount_reply": (
            f"For special rate requests, please contact us via WhatsApp:\n{whatsapp_link}"
        ),
        "cruise_passenger_reply": (
            f"For cruise ship guests, we kindly recommend contacting us directly via WhatsApp "
            f"so we can assist you based on your ship schedule:\n{whatsapp_link}"
        ),
        "contact_reply": (
            f"You can contact our reservations team directly on WhatsApp and we’ll be happy to assist you:\n"
            f"{whatsapp_link}"
        ),
        "irrelevant_reply": (
            "I may not have fully understood your question, but I’ll be happy to help 🙂\n\n"
            "Could you please clarify if you are asking about the cruise experience?"
        ),
        "availability_fallback": (
            f"The best way to check the latest availability is through our booking page:\n"
            f"{booking_link}\n\n"
            "Simply select your preferred date and you’ll see all available options instantly.\n\n"
            f"For any clarification, feel free to contact us on WhatsApp:\n{whatsapp_link}"
        ),
        "spots_fallback": (
            "I’m sorry, I could not identify the exact cruise from the previous message. "
            "Please tell me the cruise name and date, and I’ll gladly check the number of available spots for you."
        ),
        "booking_details_reply": (
            f"I can’t see personal booking details here. Please check your booking confirmation, "
            f"or contact us on WhatsApp and we’ll gladly assist you directly:\n{whatsapp_link}"
        ),
        "whatsapp_uncertain_reply": (
            f"I don’t have that exact detail here, but our team can assist you directly on WhatsApp:\n"
            f"{whatsapp_link}"
        ),
        "morning_unavailable_reply": (
            "Morning cruises are available only until 24 October 2026, so the requested morning cruise "
            "is not available on that date.\n\n"
            "During that period, only sunset cruises are operating.\n\n"
            f"You can check availability here:\n{booking_link}\n\n"
            f"For any clarification, feel free to contact us on WhatsApp:\n{whatsapp_link}"
        ),
        "sunset_only_reply": (
            "During that period, we operate sunset cruises only.\n\n"
            "The sunset cruise is a beautiful experience, as you can enjoy the famous Santorini sunset from the sea.\n\n"
            f"You can check availability here:\n{booking_link}\n\n"
            f"If you need help choosing, feel free to contact us on WhatsApp:\n{whatsapp_link}"
        ),
        "off_season_reply": (
            "Our cruises are not operating during that period, as the season is closed.\n\n"
            "We resume from 15 March 2027.\n\n"
            f"You can check available dates here:\n{booking_link}\n\n"
            f"For any clarification, feel free to contact us on WhatsApp:\n{whatsapp_link}"
        ),
        "sunset_reply": (
            "Yes, you will enjoy the sunset from onboard the catamaran. "
            "Our sunset cruises are timed so you can watch the famous Santorini sunset directly from the sea."
        ),
        "weather_reply": (
            "Weather conditions can change quickly in Santorini 🙂 "
            "Our cruises take place inside the caldera, where the sea is usually quite calm. "
            "In case of unsafe conditions, cruises are cancelled only under official Port Authority instructions, "
            "and guests are offered a reschedule or full refund."
        ),
        "food_reply": (
            "A freshly prepared BBQ meal is included on all cruises. "
            "Vegetarian options are also available."
        ),
        "drinks_reply": (
            "Complimentary drinks are included on board, such as white wine, soft drinks and water. "
            "Beer is included in selected cruises, and Diamond also includes one cocktail per guest."
        ),
        "transfer_reply": (
            "Transfers are included in most cruise options, except for no-transfer options. "
            "If you tell me which cruise you are interested in, I can guide you more precisely."
        ),
        "route_reply": (
            "Our cruises usually include stops for swimming, snorkeling and sightseeing around the Santorini caldera. "
            "Exact stops may vary depending on weather conditions."
        ),
    }

    return translations.get(key, "")


def translate_availability_reply(reply_text: str, language: str) -> str:
    return reply_text