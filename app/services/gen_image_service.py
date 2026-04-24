import logging
import tempfile

import httpx
from google.genai import types

from app.config import settings
from app.schemas.job import ImageJobData, JobStatus
from app.services.job_store import complete_job, fail_job, get_job, update_job_status
from app.services.stats_service import update_llm_usage
from app.utils.gemini import generate_image, generate_image_prompt, get_genai_client


async def submit_result(character_id: str, images: list[types.Image]):
    for image in images:
        async with httpx.AsyncClient() as client:
            with tempfile.TemporaryDirectory() as temp_dir:
                image.save(f"{temp_dir}/image.jpg")
                await client.post(
                    settings.IMAGE_UPLOAD_ENDPOINT,
                    data={"character_id": character_id},
                    files={"image": open(f"{temp_dir}/image.jpg", "rb")},
                )


async def process_image_job(job_id: str) -> None:

    job: ImageJobData = await get_job(job_id)
    if job is None:
        return
    await update_job_status(job_id, JobStatus.processing)
    model_client = get_genai_client(settings.GEMINI_API_KEY)

    try:
        (prompt, metadata) = await generate_image_prompt(model_client, job.character_id)
    except Exception as exc:
        await fail_job(job_id, str(exc))
        raise
    logging.info(f"Gemini image generation prompt: {prompt}")
    if metadata:
        await update_llm_usage("image generation", metadata.total_token_count)
    if prompt is None:
        raise RuntimeError("Failed to generate image prompt")
    try:
        logging.info("start waiting")
        images = await generate_image(model_client, job.character_id, prompt)
        logging.info("done waiting")
    except Exception as exc:
        await fail_job(job_id, str(exc))
    if images is None:
        raise RuntimeError("Failed to generate images")
    await submit_result(job.character_id, images)
    await complete_job(job_id, {})
