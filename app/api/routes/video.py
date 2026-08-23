import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.schemas.job import JobCreateResponse, JobType
from app.schemas.video import VideoColorCorrectRequest, VideoInterpolateRequest, VideoUpscaleRequest
from app.workers.tasks import task_video_color_correct, task_video_interpolate, task_video_upscale

router = APIRouter(prefix="/video", tags=["video"])


def _save_upload(file: UploadFile) -> Path:
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_VIDEO_EXT:
        raise HTTPException(status_code=400, detail=f"Недопустимый формат файла: {ext}")

    dest_dir = settings.INPUT_DIR / "videos"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{uuid.uuid4().hex}{ext}"

    with dest_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return dest_path


@router.post("/upscale", response_model=JobCreateResponse)
async def upscale_video(file: UploadFile = File(...), scale: int = 2, face_enhance: bool = False) -> JobCreateResponse:
    input_path = _save_upload(file)
    params = VideoUpscaleRequest(scale=scale, face_enhance=face_enhance)

    job_id = uuid.uuid4().hex
    task_video_upscale.delay(job_id, str(input_path), params.model_dump())

    return JobCreateResponse(job_id=job_id, job_type=JobType.VIDEO_UPSCALE)


@router.post("/interpolate", response_model=JobCreateResponse)
async def interpolate_video(file: UploadFile = File(...), target_fps: int = 60) -> JobCreateResponse:
    input_path = _save_upload(file)
    params = VideoInterpolateRequest(target_fps=target_fps)

    job_id = uuid.uuid4().hex
    task_video_interpolate.delay(job_id, str(input_path), params.model_dump())

    return JobCreateResponse(job_id=job_id, job_type=JobType.VIDEO_INTERPOLATE)


@router.post("/color-correct", response_model=JobCreateResponse)
async def color_correct_video(
    file: UploadFile = File(...),
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
) -> JobCreateResponse:
    input_path = _save_upload(file)
    params = VideoColorCorrectRequest(brightness=brightness, contrast=contrast, saturation=saturation)

    job_id = uuid.uuid4().hex
    task_video_color_correct.delay(job_id, str(input_path), params.model_dump())

    return JobCreateResponse(job_id=job_id, job_type=JobType.VIDEO_COLOR_CORRECT)
