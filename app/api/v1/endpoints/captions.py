from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.schemas.caption import CaptionJobResponse, CaptionRequest, CaptionStatusResponse
from app.services.caption_service import process_caption_job
from app.services.job_store import create_job, get_job

router = APIRouter()


@router.post("/captions", response_model=CaptionJobResponse, tags=["captions"])
async def create_caption_job(
    payload: CaptionRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
) -> CaptionJobResponse:
    """Submit a caption processing job."""
    job = await create_job(
        character_id=payload.character_id,
        image_file=payload.image_file,
        current_description=payload.current_description,
        created_by=user_id,
    )
    background_tasks.add_task(process_caption_job, job.job_id)
    return CaptionJobResponse(job_id=job.job_id, status=job.status.value)


@router.get("/captions/{job_id}", response_model=CaptionStatusResponse, tags=["captions"])
async def get_caption_job_status(
    job_id: str,
    user_id: str = Depends(get_current_user),
) -> CaptionStatusResponse:
    """Retrieve caption job status and result."""
    job = await get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.created_by != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return CaptionStatusResponse(
        job_id=job.job_id,
        character_id=job.character_id,
        status=job.status,
        result=job.result,
        error=job.error,
    )
