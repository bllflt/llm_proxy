from enum import StrEnum
from typing import Any, Optional

from pydantic import BaseModel


class JobStatus(StrEnum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class JobData(BaseModel):
    job_id: str
    character_id: str
    image_file: str
    current_description: Optional[str] = None
    created_by: str
    status: JobStatus
    result: dict[str, Any]| None = None
    error: str | None = None
