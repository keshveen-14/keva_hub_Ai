from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends

from .. import models, ai_service
from ..deps import get_current_user

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None


@router.post("/message")
def chat(payload: ChatRequest, current_user: models.Employee = Depends(get_current_user)):
    history = [h.model_dump() for h in payload.history] if payload.history else []
    reply = ai_service.chatbot_reply(payload.message, history)
    return {"reply": reply}
