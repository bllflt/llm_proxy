"""Chat message schemas."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageSchema(BaseModel):
    """Single message in conversation history."""

    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """Chat message request."""

    content: str = Field(..., min_length=1, max_length=4096, description="User message")


class ChatResponse(BaseModel):
    """Chat message response."""

    assistant: str = Field(..., description="Assistant's response")


class ChatHistoryResponse(BaseModel):
    """Full chat conversation history."""

    messages: list[ChatMessageSchema] = Field(
        default_factory=list, description="Conversation history"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "messages": [
                    {"role": "user", "content": "What is the capital of France?"},
                    {"role": "assistant", "content": "The capital of France is Paris."},
                ]
            }
        }
    )
