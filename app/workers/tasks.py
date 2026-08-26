from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from celery import states

from app.core.config import settings
from app.core.logging import logger
from app.schemas.job import JobStatus, JobStatusResponse, JobType
from app.services.background_remover import BackgroundRemoverService
from app.services.color_processor import ColorProcessorService
from app.services.face_enhancer import FaceEnhancerService
from app.services.frame_interpolator import FrameInterpolatorService
from app.services.object_remover import ObjectRemoverService
from app.services.upscaler import UpscalerService
from app.services.video_processor import VideoProcessorService
from app.workers.celery_app import celery_app

# Сервисы инициализируются один раз на процесс воркера и переиспользуются
# между задачами — это позволяет не перезагружать веса моделей каждый раз.
_upscaler = UpscalerService(model_dir=settings.REALESRGAN_DIR)
_face_enhancer = FaceEnhancerService(model_dir=settings.GFPGAN_DIR)
_background_remover = BackgroundRemoverService(model_dir=settings.RMBG_DIR)
_object_remover = ObjectRemoverService(model_dir=settings.MODELS_DIR / "lama")
_color_processor = ColorProcessorService(model_dir=settings.MODELS_DIR)
_interpolator = FrameInterpolatorService(model_dir=settings.VIDEO_MODELS_DIR)
_video_processor = VideoProcessorService(
    upscaler=_upscaler,
    face_enhancer=_face_enhancer,
    interpolator=_interpolator,
    color_processor=_color_processor,
)


def get_job_status(job_id: str) -> Optional[JobStatusResponse]:
    """Читает статус задачи из результата Celery по её id."""
    result = celery_app.AsyncResult(job_id)

    if result.state == states.PENDING:
        return None

    status_map = {
        states.PENDING: JobStatus.PENDING,
        states.STARTED: JobStatus.RUNNING,
        states.SUCCESS: JobStatus.SUCCESS,
        states.FAILURE: JobStatus.FAILED,
        states.RETRY: JobStatus.RUNNING,
    }

    info: Dict[str, Any] = result.info if isinstance(result.info, dict) else {}

    return JobStatusResponse(
        job_id=job_id,
        job_type=JobType(info.get("job_type", JobType.PHOTO_UPSCALE.value)),
        status=status_map.get(result.state, JobStatus.PENDING),
        progress=info.get("progress", 100.0 if result.successful() else 0.0),
        result_path=info.get("result_path"),
        error=str(result.result) if result.failed() else None,
        created_at=info.get("created_at", datetime.utcnow()),
        updated_at=datetime.utcnow(),
        meta=info,
    )


def _make_output_path(input_path: Path, output_root: Path, suffix: str) -> Path:
    return output_root / f"{input_path.stem}_{suffix}{input_path.suffix}"

def _cleanup_input_file(input_path: Path) -> None:
    """
    Удаляет временный файл, загруженный через API.
    Никогда не удаляет файлы из data/input.
    """
    try:
        if input_path.is_file() and settings.TEMP_DIR in input_path.parents:
            input_path.unlink()
            logger.info(f"Удалён временный файл: {input_path}")
    except Exception:
        logger.exception(f"Не удалось удалить временный файл: {input_path}")



@celery_app.task(bind=True, name="video.upscale")
def task_video_upscale(self, job_id: str, input_path: str, params: dict):
    in_path = Path(input_path)

    try:
        out_path = _make_output_path(
            in_path,
            settings.OUTPUT_DIR / "video",
            "upscaled",
        )

        result_path = _video_processor.upscale_video(
            job_id,
            in_path,
            out_path,
            scale=params.get("scale", 2),
            face_enhance=params.get("face_enhance", False),
        )

        return {
            "job_type": JobType.VIDEO_UPSCALE.value,
            "result_path": str(result_path),
            "progress": 100.0,
        }

    except Exception as exc:
        logger.exception(
            f"[{job_id}] Ошибка апскейла видео"
        )
        raise exc

    finally:
        _cleanup_input_file(in_path)

@celery_app.task(bind=True, name="photo.upscale")
def task_photo_upscale(self, job_id: str, input_path: str, params: dict):
    try:
        in_path = Path(input_path)

        out_path = _make_output_path(
            in_path,
            settings.OUTPUT_DIR / "photos",
            "upscaled",
        )

        result_path = _upscaler.process(
            in_path,
            out_path,
            scale=params.get("scale", 2),
        )

        if params.get("face_enhance"):
            result_path = _face_enhancer.process(
                result_path,
                result_path,
            )

        return {
            "job_type": JobType.PHOTO_UPSCALE.value,
            "result_path": str(result_path),
            "progress": 100.0,
        }

    except Exception as exc:
        logger.exception(
            f"[{job_id}] Ошибка апскейла фото"
        )
        raise exc

@celery_app.task(bind=True, name="photo.face_enhance")
def task_photo_face_enhance(self, job_id: str, input_path: str, params: dict):
    try:
        in_path = Path(input_path)
        out_path = _make_output_path(in_path, settings.OUTPUT_DIR / "photos", "face_enhanced")

        result_path = _face_enhancer.process(
            in_path, out_path,
            upscale=params.get("upscale", 1),
            fidelity=params.get("fidelity", 0.5),
        )

        return {"job_type": JobType.PHOTO_FACE_ENHANCE.value, "result_path": str(result_path), "progress": 100.0}
    except Exception as exc:
        logger.exception(f"[{job_id}] Ошибка улучшения лиц")
        raise exc


@celery_app.task(bind=True, name="photo.background_remove")
def task_photo_background_remove(self, job_id: str, input_path: str, params: dict):
    try:
        in_path = Path(input_path)
        out_path = _make_output_path(in_path, settings.OUTPUT_DIR / "photos", "no_bg").with_suffix(".png")

        result_path = _background_remover.process(in_path, out_path, return_mask=params.get("return_mask", False))

        return {"job_type": JobType.PHOTO_BACKGROUND_REMOVE.value, "result_path": str(result_path), "progress": 100.0}
    except Exception as exc:
        logger.exception(f"[{job_id}] Ошибка удаления фона")
        raise exc


@celery_app.task(bind=True, name="photo.object_remove")
def task_photo_object_remove(self, job_id: str, input_path: str, params: dict):
    try:
        in_path = Path(input_path)
        out_path = _make_output_path(in_path, settings.OUTPUT_DIR / "photos", "obj_removed")

        result_path = _object_remover.process(in_path, out_path, mask_path=params.get("mask_path", ""))

        return {"job_type": JobType.PHOTO_OBJECT_REMOVE.value, "result_path": str(result_path), "progress": 100.0}
    except Exception as exc:
        logger.exception(f"[{job_id}] Ошибка удаления объекта")
        raise exc


@celery_app.task(bind=True, name="photo.color_correct")
def task_photo_color_correct(self, job_id: str, input_path: str, params: dict):
    try:
        in_path = Path(input_path)
        out_path = _make_output_path(in_path, settings.OUTPUT_DIR / "photos", "color_corrected")

        result_path = _color_processor.process(
            in_path, out_path,
            brightness=params.get("brightness", 1.0),
            contrast=params.get("contrast", 1.0),
            saturation=params.get("saturation", 1.0),
            auto_white_balance=params.get("auto_white_balance", False),
        )

        return {"job_type": JobType.PHOTO_COLOR_CORRECT.value, "result_path": str(result_path), "progress": 100.0}
    except Exception as exc:
        logger.exception(f"[{job_id}] Ошибка цветокоррекции фото")
        raise exc


@celery_app.task(bind=True, name="video.upscale")
def task_video_upscale(self, job_id: str, input_path: str, params: dict):
    try:
        in_path = Path(input_path)
        out_path = _make_output_path(in_path, settings.OUTPUT_DIR / "video", "upscaled")

        result_path = _video_processor.upscale_video(
            job_id, in_path, out_path,
            scale=params.get("scale", 2),
            face_enhance=params.get("face_enhance", False),
        )

        return {"job_type": JobType.VIDEO_UPSCALE.value, "result_path": str(result_path), "progress": 100.0}
    except Exception as exc:
        logger.exception(f"[{job_id}] Ошибка апскейла видео")
        raise exc


@celery_app.task(bind=True, name="video.interpolate")
def task_video_interpolate(self, job_id: str, input_path: str, params: dict):
    try:
        in_path = Path(input_path)
        out_path = _make_output_path(in_path, settings.OUTPUT_DIR / "video", "interpolated")

        result_path = _video_processor.interpolate_video(
            job_id, in_path, out_path, target_fps=params.get("target_fps", 60),
        )

        return {"job_type": JobType.VIDEO_INTERPOLATE.value, "result_path": str(result_path), "progress": 100.0}
    except Exception as exc:
        logger.exception(f"[{job_id}] Ошибка интерполяции видео")
        raise exc


@celery_app.task(bind=True, name="video.color_correct")
def task_video_color_correct(self, job_id: str, input_path: str, params: dict):
    try:
        in_path = Path(input_path)
        out_path = _make_output_path(in_path, settings.OUTPUT_DIR / "video", "color_corrected")

        result_path = _video_processor.color_correct_video(
            job_id, in_path, out_path,
            brightness=params.get("brightness", 1.0),
            contrast=params.get("contrast", 1.0),
            saturation=params.get("saturation", 1.0),
        )

        return {"job_type": JobType.VIDEO_COLOR_CORRECT.value, "result_path": str(result_path), "progress": 100.0}
    except Exception as exc:
        logger.exception(f"[{job_id}] Ошибка цветокоррекции видео")
        raise exc
