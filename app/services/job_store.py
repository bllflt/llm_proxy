import json
from typing import Any
from uuid import uuid4

import redis.asyncio as redis

from app.config import settings
from app.schemas.job import CaptionJobData, ImageJobData, JobDataTypes, JobStatus, JobType
from app.utils import logger

client = redis.Redis.from_url(settings.REDIS_URL)


async def create_job(type: JobType, **kwargs: Any) -> JobDataTypes:
    """Create a new caption job in Redis."""
    job_id = str(uuid4())
    if type == JobType.CAPTION:
        job = CaptionJobData(
            type=type,
            job_id=job_id,
            character_id=kwargs["character_id"],
            image_file=kwargs["image_file"],
            current_description=kwargs["current_description"],
            created_by=kwargs["created_by"],
            status=JobStatus.pending,
        )
    elif type == JobType.IMAGE:
        job = ImageJobData(
            type=type,
            job_id=job_id,
            character_id=kwargs["character_id"],
            current_description=kwargs["current_description"],
            created_by=kwargs["created_by"],
            status=JobStatus.pending,
        )
    else:
        raise ValueError(f"Invalid job type: {type}")

    await client.set(job_id, job.model_dump_json())
    return job


async def get_job(job_id: str) -> JobDataTypes | None:
    """Retrieve a stored job by ID from Redis."""
    data = await client.get(job_id)
    if data is None:
        return None
    decoded = json.loads(data.decode("utf-8"))
    logger.logger.debug(decoded)
    if decoded["type"] == JobType.CAPTION:
        return CaptionJobData.model_validate_json(data)
    elif decoded["type"] == JobType.IMAGE:
        return ImageJobData.model_validate_json(data)
    else:
        return None


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
