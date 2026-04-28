"""FastAPI application factory."""

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.config import settings


def create_app(mcp_client: Any | None = None) -> FastAPI:
    """
    Create and configure FastAPI application.

    Args:
        mcp_client: Optional MCP client to inject (e.g., for testing).
                   If not provided, will be created from MCP_ENDPOINT.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="LLM Proxy API",
        description="FastAPI REST API with JWT authentication",
        version="0.1.0",
        debug=settings.DEBUG,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(v1_router)

    @app.get("/", tags=["root"])
    async def root() -> dict[str, str]:
        """Root endpoint."""
        return {"message": "Welcome to LLM Proxy API"}

    return app


# Production app instance (no mcp_client injected, will use MCP_ENDPOINT)
app = create_app()
