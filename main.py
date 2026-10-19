
from contextlib import asynccontextmanager

from fastapi import FastAPI

import models
import news

from auth import router as auth_router
from social import router as social_router
from reels import router as reels_router
from news import router as news_router
from database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


app = FastAPI(
    title="EchoChat API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(social_router)
app.include_router(reels_router)
app.include_router(news_router)


@app.get("/")
async def root():
    return {
        "app": "EchoChat",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "app": "EchoChat",
    }
