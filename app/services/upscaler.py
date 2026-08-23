from pathlib import Path

import cv2
import numpy as np
import torch
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

from app.core.config import settings
from app.services.base import BaseService


class UpscalerService(BaseService):
    """Апскейл изображений и отдельных кадров видео с помощью Real-ESRGAN."""

    def __init__(self, model_dir: Path, model_name: str = "RealESRGAN_x2plus.pth"):
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

        arch = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)

        self._model = RealESRGANer(
            scale=2,
            model_path=str(model_path),
            model=arch,
            tile=400,
            tile_pad=10,
            pre_pad=0,
            half=self.device == "cuda",
            device=self.device,
        )

    def process(self, input_path: Path, output_path: Path, scale: int = 2, **kwargs) -> Path:
        self.ensure_loaded()

        img = cv2.imread(str(input_path), cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ValueError(f"Не удалось прочитать изображение: {input_path}")

        output, _ = self._model.enhance(img, outscale=scale)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), output)

        return output_path

    def process_frame(self, frame: np.ndarray, scale: int = 2) -> np.ndarray:
        """Апскейл одного кадра в памяти (используется video_processor'ом, без записи на диск)."""
        self.ensure_loaded()
        output, _ = self._model.enhance(frame, outscale=scale)
        return output
