"""FastAPI application configuration."""

import logging
from typing import Literal

from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=find_dotenv(), case_sensitive=True)

    # Application
    DEBUG: bool = False
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # JWT
    JWT_SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Gemini
    GEMINI_API_KEY: str = ""
    RESULT_API_ENDPOINT: str = "http://localhost:2000/api/v1/ai/work/caption/complete"
    IMAGE_UPLOAD_ENDPOINT: str = "http://localhost:2000/characters/upload-image"
    HTTP_TIMEOUT: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # MCP (Model Context Protocol)
    MCP_ENDPOINT: str = ""

    # Chat
    CHAT_HISTORY_EXPIRE_MINUTES: int = 1440  # 24 hours
    CHAT_HISTORY_PREFIX: str = "chat"
    CHAT_MODEL: str = "gemini-2.5-flash"

    STATS_PREFIX: str = "stats"

settings = Settings()

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)
