from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.schemas.image import ImageJobResponse, ImageRequest, ImageStatusResponse
from app.schemas.job import JobStatus
from app.services.gen_image_service import process_image_job
from app.services.job_store import JobType, create_job, get_job

router = APIRouter()


@router.post("/images", response_model=ImageJobResponse, tags=["images"])
async def create_gen_image_job(
    payload: ImageRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
) -> ImageJobResponse:

    job = await create_job(
        type=JobType.IMAGE,
        character_id=payload.character_id,
        current_description=payload.current_description,
        created_by=user_id,
    )
    background_tasks.add_task(process_image_job, job.job_id)
    return ImageJobResponse(job_id=job.job_id, status=JobStatus.pending)


@router.get("/images/{job_id}", response_model=ImageStatusResponse, tags=["images"])
async def get_image_job_status(
    job_id: str,
    user_id: str = Depends(get_current_user),
) -> ImageStatusResponse:
    """Retrieve caption job status and result."""
    job = await get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.created_by != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return ImageStatusResponse(
        job_id=job.job_id,
        character_id=job.character_id,
        status=job.status,
        result=job.result,
        error=job.error,
    )
