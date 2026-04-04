from fastapi import APIRouter
from app.models.schemas import Message, ChatResponse
from app.services.openai_service import get_ai_reply
from app.services.knowledge_service import load_company_knowledge

router = APIRouter()


@router.post("/")
def chat(data: Message):
    knowledge = load_company_knowledge()

    prompt = f"""
You are a professional assistant for Sunset Oia Sailing Cruises in Santorini.

Instructions:
- Answer clearly and politely
- Keep answers short and useful
- Use the company knowledge below
- If you don’t know something, say it honestly
- When relevant, suggest booking

Company knowledge:
{knowledge}

Customer question:
{data.message}
"""

    reply = get_ai_reply(prompt)

    return ChatResponse(reply=reply)