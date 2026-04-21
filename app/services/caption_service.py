import httpx

from app.config import settings
from app.schemas.caption import CaptionJobResult
from app.schemas.job import JobStatus
from app.services.job_store import complete_job, fail_job, get_job, update_job_status
from app.services.stats_service import update_llm_usage
from app.utils.gemini import analyze_image, compare_descriptions, get_genai_client


async def submit_result(character_id: str, explanation: str | None, merge: str | None) -> None:
    """Submit the caption result to the external API endpoint."""
    async with httpx.AsyncClient() as client:
        await client.put(
            settings.RESULT_API_ENDPOINT,
            json={
                "character_id": character_id,
                "explanation": explanation,
                "merge": merge,
            },
            timeout=settings.HTTP_TIMEOUT,
        )


async def process_caption_job(job_id: str) -> None:
    """Process a caption job end-to-end."""
    job = await get_job(job_id)
    if job is None:
        return

    await update_job_status(job_id, JobStatus.processing)
    model_client = get_genai_client(settings.GEMINI_API_KEY)

    try:
        (description, metadata) = await analyze_image(model_client, job.image_file)
        if metadata:
            await update_llm_usage("image analysis", metadata.total_token_count)
        if description is None:
            raise RuntimeError("Failed to generate description from image")
        if job.current_description:
            (comparison, metadata) = await compare_descriptions(
                model_client,
                job.current_description,
                description,
            )
            if metadata:
                await update_llm_usage("description comparison", metadata.total_token_count)
            if comparison is None:
                raise RuntimeError("Failed to compare descriptions")
        else:
            comparison = CaptionJobResult(
                state="Conflict",
                explanation=None,
                merge=description,
            )

        await complete_job(job_id, comparison.model_dump())
        if comparison.state == "Conflict":
            await submit_result(job.character_id, comparison.explanation, comparison.merge)
    except Exception as exc:
        await fail_job(job_id, str(exc))
