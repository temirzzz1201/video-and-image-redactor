from pathlib import Path

import cv2
import numpy as np
import torch
from gfpgan import GFPGANer

from app.core.config import settings
from app.services.base import BaseService


class FaceEnhancerService(BaseService):
    """Улучшение лиц на изображениях и кадрах видео с помощью GFPGAN."""

    def __init__(self, model_dir: Path, model_name: str = "GFPGANv1.4.pth"):
        super().__init__(model_dir)
        self.model_name = model_name
        self.device = "cuda" if (settings.DEVICE == "cuda" and torch.cuda.is_available()) else "cpu"

    def load_model(self) -> None:
        model_path = self.model_dir / self.model_name
        if not model_path.exists():
            raise FileNotFoundError(
                f"Файл весов модели не найден: {model_path}. "
                f"Скачайте {self.model_name} и положите его в {self.model_dir}"
            )

        self._model = GFPGANer(
            model_path=str(model_path),
            upscale=1,
            arch="clean",
            channel_multiplier=2,
            bg_upsampler=None,
            device=self.device,
        )

    def process(self, input_path: Path, output_path: Path, upscale: int = 1, fidelity: float = 0.5, **kwargs) -> Path:
        self.ensure_loaded()

        img = cv2.imread(str(input_path), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Не удалось прочитать изображение: {input_path}")

        self._model.upscale = upscale
        _, _, restored_img = self._model.enhance(
            img, has_aligned=False, only_center_face=False, paste_back=True, weight=fidelity,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), restored_img)

        return output_path

    def process_frame(self, frame: np.ndarray, fidelity: float = 0.5) -> np.ndarray:
        """Улучшение лиц на одном кадре в памяти (используется video_processor'ом)."""
        self.ensure_loaded()
        _, _, restored = self._model.enhance(
            frame, has_aligned=False, only_center_face=False, paste_back=True, weight=fidelity,
        )
        return restored
