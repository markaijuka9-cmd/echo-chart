
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import Column, DateTime, Integer, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from database import Base, get_db
from models import User

router = APIRouter(prefix="/news", tags=["News"])


class NewsItem(Base):
    __tablename__ = "news_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(250), nullable=False)
    summary = Column(Text, default="", nullable=False)
    source = Column(String(150), default="", nullable=False)
    article_url = Column(String(1000), nullable=False)
    region = Column(String(10), default="UG", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class NewsCreate(BaseModel):
    title: str = Field(min_length=1, max_length=250)
    summary: str = Field(default="", max_length=5000)
    source: str = Field(default="", max_length=150)
    article_url: HttpUrl
    region: str = Field(default="UG", min_length=2, max_length=10)


class NewsResponse(BaseModel):
    id: int
    title: str
    summary: str
    source: str
    article_url: str
    region: str
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[NewsResponse])
async def list_news(
    region: str = "UG",
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    limit = max(1, min(limit, 50))

    result = await db.execute(
        select(NewsItem)
        .where(NewsItem.region == region.upper())
        .order_by(NewsItem.id.desc())
        .limit(limit)
    )

    return result.scalars().all()


@router.post("/", response_model=NewsResponse, status_code=201)
async def create_news(
    data: NewsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required.",
        )

    item = NewsItem(
        title=data.title.strip(),
        summary=data.summary.strip(),
        source=data.source.strip(),
        article_url=str(data.article_url),
        region=data.region.upper(),
    )

    if not item.title:
        raise HTTPException(status_code=400, detail="Title is required.")

    db.add(item)
    await db.flush()
    await db.refresh(item)

    return item
