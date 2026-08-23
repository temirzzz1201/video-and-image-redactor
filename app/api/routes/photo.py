import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.schemas.job import JobCreateResponse, JobType
from app.schemas.photo import (
    BackgroundRemoveRequest,
    ColorCorrectRequest,
    FaceEnhanceRequest,
    ObjectRemoveRequest,
    UpscaleRequest,
)
from app.workers.tasks import (
    task_photo_background_remove,
    task_photo_color_correct,
    task_photo_face_enhance,
    task_photo_object_remove,
    task_photo_upscale,
)

router = APIRouter(prefix="/photo", tags=["photo"])


def _save_upload(file: UploadFile) -> Path:
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_PHOTO_EXT:
        raise HTTPException(status_code=400, detail=f"Недопустимый формат файла: {ext}")

    dest_dir = settings.INPUT_DIR / "photos"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{uuid.uuid4().hex}{ext}"

    with dest_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return dest_path


@router.post("/upscale", response_model=JobCreateResponse)
async def upscale_photo(file: UploadFile = File(...), scale: int = 2, face_enhance: bool = False) -> JobCreateResponse:
    input_path = _save_upload(file)
    params = UpscaleRequest(scale=scale, face_enhance=face_enhance)

    job_id = uuid.uuid4().hex
    task_photo_upscale.delay(job_id, str(input_path), params.model_dump())

    return JobCreateResponse(job_id=job_id, job_type=JobType.PHOTO_UPSCALE)


@router.post("/face-enhance", response_model=JobCreateResponse)
async def face_enhance_photo(file: UploadFile = File(...), upscale: int = 1, fidelity: float = 0.5) -> JobCreateResponse:
    input_path = _save_upload(file)
    params = FaceEnhanceRequest(upscale=upscale, fidelity=fidelity)

    job_id = uuid.uuid4().hex
    task_photo_face_enhance.delay(job_id, str(input_path), params.model_dump())

    return JobCreateResponse(job_id=job_id, job_type=JobType.PHOTO_FACE_ENHANCE)


@router.post("/remove-background", response_model=JobCreateResponse)
async def remove_background(file: UploadFile = File(...), return_mask: bool = False) -> JobCreateResponse:
    input_path = _save_upload(file)
    params = BackgroundRemoveRequest(return_mask=return_mask)

    job_id = uuid.uuid4().hex
    task_photo_background_remove.delay(job_id, str(input_path), params.model_dump())

    return JobCreateResponse(job_id=job_id, job_type=JobType.PHOTO_BACKGROUND_REMOVE)


@router.post("/remove-object", response_model=JobCreateResponse)
async def remove_object(file: UploadFile = File(...), mask_path: str = "") -> JobCreateResponse:
    input_path = _save_upload(file)

    if not mask_path:
        raise HTTPException(status_code=400, detail="Не передан путь к маске (mask_path)")

    params = ObjectRemoveRequest(mask_path=mask_path)

    job_id = uuid.uuid4().hex
    task_photo_object_remove.delay(job_id, str(input_path), params.model_dump())

    return JobCreateResponse(job_id=job_id, job_type=JobType.PHOTO_OBJECT_REMOVE)


@router.post("/color-correct", response_model=JobCreateResponse)
async def color_correct_photo(
    file: UploadFile = File(...),
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    auto_white_balance: bool = False,
) -> JobCreateResponse:
    input_path = _save_upload(file)
    params = ColorCorrectRequest(
        brightness=brightness,
        contrast=contrast,
        saturation=saturation,
        auto_white_balance=auto_white_balance,
    )

    job_id = uuid.uuid4().hex
    task_photo_color_correct.delay(job_id, str(input_path), params.model_dump())

    return JobCreateResponse(job_id=job_id, job_type=JobType.PHOTO_COLOR_CORRECT)
