"""User-related request/response schemas."""

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """User response model."""

    user_id: str
    username: str


class UserUpdate(BaseModel):
    """User update model."""

    username: str = Field(..., min_length=1)
