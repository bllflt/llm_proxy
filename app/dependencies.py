"""FastAPI dependencies for authentication and business logic."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import get_subject_from_token

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    """
    Dependency to extract and verify the current user from JWT token.

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        User identifier (subject) from token

    Raises:
        HTTPException: If token is invalid or missing
    """
    try:
        user_id = get_subject_from_token(credentials.credentials)
        return user_id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
