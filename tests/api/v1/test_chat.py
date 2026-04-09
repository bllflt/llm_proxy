"""Tests for chat endpoints."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.auth.jwt import create_access_token
from app.main import create_app


class MockMCPClient:
    """Mock MCP client for testing."""

    def __init__(self):
        self.session = []


@pytest.fixture
def client_with_config() -> TestClient:
    """FastAPI test client with MCP configured."""
    mock_mcp = MockMCPClient()
    test_app = create_app(mcp_client=mock_mcp)
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture
def access_token_1() -> str:
    """Create a valid JWT token for user 1."""
    data = {"sub": "test_user_1"}
    token = create_access_token(
        data=data,
        expires_delta=timedelta(minutes=30),
    )
    return token


@pytest.fixture
def access_token_2() -> str:
    """Create a valid JWT token for user 2."""
    data = {"sub": "test_user_2"}
    token = create_access_token(
        data=data,
        expires_delta=timedelta(minutes=30),
    )
    return token


@pytest.fixture
def auth_headers_1(access_token_1: str) -> dict[str, str]:
    """HTTP headers with user 1's JWT Bearer token."""
    return {"Authorization": f"Bearer {access_token_1}"}


@pytest.fixture
def auth_headers_2(access_token_2: str) -> dict[str, str]:
    """HTTP headers with user 2's JWT Bearer token."""
    return {"Authorization": f"Bearer {access_token_2}"}


# ============================================================================
# Tests for POST /chat/message endpoint
# ============================================================================


def test_send_message_authenticated(
    client_with_config: TestClient,
    auth_headers_1: dict[str, str],
) -> None:
    """Test sending a chat message with valid authentication."""
    with patch("app.services.chat_service.send_message") as mock_send:
        mock_send.return_value = "This is an assistant response."

        response = client_with_config.post(
            "/api/v1/chat/message",
            json={"content": "Hello, assistant!"},
            headers=auth_headers_1,
        )

        assert response.status_code == 200
        data = response.json()
        assert "assistant" in data
        assert data["assistant"] == "This is an assistant response."
        mock_send.assert_called_once()


def test_send_message_unauthorized(client_with_config: TestClient) -> None:
    """Test sending message without authentication."""
    response = client_with_config.post(
        "/api/v1/chat/message",
        json={"content": "Hello!"},
    )
    assert response.status_code == 401


def test_send_message_invalid_token(client_with_config: TestClient) -> None:
    """Test sending message with invalid token."""
    response = client_with_config.post(
        "/api/v1/chat/message",
        json={"content": "Hello!"},
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401


def test_send_message_empty_content(
    client_with_config: TestClient,
    auth_headers_1: dict[str, str],
) -> None:
    """Test sending a message with empty content."""
    response = client_with_config.post(
        "/api/v1/chat/message",
        json={"content": ""},
        headers=auth_headers_1,
    )
    assert response.status_code == 422  # Validation error


def test_send_message_missing_content(
    client_with_config: TestClient,
    auth_headers_1: dict[str, str],
) -> None:
    """Test sending a message without content field."""
    response = client_with_config.post(
        "/api/v1/chat/message",
        json={},
        headers=auth_headers_1,
    )
    assert response.status_code == 422


def test_send_message_service_error(
    client_with_config: TestClient,
    auth_headers_1: dict[str, str],
) -> None:
    """Test handling service errors."""
    with patch("app.services.chat_service.send_message") as mock_send:
        mock_send.side_effect = RuntimeError("Gemini API error")

        response = client_with_config.post(
            "/api/v1/chat/message",
            json={"content": "Hello!"},
            headers=auth_headers_1,
        )

        assert response.status_code == 500


# ============================================================================
# Tests for GET /chat/history endpoint
# ============================================================================


def test_get_empty_history(
    client_with_config: TestClient,
    auth_headers_1: dict[str, str],
) -> None:
    """Test retrieving empty chat history."""
    with patch("app.services.chat_service.get_chat_history") as mock_get:
        mock_get.return_value = []

        response = client_with_config.get(
            "/api/v1/chat/history",
            headers=auth_headers_1,
        )

        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert data["messages"] == []
        mock_get.assert_called_once_with("test_user_1")


def test_get_chat_history(
    client_with_config: TestClient,
    auth_headers_1: dict[str, str],
) -> None:
    """Test retrieving chat history."""
    from app.schemas.chat import ChatMessageSchema

    mock_history = [
        ChatMessageSchema(role="user", content="Hello!"),
        ChatMessageSchema(role="assistant", content="Hi there!"),
        ChatMessageSchema(role="user", content="How are you?"),
        ChatMessageSchema(role="assistant", content="I'm doing great!"),
    ]

    with patch("app.services.chat_service.get_chat_history") as mock_get:
        mock_get.return_value = mock_history

        response = client_with_config.get(
            "/api/v1/chat/history",
            headers=auth_headers_1,
        )

        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert len(data["messages"]) == 4
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == "Hello!"
        assert data["messages"][1]["role"] == "assistant"
        mock_get.assert_called_once_with("test_user_1")


def test_get_history_unauthorized(client_with_config: TestClient) -> None:
    """Test retrieving history without authentication."""
    response = client_with_config.get("/api/v1/chat/history")
    assert response.status_code == 401


def test_get_history_different_users(
    client_with_config: TestClient,
    auth_headers_1: dict[str, str],
    auth_headers_2: dict[str, str],
) -> None:
    """Test that different users see different histories."""
    from app.schemas.chat import ChatMessageSchema

    mock_history_1 = [
        ChatMessageSchema(role="user", content="User 1 message"),
    ]
    mock_history_2 = [
        ChatMessageSchema(role="user", content="User 2 message"),
    ]

    with patch("app.services.chat_service.get_chat_history") as mock_get:
        mock_get.side_effect = [mock_history_1, mock_history_2]

        # Get history for user 1
        response1 = client_with_config.get(
            "/api/v1/chat/history",
            headers=auth_headers_1,
        )
        assert response1.status_code == 200
        assert response1.json()["messages"][0]["content"] == "User 1 message"

        # Get history for user 2
        response2 = client_with_config.get(
            "/api/v1/chat/history",
            headers=auth_headers_2,
        )
        assert response2.status_code == 200
        assert response2.json()["messages"][0]["content"] == "User 2 message"


def test_get_history_service_error(
    client_with_config: TestClient,
    auth_headers_1: dict[str, str],
) -> None:
    """Test handling service errors for history retrieval."""
    with patch("app.services.chat_service.get_chat_history") as mock_get:
        mock_get.side_effect = RuntimeError("Redis error")

        response = client_with_config.get(
            "/api/v1/chat/history",
            headers=auth_headers_1,
        )

        assert response.status_code == 500


# ============================================================================
# Tests for DELETE /chat/history endpoint
# ============================================================================


def test_clear_history(
    client_with_config: TestClient,
    auth_headers_1: dict[str, str],
) -> None:
    """Test clearing chat history."""
    with patch("app.services.chat_service.clear_chat_history") as mock_clear:
        response = client_with_config.delete(
            "/api/v1/chat/history",
            headers=auth_headers_1,
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "cleared" in data["message"].lower()
        mock_clear.assert_called_once_with("test_user_1")


def test_clear_history_unauthorized(client_with_config: TestClient) -> None:
    """Test clearing history without authentication."""
    response = client_with_config.delete("/api/v1/chat/history")
    assert response.status_code == 401


def test_clear_history_service_error(
    client_with_config: TestClient,
    auth_headers_1: dict[str, str],
) -> None:
    """Test handling service errors for clearing history."""
    with patch("app.services.chat_service.clear_chat_history") as mock_clear:
        mock_clear.side_effect = RuntimeError("Redis error")

        response = client_with_config.delete(
            "/api/v1/chat/history",
            headers=auth_headers_1,
        )

        assert response.status_code == 500
