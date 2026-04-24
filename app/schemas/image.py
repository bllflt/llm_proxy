import typing

from pydantic import BaseModel, Field

from app.schemas.job import JobStatus


class ImageRequest(BaseModel):
    """Request payload for submitting a caption job."""

    character_id: str = Field(..., min_length=1)
    current_description: str | None = None


class ImageJobResult(BaseModel): ...


class ImageJobResponse(BaseModel):
    """Response returned when an Image job is created."""

    job_id: str
    status: JobStatus = JobStatus.pending


class ImageStatusResponse(BaseModel):
    """Response for caption job status queries."""

    job_id: str
    character_id: str
    status: JobStatus
    result: dict[str, typing.Any] | None = None
    error: str | None = None
