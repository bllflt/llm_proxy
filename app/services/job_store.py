from typing import Any
from uuid import uuid4

import redis.asyncio as redis

from app.config import settings
from app.schemas.job import JobData, JobStatus

client = redis.Redis.from_url(settings.REDIS_URL)


async def create_job(
    character_id: str,
    image_file: str,
    current_description: str | None,
    created_by: str,
) -> JobData:
    """Create a new caption job in Redis."""
    job_id = str(uuid4())
    job = JobData(
        job_id=job_id,
        character_id=character_id,
        image_file=image_file,
        current_description=current_description,
        created_by=created_by,
        status=JobStatus.pending,
    )
    await client.set(job_id, job.model_dump_json())
    return job


async def get_job(job_id: str) -> JobData | None:
    """Retrieve a stored job by ID from Redis."""
    data = await client.get(job_id)
    if data is None:
        return None
    return JobData.model_validate_json(data.decode("utf-8"))


async def update_job_status(job_id: str, status: JobStatus) -> None:
    """Update a job status in Redis."""
    job = await get_job(job_id)
    if job is None:
        return
    job.status = status
    await client.set(job_id, job.model_dump_json())


async def complete_job(job_id: str, result: dict[str, Any]) -> None:
    """Mark a job completed with result data in Redis."""
    job = await get_job(job_id)
    if job is None:
        return
    job.status = JobStatus.completed
    job.result = result
    await client.set(job_id, job.model_dump_json())


async def fail_job(job_id: str, error: str) -> None:
    """Mark a job failed with an error message in Redis."""
    job = await get_job(job_id)
    if job is None:
        return
    job.status = JobStatus.failed
    job.error = error
    await client.set(job_id, job.model_dump_json())
