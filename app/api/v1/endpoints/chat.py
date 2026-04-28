"""Chat endpoints."""

from fastapi import APIRouter, HTTPException, Request, status
from fastmcp import Client

from app.schemas.chat import ChatRequest, ChatResponse
from app.services import chat_service

router = APIRouter()


@router.post("/chat/message", response_model=ChatResponse, tags=["chat"])
async def send_chat_message(request: Request, message: ChatRequest) -> ChatResponse:
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
        # Send message and get response
        response = await chat_service.send_message(message_content=message)
        if response:
            response_text = response
        else:
            response_text = "Failed to get a response from the assistant."

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
