from pydantic import BaseModel, ConfigDict, Field


class ChatMessageSchema(BaseModel):
    """Single message in conversation history."""

    content: str


class ChatRequest(BaseModel):
    """Chat message request."""

    content: str = Field(..., min_length=1, max_length=4096, description="User message")
    story_uuid: str = Field(..., description="UUID of the story context for the chat")
    user_id: str = Field(..., description="User ID for the chat session")
    permitted_stories: list[str] = Field(
        ..., description="List of story UUIDs the user is allowed to access"
    )


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
