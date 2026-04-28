import logging
import os

from fastmcp import Client
from google import genai
from google.genai import types

from app.config import settings
from app.schemas.caption import CaptionJobResult

CAPTION_SYSTEM_PROMPT = """
As image analysis tool, concentrate on the physical description of the subject in the picture. Exclude ephemeral descriptions or attribures like mood, emotion, background, dress, actions
and accessories. Try to infer the gender, age, hair, skin tone, physique, ethnic and other physical descriptions that would help to uniquely identify the person.
Consider if the person in the picture is non-human, or possibly a species from fantasy or science fiction, ie elves, orcs, ogres, and etc. Include species information
only if the subject is non-human. 1-2 sentences is the sweet spot.
Three sentences is pretty much the maximum length you should use unless there is something truly and outrageously unusual about the character.
Remember that you don’t need to describe every single thing about them: Pick out their most interesting and unique features. The description should be suitable to
pass to a text to image generator, as an example: don't start with "The photograph contains.." or "this picture contains..."
Here is a good example:
A pale-skinned elderly woman with long, white hair and a gaunt face. She has a skeletal appearance with deep-set eyes and prominent cheekbones. Her long, flowing white hair frames her face.
"""

COMPARE_SYSTEM_PROMPT = """
Consider hurp to be a function that compares two short character physical descriptions and tell me if they are in conflict or if
they generally agree on the description. Only if they do conflict, generate a plausible merge of the descriptions.
The generated description could merge some of the characteristics of each one. For example, if one describes an Asian person, and the other
a Caucasian person, offer an Eurasian description or mixed heritage. If attributes are in clear opposition, tall vs short, just pick one,
or merge the two, for example if one is a prototypical sword and sorcery muscular male barbarian, in the manner of Conan for example,
and the other is a female then something like Red Sonja would be an acceptable plausible merge.
"""

GENERATE_IMAGE_PROMPT = """
Use information from the character summary for character with the supplied character id and environ to construct
a prompt for a text-to-image model such as Nano Banana, Chroma or Z-Image to create an upper body portrait photograph
(3:4 aspect ratio) of the character posing for a picture.
Use information about the character to set the mood and lighting, such has dark and gloomy for an evil character
for example. Incorporate any mentioned colors or styling the character might have a disposition for , or any
historical period mentioned in the character summery.  Set the background to be something appropriate for the
character, like a smithy for a blacksmith for example, or a ruler sitting on a throne.  However, keep the focus
on the character itself.

Avoid explicit historical religious symbols: generic, fictional or fantastical symbols would be preferred. For example, do not
show an explict cross, but a magical rune would be permitted.

Output ONLY the prompt text, nothing else.

environ: 13th century Eastern Mythiic Europe
"""


def get_genai_client(api_key: str) -> genai.Client:
    """Create a Gemini client instance."""
    if not api_key:
        raise ValueError("GEMINI_API_KEY must be configured before using Gemini services")
    return genai.Client(api_key=api_key)


async def analyze_image(
    model_client: genai.Client, image_path: str
) -> tuple[str, types.GenerateContentResponseUsageMetadata] | tuple[None, None]:
    """Analyze an image file and return a short description."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file does not exist: {image_path}")

    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()

    try:
        response = await model_client.aio.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                "Describe the person in the picture.",
            ],
            config=types.GenerateContentConfig(
                system_instruction=CAPTION_SYSTEM_PROMPT,
            ),
        )
    except Exception as e:
        raise RuntimeError(f"Error during Gemini image analysis: {str(e)}")

    logging.info(f"Gemini image analysis response: {response}")
    if response is None:
        raise RuntimeError("Gemini returned no response for image analysis")

    if response.text and response.usage_metadata:
        return (response.text, response.usage_metadata)
    return (None, None)


async def compare_descriptions(
    model_client: genai.Client,
    existing_description: str,
    new_description: str,
) -> tuple[CaptionJobResult, types.GenerateContentResponseUsageMetadata] | tuple[None, None]:
    """Compare two descriptions and return a merged result."""
    response = await model_client.aio.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=f"hurp({existing_description}, {new_description})",
        config=types.GenerateContentConfig(
            system_instruction=COMPARE_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_json_schema={
                "type": "object",
                "properties": {
                    "state": {"type": "string", "enum": ["Congruent", "Conflict"]},
                    "explanation": {"type": ["string", "null"]},
                    "merge": {"type": ["string", "null"]},
                },
                "required": ["state"],
            },
        ),
    )

    if response is None:
        raise RuntimeError("Gemini returned no response for comparison")

    if response.text and response.usage_metadata:
        return (CaptionJobResult.model_validate_json(response.text), response.usage_metadata)
    return (None, None)


async def generate_image_prompt(
    model_client: genai.Client, character_id: str
) -> tuple[str, types.GenerateContentResponseUsageMetadata] | tuple[None, None]:

    local_mcp_client = Client(settings.MCP_ENDPOINT)
    try:
        async with local_mcp_client:
            (response,) = (
                await model_client.aio.models.generate_content(
                    model="gemini-3.1-flash-lite-preview",
                    contents=f"Generate a prompt for character id:{character_id}",
                    config=types.GenerateContentConfig(
                        system_instruction=GENERATE_IMAGE_PROMPT,
                        tools=[local_mcp_client.session],
                        tool_config=types.ToolConfig(
                            function_calling_config=types.FunctionCallingConfig(
                                mode=types.FunctionCallingConfigMode.AUTO
                            )
                        ),
                    ),
                ),
            )

    except Exception as e:
        raise RuntimeError(f"Error during Gemini image generation: {str(e)}")
    if response.text and response.usage_metadata:
        return (response.text, response.usage_metadata)
    return (None, None)


async def generate_image(
    model_client: genai.Client, character_id: str, prompt: str
) -> list[types.Image]:
    images = []
    try:
        response: types.GenerateContentResponse = await model_client.aio.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=[prompt],
            config=types.GenerateContentConfig(
                http_options=types.HttpOptions(timeout=60000),
                image_config=types.ImageConfig(image_size="512px", aspect_ratio="3:4"),
            ),
        )
        logging.error(f"done: {response}")
        if (response is None) or (response.parts is None):
            return images

        for part in response.parts:
            if part.text is not None:
                logging.info(part.text)
            elif part.inline_data is not None:
                image = part.as_image()
                images.append(image)
    except Exception as e:
        logging.error(f"Error during Gemini image generation: {str(e)}")

    logging.error(images)
    return images
