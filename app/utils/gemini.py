import os

from google import genai
from google.genai import types

from app.schemas.caption import CaptionJobResult

CAPTION_SYSTEM_PROMPT = """
As image analysis tool, concentrate on the physical description of the subject in the picture. Ignore ephemeral attribures like mood, emotion, background, dress, actions
and accessories. Try to sus out the gender, age, hair, skin tone, physique, ethnic and other physical descriptions that would help to uniquely identify the person.
Consider if the person in the picture is non-human, or possibly a species from fantasy or science fiction, ie elves, orcs, ogres, and etc. Include species information
only if the subject is non-human. 1-2 sentences is the sweet spot.
Three sentences is pretty much the maximum length you should use unless there is something truly and outrageously unusual about the character.
Remember that you don’t need to describe every single thing about them: Pick out their most interesting and unique features. The description should be suitable to
pass to a text to image generator, that is don't start with "The photograph contains.." or "this picture contains..."
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


def get_genai_client(api_key: str) -> genai.Client:
    """Create a Gemini client instance."""
    if not api_key:
        raise ValueError("GEMINI_API_KEY must be configured before using Gemini services")
    return genai.Client(api_key=api_key)


async def analyze_image(model_client: genai.Client, image_path: str) -> str | None:
    """Analyze an image file and return a short description."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file does not exist: {image_path}")

    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()

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

    if response is None:
        raise RuntimeError("Gemini returned no response for image analysis")

    return response.text


async def compare_descriptions(
    model_client: genai.Client,
    existing_description: str,
    new_description: str,
) -> CaptionJobResult:
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

    return CaptionJobResult.model_validate_json(response.text)
