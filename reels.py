
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from database import get_db
from models import Reel, User

router = APIRouter(prefix="/reels", tags=["Reels"])


class ReelCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    video_url: HttpUrl


class ReelResponse(BaseModel):
    id: int
    title: str
    video_url: str
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[ReelResponse])
async def list_reels(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    limit = max(1, min(limit, 50))

    result = await db.execute(
        select(Reel)
        .order_by(Reel.id.desc())
        .limit(limit)
    )

    return result.scalars().all()


@router.post("/", response_model=ReelResponse, status_code=201)
async def create_reel(
    data: ReelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    title = data.title.strip()

    if not title:
        raise HTTPException(
            status_code=400,
            detail="Reel title cannot be empty.",
        )

    reel = Reel(
        title=title,
        video_url=str(data.video_url),
        user_id=current_user.id,
    )

    db.add(reel)
    await db.flush()
    await db.refresh(reel)

    return reel
