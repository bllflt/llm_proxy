"""Pydantic schemas for authentication."""

from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    """Request model for token generation."""

    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class Token(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str
