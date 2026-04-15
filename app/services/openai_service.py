from openai import OpenAI
from app.core.config import OPENAI_API_KEY, MODEL_NAME
from app.services.knowledge_service import get_company_knowledge

client = OpenAI(api_key=OPENAI_API_KEY)


def get_ai_reply(user_message: str, history: list[dict] = None) -> str:
    knowledge = get_company_knowledge()

    messages = [
        {
            "role": "system",
            "content": f"""
You are a professional assistant for Sunset Oia Sailing Cruises.

{knowledge}
"""
        }
    ]

    # 👉 history (αν υπάρχει)
    if history:
        for msg in history:
            messages.append(msg)

    # 👉 user message
    messages.append({
        "role": "user",
        "content": user_message
    })

    response = client.responses.create(
        model=MODEL_NAME,
        input=messages
    )

    return response.output_text