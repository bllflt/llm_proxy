"""Chat service for managing conversations and Gemini integration."""

import msgpack
import redis.asyncio as redis
from google import genai
from google.genai import types as genai_types
from google.genai.chats import AsyncChat

from app.config import settings
from app.schemas.chat import ChatMessageSchema

client = redis.Redis.from_url(settings.REDIS_URL)


def _get_redis_key(user_id: str) -> str:
    """Generate Redis key for user's chat history."""
    return f"{settings.CHAT_HISTORY_PREFIX}:{user_id}:history"


def _get_genai_client(api_key: str) -> genai.Client:
    """Create a Gemini client instance."""
    if not api_key:
        raise ValueError("GEMINI_API_KEY must be configured")
    return genai.Client(api_key=api_key)


async def get_chat_history(user_id: str) -> list[ChatMessageSchema]:
    """Retrieve chat history for a user from Redis."""
    key = _get_redis_key(user_id)
    packed = await client.get(key)
    if not packed:
        return []
    try:
        history_data = msgpack.unpackb(packed, raw=False)
        return [ChatMessageSchema(**item) for item in history_data]
    except (msgpack.exceptions.UnpackException, ValueError) as e:
        raise RuntimeError(f"Failed to deserialize chat history: {e}")


async def store_message(user_id: str, role: str, content: str) -> ChatMessageSchema:
    """Store a message in the user's chat history."""
    message = ChatMessageSchema(role=role, content=content)
    history = await get_chat_history(user_id)
    history.append(message)

    key = _get_redis_key(user_id)
    history_data = [msg.model_dump() for msg in history]
    packed = msgpack.packb(history_data, use_bin_type=True)
    expire_seconds = settings.CHAT_HISTORY_EXPIRE_MINUTES * 60
    await client.set(key, packed, ex=expire_seconds)

    return message


async def clear_chat_history(user_id: str) -> None:
    """Clear chat history for a user."""
    key = _get_redis_key(user_id)
    await client.delete(key)


async def send_message(
    user_id: str,
    message_content: str,
    mcp_client: object | None = None,
) -> str:
    """
    Send a message and get a response from Gemini with MCP tools support.

    Args:
        user_id: User ID for history tracking
        message_content: User's message
        mcp_client: Optional MCP client for tool access

    Returns:
        Assistant's response text
    """
    try:
        # Store user message
        await store_message(user_id, "user", message_content)

        # Retrieve full history for context
        history = await get_chat_history(user_id)

        # Create Gemini client
        genai_client = _get_genai_client(settings.GEMINI_API_KEY)

        # Prepare system instruction and tools based on MCP availability
        if mcp_client:
            system_instruction = (
                "You are a helpful assistant. You have access to tools for looking up specific information. "
                "Use these tools when needed. For general questions, answer directly using your internal knowledge."
            )
            tools = [mcp_client.session]
            tool_config = genai_types.ToolConfig(
                function_calling_config=genai_types.FunctionCallingConfig(mode="AUTO")
            )
        else:
            system_instruction = "You are a helpful assistant. Answer questions directly using your internal knowledge."
            tools = []
            tool_config = None

        # Build config kwargs
        config_kwargs = {
            "system_instruction": system_instruction,
            "tools": tools,
        }
        if tool_config is not None:
            config_kwargs["tool_config"] = tool_config

        # Create chat with full history
        chat: AsyncChat = genai_client.aio.chats.create(
            model=settings.CHAT_MODEL,
            config=genai_types.GenerateContentConfig(**config_kwargs),
            history=[genai_types.Content(**item.model_dump()) for item in history[:-1]],
        )

        # Send message (last one in history)
        response = await chat.send_message(message_content)

        if not response:
            raise RuntimeError("Gemini returned no response")

        assistant_response = response.text or ""

        # Store assistant response
        await store_message(user_id, "assistant", assistant_response)

        return assistant_response

    except Exception as e:
        raise RuntimeError(f"Chat processing failed: {str(e)}")
