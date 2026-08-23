from fastapi import APIRouter, HTTPException

from app.schemas.job import JobStatusResponse
from app.workers.tasks import get_job_status

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobStatusResponse)
async def job_status(job_id: str) -> JobStatusResponse:
    status = get_job_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return status
