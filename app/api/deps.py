from functools import lru_cache

from app.core.config import settings
from app.services.background_remover import BackgroundRemoverService
from app.services.color_processor import ColorProcessorService
from app.services.face_enhancer import FaceEnhancerService
from app.services.frame_interpolator import FrameInterpolatorService
from app.services.generator import GeneratorService
from app.services.object_remover import ObjectRemoverService
from app.services.photo_editor import PhotoEditorService
from app.services.upscaler import UpscalerService
from app.services.video_processor import VideoProcessorService


@lru_cache
def get_upscaler_service() -> UpscalerService:
    return UpscalerService(model_dir=settings.REALESRGAN_DIR)


@lru_cache
def get_face_enhancer_service() -> FaceEnhancerService:
    return FaceEnhancerService(model_dir=settings.GFPGAN_DIR)


@lru_cache
def get_background_remover_service() -> BackgroundRemoverService:
    return BackgroundRemoverService(model_dir=settings.RMBG_DIR)


@lru_cache
def get_object_remover_service() -> ObjectRemoverService:
    return ObjectRemoverService(model_dir=settings.MODELS_DIR / "lama")


@lru_cache
def get_color_processor_service() -> ColorProcessorService:
    return ColorProcessorService(model_dir=settings.MODELS_DIR)


@lru_cache
def get_frame_interpolator_service() -> FrameInterpolatorService:
    return FrameInterpolatorService(model_dir=settings.VIDEO_MODELS_DIR)


@lru_cache
def get_photo_editor_service() -> PhotoEditorService:
    return PhotoEditorService(
        upscaler=get_upscaler_service(),
        face_enhancer=get_face_enhancer_service(),
        background_remover=get_background_remover_service(),
        object_remover=get_object_remover_service(),
        color_processor=get_color_processor_service(),
    )


@lru_cache
def get_video_processor_service() -> VideoProcessorService:
    return VideoProcessorService(
        upscaler=get_upscaler_service(),
        face_enhancer=get_face_enhancer_service(),
        interpolator=get_frame_interpolator_service(),
        color_processor=get_color_processor_service(),
    )


@lru_cache
def get_generator_service() -> GeneratorService:
    return GeneratorService(model_dir=settings.MODELS_DIR / "generation")
