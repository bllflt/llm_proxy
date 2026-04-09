"""Tests for application startup and root endpoint."""

from fastapi.testclient import TestClient


def test_app_startup(client: TestClient) -> None:
    """Test that app starts without errors."""
    assert client is not None


def test_root_endpoint(client: TestClient) -> None:
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "Welcome to LLM Proxy API"
