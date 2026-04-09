"""Tests for user endpoints."""

from fastapi.testclient import TestClient


def test_get_current_user_authenticated(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Test getting current user with valid token."""
    response = client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "username" in data
    assert data["user_id"] == "test_user_123"


def test_get_current_user_unauthorized(client: TestClient) -> None:
    """Test getting current user without authentication."""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401  # Missing Authorization header


def test_get_current_user_invalid_token(client: TestClient) -> None:
    """Test getting current user with invalid token."""
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401
