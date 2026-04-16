import logging

import msgpack
import redis.asyncio as redis
from fastmcp import Client
from google import genai
from google.genai import types as genai_types
from google.genai.chats import AsyncChat

from app.config import settings
from app.schemas.chat import ChatRequest

client = redis.Redis.from_url(settings.REDIS_URL)


def _get_redis_key(user_id: str) -> str:
    """Generate Redis key for user's chat history."""
    return f"{settings.CHAT_HISTORY_PREFIX}:{user_id}:history"


def _get_genai_client(api_key: str) -> genai.Client:
    """Create a Gemini client instance."""
    if not api_key:
        raise ValueError("GEMINI_API_KEY must be configured")
    return genai.Client(api_key=api_key)


async def send_message(
    message_content: ChatRequest,
    mcp_client: Client,
) -> str | None:
    """
    Send a message and get a response from Gemini with MCP tools support.
    """
    genai_client = _get_genai_client(settings.GEMINI_API_KEY)
    print(message_content)
    try:
        async with mcp_client:
            packed = await client.get("chat:1:history")
            if packed:
                history = msgpack.unpackb(packed, raw=False)
            else:
                history = []
            chat: AsyncChat = genai_client.aio.chats.create(
                model=settings.CHAT_MODEL,
                config=genai_types.GenerateContentConfig(
                    system_instruction="""
                                    You are a helpful assistant. You have access to tools for looking up specific character details. 
                                    However, for general questions (like history, fashion, culture), answer directly using your internal 
                                    knowledge.
                    """,
                    tools=[mcp_client.session],
                    tool_config=genai_types.ToolConfig(
                        function_calling_config=genai_types.FunctionCallingConfig(mode="AUTO")
                    ),
                ),
                history=[genai_types.Content(**item) for item in history],
            )
            response = await chat.send_message(message_content.content)
            if response:
                history_to_save = [item.model_dump() for item in chat.get_history()]
                packed = msgpack.packb(history_to_save, use_bin_type=True)
                await client.set(
                    "chat:1:history", packed, ex=settings.CHAT_HISTORY_EXPIRE_MINUTES * 60
                )
                logging.error(response)
                if response.text:
                    return response.text
            else:
                raise RuntimeError("Gemini returned no response")
    except Exception as e:
        print(e)
        return None
