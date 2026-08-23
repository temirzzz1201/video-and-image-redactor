from pathlib import Path

from app.services.background_remover import BackgroundRemoverService
from app.services.color_processor import ColorProcessorService
from app.services.face_enhancer import FaceEnhancerService
from app.services.object_remover import ObjectRemoverService
from app.services.upscaler import UpscalerService


class PhotoEditorService:
    """
    Оркестратор редактирования фото: объединяет отдельные сервисы
    (upscaler, face_enhancer, background_remover, object_remover, color_processor)
    в единый пайплайн обработки изображения.
    """

    def __init__(
        self,
        upscaler: UpscalerService,
        face_enhancer: FaceEnhancerService,
        background_remover: BackgroundRemoverService,
        object_remover: ObjectRemoverService,
        color_processor: ColorProcessorService,
    ):
        self.upscaler = upscaler
        self.face_enhancer = face_enhancer
        self.background_remover = background_remover
        self.object_remover = object_remover
        self.color_processor = color_processor

    def upscale(self, input_path: Path, output_path: Path, scale: int = 2, face_enhance: bool = False) -> Path:
        result_path = self.upscaler.process(input_path, output_path, scale=scale)

        if face_enhance:
            result_path = self.face_enhancer.process(result_path, result_path, upscale=1)

        return result_path

    def enhance_faces(self, input_path: Path, output_path: Path, upscale: int = 1, fidelity: float = 0.5) -> Path:
        return self.face_enhancer.process(input_path, output_path, upscale=upscale, fidelity=fidelity)

    def remove_background(self, input_path: Path, output_path: Path, return_mask: bool = False) -> Path:
        return self.background_remover.process(input_path, output_path, return_mask=return_mask)

    def remove_object(self, input_path: Path, output_path: Path, mask_path: str) -> Path:
        return self.object_remover.process(input_path, output_path, mask_path=mask_path)

    def color_correct(
        self,
        input_path: Path,
        output_path: Path,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        auto_white_balance: bool = False,
    ) -> Path:
        return self.color_processor.process(
            input_path,
            output_path,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            auto_white_balance=auto_white_balance,
        )
