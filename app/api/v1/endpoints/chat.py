"""Chat endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.dependencies import get_current_user
from app.schemas.chat import ChatHistoryResponse, ChatRequest, ChatResponse
from app.services import chat_service

router = APIRouter()


@router.post("/chat/message", response_model=ChatResponse, tags=["chat"])
async def send_chat_message(
    request: Request,
    message: ChatRequest,
    user_id: Annotated[str, Depends(get_current_user)],
) -> ChatResponse:
    """
    Send a chat message and get a response from the assistant.

    Requires JWT authentication.

    Args:
        request: FastAPI request object (for accessing app state)
        message: Chat message content
        user_id: Current user ID from JWT token

    Returns:
        Assistant's response

    Raises:
        HTTPException: If message processing fails
    """
    try:
        # Get MCP client from app state if available
        mcp_client = getattr(request.app.state, "mcp_client", None)

        # Send message and get response
        response_text = await chat_service.send_message(
            user_id=user_id,
            message_content=message.content,
            mcp_client=mcp_client,
        )

        return ChatResponse(assistant=response_text)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.get("/chat/history", response_model=ChatHistoryResponse, tags=["chat"])
async def get_chat_history(
    user_id: Annotated[str, Depends(get_current_user)],
) -> ChatHistoryResponse:
    """
    Retrieve the full chat history for the current user.

    Requires JWT authentication.

    Args:
        user_id: Current user ID from JWT token

    Returns:
        Chat history with all messages

    Raises:
        HTTPException: If history retrieval fails
    """
    try:
        messages = await chat_service.get_chat_history(user_id)
        return ChatHistoryResponse(messages=messages)

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.delete("/chat/history", tags=["chat"])
async def clear_chat_history(
    user_id: Annotated[str, Depends(get_current_user)],
) -> dict[str, str]:
    """
    Clear the chat history for the current user.

    Requires JWT authentication.

    Args:
        user_id: Current user ID from JWT token

    Returns:
        Confirmation message
    """
    try:
        await chat_service.clear_chat_history(user_id)
        return {"message": "Chat history cleared successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear history: {str(e)}",
        )
