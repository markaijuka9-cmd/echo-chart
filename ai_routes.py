
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ai_council import council
from auth import get_current_user
from models import User

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


class AIMessage(BaseModel):
    message: str = Field(min_length=1, max_length=5000)


class AIResponse(BaseModel):
    answer: str


@router.post("/chat", response_model=AIResponse)
async def chat_with_ai(
    data: AIMessage,
    current_user: User = Depends(get_current_user),
):
    answer = await council.answer(data.message)

    return AIResponse(answer=answer)
