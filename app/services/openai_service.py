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

Use the company knowledge below as your main source of truth.

Important reply style rules:
- Keep replies natural, warm, and professional
- Keep replies short, ideally 2 to 4 lines
- Do not sound robotic or too abrupt
- Avoid starting replies with "Yes," or "No," unless absolutely necessary
- Prefer smooth natural phrasing instead of very short broken sentences
- When relevant, gently guide the guest toward the most suitable cruise
- Do not invent details that are not in the knowledge
- If something is uncertain or not clearly available, say so politely

Company knowledge:
{knowledge}
"""
        }
    ]

    if history:
        for msg in history:
            messages.append(msg)

    messages.append({
        "role": "user",
        "content": user_message
    })

    response = client.responses.create(
        model=MODEL_NAME,
        input=messages
    )

    return response.output_text