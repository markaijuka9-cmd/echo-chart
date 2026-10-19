
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from database import get_db
from models import Conversation, Message, User

router = APIRouter(prefix="/social", tags=["Messaging"])


class MessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class ConversationRequest(BaseModel):
    user2_id: int


async def get_conversation(
    db: AsyncSession,
    conversation_id: int,
    user_id: int,
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            or_(
                Conversation.user1_id == user_id,
                Conversation.user2_id == user_id,
            ),
        )
    )
    conversation = result.scalar_one_or_none()

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return conversation


@router.post("/conversations")
async def create_conversation(
    data: ConversationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.user2_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot start a conversation with yourself.",
        )

    result = await db.execute(
        select(User).where(
            User.id == data.user2_id,
            User.is_active.is_(True),
        )
    )
    other_user = result.scalar_one_or_none()

    if other_user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    first_id, second_id = sorted(
        [current_user.id, other_user.id]
    )

    result = await db.execute(
        select(Conversation).where(
            Conversation.user1_id == first_id,
            Conversation.user2_id == second_id,
        )
    )
    conversation = result.scalar_one_or_none()

    if conversation is None:
        conversation = Conversation(
            user1_id=first_id,
            user2_id=second_id,
        )
        db.add(conversation)
        await db.flush()
        await db.refresh(conversation)

    return {
        "id": conversation.id,
        "user1_id": conversation.user1_id,
        "user2_id": conversation.user2_id,
        "created_at": conversation.created_at,
    }


@router.get("/conversations")
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Conversation)
        .where(
            or_(
                Conversation.user1_id == current_user.id,
                Conversation.user2_id == current_user.id,
            )
        )
        .order_by(Conversation.id.desc())
    )

    return [
        {
            "id": item.id,
            "user1_id": item.user1_id,
            "user2_id": item.user2_id,
            "created_at": item.created_at,
        }
        for item in result.scalars().all()
    ]


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: int,
    data: MessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_conversation(
        db,
        conversation_id,
        current_user.id,
    )

    content = data.content.strip()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    message = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=content,
    )

    db.add(message)
    await db.flush()
    await db.refresh(message)

    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "sender_id": message.sender_id,
        "content": message.content,
        "created_at": message.created_at,
    }


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_conversation(
        db,
        conversation_id,
        current_user.id,
    )

    limit = max(1, min(limit, 100))

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(limit)
    )

    messages = list(result.scalars().all())
    messages.reverse()

    return [
        {
            "id": item.id,
            "sender_id": item.sender_id,
            "content": item.content,
            "created_at": item.created_at,
        }
        for item in messages
    ]
