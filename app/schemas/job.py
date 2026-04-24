from enum import StrEnum
from typing import Annotated, Any, Optional

from pydantic import BaseModel
from pydantic import Field as PydanticField


class JobType(StrEnum):
    CAPTION = "caption"
    IMAGE = "image"


class JobStatus(StrEnum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class JobData(BaseModel):
    type: JobType
    job_id: str
    character_id: str
    current_description: Optional[str] = None
    created_by: str
    status: JobStatus
    result: dict[str, Any] | None = None
    error: str | None = None


class CaptionJobData(JobData):
    type: JobType = JobType.CAPTION
    image_file: str


class ImageJobData(JobData):
    type: JobType = JobType.IMAGE


JobDataTypes = Annotated[CaptionJobData | ImageJobData, PydanticField(discriminator="type")]
