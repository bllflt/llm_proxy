"""Tests for JWT functions."""

import pytest

from app.auth.jwt import create_access_token, get_subject_from_token, verify_token
from app.exceptions import UnauthorizedException


def test_create_access_token() -> None:
    """Test access token creation."""
    data = {"sub": "test_user"}
    token = create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_valid_token() -> None:
    """Test verifying a valid token."""
    data = {"sub": "test_user"}
    token = create_access_token(data)
    payload = verify_token(token)
    assert payload["sub"] == "test_user"


def test_verify_invalid_token() -> None:
    """Test verifying an invalid token."""
    with pytest.raises(UnauthorizedException):
        verify_token("invalid_token")


def test_get_subject_from_token() -> None:
    """Test extracting subject from token."""
    data = {"sub": "test_user_456"}
    token = create_access_token(data)
    subject = get_subject_from_token(token)
    assert subject == "test_user_456"


def test_get_subject_from_invalid_token() -> None:
    """Test extracting subject from invalid token."""
    with pytest.raises(UnauthorizedException):
        get_subject_from_token("invalid_token")
