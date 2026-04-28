import logging

import msgpack
import redis.asyncio as redis
from fastmcp import Client
from google import genai
from google.genai import types as genai_types
from google.genai.chats import AsyncChat
from google.genai.errors import APIError

from app.config import settings
from app.schemas.chat import ChatRequest
from app.services.stats_service import update_llm_usage

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
) -> str | None:
    """
    Send a message and get a response from Gemini with MCP tools support.
    """
    genai_client = _get_genai_client(settings.GEMINI_API_KEY)
    print(message_content)

    try:
        local_mcp_client = Client(settings.MCP_ENDPOINT)
        async with local_mcp_client:
            packed = await client.get("chat:1:history")
            if packed:
                history = msgpack.unpackb(packed, raw=False)
            else:
                history = []
            chat: AsyncChat = genai_client.aio.chats.create(
                model=settings.CHAT_MODEL,
                config=genai_types.GenerateContentConfig(
                    system_instruction="""
                                        Helpful assistant writer. You have access to tools for looking up specific character details.
                                        However, for general questions (like history, fashion, culture), answer directly using your internal
                                        knowledge.
                                        Do not discuss implementation details of the tools or mention that you are using tools.
                                        Just provide the answer to the user's question.
                                        Prefer referencing specific character fields, rather than infering or making assumptions.
                                        For example, if the user asks "Is Donald a man?" then use the sex field to answer the question,
                                        rather than infering based on the name or other details.
                                        Format the output as plain text.
                       """,
                    tools=[local_mcp_client.session],
                    tool_config=genai_types.ToolConfig(
                        function_calling_config=genai_types.FunctionCallingConfig(
                            mode=genai_types.FunctionCallingConfigMode.AUTO
                        )
                    ),
                ),
                history=[genai_types.Content(**item) for item in history],
            )
            response = await chat.send_message(message_content.content)
            if response:
                history_to_save = [item.model_dump() for item in chat.get_history()]
                packed = msgpack.packb(history_to_save, use_bin_type=True)
                if packed:
                    await client.set(
                        "chat:1:history", packed, ex=settings.CHAT_HISTORY_EXPIRE_MINUTES * 60
                    )
                logging.error(response.usage_metadata)
                if response.usage_metadata:
                    await update_llm_usage("chat", response.usage_metadata.total_token_count)
                if response.text:
                    return response.text
            else:
                raise RuntimeError("Gemini returned no response")
    except APIError as e:
        logging.error(f"APIError: {e.code} - {e.response}")
        return None

    except Exception as e:
        logging.error(f"Error during Gemini chat: {str(e)}")
        return None
