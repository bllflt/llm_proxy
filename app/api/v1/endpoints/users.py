"""User endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/users/me", response_model=UserResponse, tags=["users"])
async def get_current_user_info(
    user_id: Annotated[str, Depends(get_current_user)],
) -> UserResponse:
    """
    Get current user information.

    Requires JWT authentication.

    Args:
        user_id: Current user ID from JWT token

    Returns:
        User information
    """
    return UserResponse(user_id=user_id, username=f"user_{user_id}")
