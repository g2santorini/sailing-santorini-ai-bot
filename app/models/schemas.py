from pydantic import BaseModel


class Message(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str