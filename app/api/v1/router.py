"""v1 API router."""

from fastapi import APIRouter

from app.api.v1.endpoints import captions, chat, health, users

router = APIRouter(prefix="/api/v1")

router.include_router(health.router)
router.include_router(users.router)
router.include_router(captions.router)
router.include_router(chat.router)
