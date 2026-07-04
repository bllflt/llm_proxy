import logging
from typing import Any

import msgpack
import redis.asyncio as redis
from fastmcp import Client
from google import genai
from google.genai import types as genai_types
from google.genai.chats import AsyncChat
from google.genai.errors import APIError

from app.auth.jwt import create_access_token
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


async def get_history(user_id: str) -> list[Any]:
    packed = await client.get(_get_redis_key(user_id))
    if packed:
        history = msgpack.unpackb(packed, raw=False)
        return history
    else:
        return []


async def send_message(
    message_content: ChatRequest,
) -> str | None:
    """
    Send a message and get a response from Gemini with MCP tools support.
    """
    genai_client = _get_genai_client(settings.GEMINI_API_KEY)

    token = create_access_token(
        {
            "sub": message_content.user_id,
            "story_uuid": message_content.story_uuid,
            "permitted_stories": message_content.permitted_stories,
        }
    )

    try:
        local_mcp_client = Client(settings.MCP_ENDPOINT, auth=token)
        async with local_mcp_client:  # notype: ignore
            packed = await client.get(_get_redis_key(message_content.user_id))
            if packed:
                history = msgpack.unpackb(packed, raw=False)
            else:
                history = []
            chat: AsyncChat = genai_client.aio.chats.create(
                model=settings.CHAT_MODEL,
                config=genai_types.GenerateContentConfig(
                    system_instruction="""
                                        You are a Medieval Fantasy Lore and History Assistant. Your purpose is to help users develop,
                                        track and understand historical, cultural and mythological details for medieval fantasy settings.
                                        You have access to a production "Writer's Bible" - the internal guidebook used to establish
                                        characters, rules and settings. However, for general questions (like history, fashion,
                                        culture), answer directly using your internal knowledge.
                                        Unless specified otherwise assume and prioritize the character tools when asked about names.
                                        Do not discuss implementation details of the tools or mention that you are using tools. You are not
                                        a coding assistant, do not answer questions regarding coding.
                                        Just provide the answer to the user's question. Do not hallucinate, if a field is empty report it as
                                        such.
                                        Prefer referencing specific character fields, rather than infering or making assumptions.
                                        For example, if the user asks "Is Donald a man?" then use the sex field to answer the question,
                                        rather than infering based on the name or other details.
                                        Format the output in markdown.
                                        Scope of Knowledge:
                                          - You may discuss real-world medieval history, culture and warefare.
                                          - You may discuss fictional world-building, lore, character backgrounds and medieval
                                            fantasy tropes.
                                        Strict Contraints:
                                            - You are strictly prohibited from acting as a coding assistant, writing software code or debugging.
                                            - You are strictly prohibited from offering mathematical, scientific or non-medieval factual advice.
                                        Handling Out-of-Scope Requests:
                                        If the user asks for anything related to coding, modern technology or any topic outside of
                                        medieval fantasy and history, you must reply with exactly this message:
                                        "I am designed exclusively for medieval fantasy lore and historical tracking. I cannot assist with
                                        that topic."

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
                        _get_redis_key(message_content.user_id),
                        packed,
                        ex=settings.CHAT_HISTORY_EXPIRE_MINUTES * 60,
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
