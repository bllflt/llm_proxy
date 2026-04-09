"""FastAPI application factory."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import Client

from app.api.v1.router import router as v1_router
from app.config import logger, settings


def _create_lifespan(mcp_client: Any | None) -> Any:
    """Create a lifespan context manager for the app.

    Args:
        mcp_client: The MCP client to use. If None, it will be created from MCP_ENDPOINT.
                   In production, should not be None.

    Returns:
        An async context manager for the app lifespan
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> Any:
        """Application lifespan context manager."""
        logger.info("Application startup")

        # If mcp_client was injected (e.g., in tests), use it directly
        if mcp_client is not None:
            app.state.mcp_client = mcp_client
            logger.info("MCP client injected")
        else:
            # Production mode: MCP_ENDPOINT is required
            if not settings.MCP_ENDPOINT:
                raise RuntimeError("MCP_ENDPOINT environment variable is required in production")
            try:
                client = Client(settings.MCP_ENDPOINT)
                logger.info(f"MCP client initialized at {settings.MCP_ENDPOINT}")
                app.state.mcp_client = client
            except Exception as e:
                logger.error(f"Failed to initialize MCP client: {e}")
                raise

        yield

        logger.info("Application shutdown")

    return lifespan


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
        lifespan=_create_lifespan(mcp_client),
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
