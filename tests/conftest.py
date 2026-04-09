"""Pytest configuration and shared fixtures."""

from datetime import timedelta
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.auth.jwt import create_access_token
from app.main import create_app


class MockMCPClient:
    """Mock MCP client for testing.

    Provides a minimal interface that matches the real MCP client,
    allowing tests to run without requiring an actual MCP service.
    """

    def __init__(self):
        """Initialize the mock MCP client."""
        # Empty list of tools for testing
        # In real production, this would contain actual tools from the MCP server
        self.session = []


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """FastAPI test client fixture with mock MCP client.

    This fixture creates a test app with a mock MCP client injected,
    similar to how you would inject a test database connection.
    This allows tests to run without requiring an actual MCP service.
    """
    # Create app with mock MCP client injected
    mock_mcp = MockMCPClient()
    test_app = create_app(mcp_client=mock_mcp)

    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture
def access_token() -> str:
    """Create a valid JWT access token for testing."""
    data = {"sub": "test_user_123"}
    token = create_access_token(
        data=data,
        expires_delta=timedelta(minutes=30),
    )
    return token


@pytest.fixture
def auth_headers(access_token: str) -> dict[str, str]:
    """HTTP headers with JWT Bearer token."""
    return {"Authorization": f"Bearer {access_token}"}
