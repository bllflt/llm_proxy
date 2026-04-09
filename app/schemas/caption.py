import typing

from pydantic import BaseModel, Field

from app.schemas import job


class CaptionRequest(BaseModel):
    """Request payload for submitting a caption job."""

    character_id: str = Field(..., min_length=1)
    image_file: str = Field(..., min_length=1)
    current_description: str | None = None


class CaptionJobResult(BaseModel):
    """Caption job result structure."""

    state: typing.Literal["Congruent", "Conflict"]
    explanation: str | None = None
    merge: str | None = None


class CaptionJobResponse(BaseModel):
    """Response returned when a caption job is created."""

    job_id: str
    status: typing.Literal["pending"]


class CaptionStatusResponse(BaseModel):
    """Response for caption job status queries."""

    job_id: str
    character_id: str
    status: job.JobStatus
    result: dict[str, typing.Any] | None  = None
    error: str | None = None
