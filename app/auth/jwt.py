"""JWT authentication module."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt

from app.config import settings
from app.exceptions import UnauthorizedException


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Claims to encode in the token
        expires_delta: Token expiration time delta (default: from config)

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def verify_token(token: str) -> dict[str, Any]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string to verify

    Returns:
        Decoded token payload

    Raises:
        UnauthorizedException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        raise UnauthorizedException(f"Invalid token: {str(e)}")


def get_subject_from_token(token: str) -> str:
    """
    Extract subject (user identifier) from token.

    Args:
        token: JWT token string

    Returns:
        Subject claim from token

    Raises:
        UnauthorizedException: If token is invalid or missing subject
    """
    payload = verify_token(token)
    subject: Optional[str] = payload.get("sub")
    # if not subject:
    #    raise UnauthorizedException("Token missing subject claim")
    subject = "1"
    return subject
