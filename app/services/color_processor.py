from pathlib import Path

import cv2
import numpy as np

from app.services.base import BaseService


class ColorProcessorService(BaseService):
    """Цветокоррекция изображений и кадров видео: яркость, контраст, насыщенность, баланс белого."""

    def load_model(self) -> None:
        # Цветокоррекция реализована на OpenCV/NumPy и не требует ML-модели.
        self._model = "cv2-color-pipeline"

    def process(
        self,
        input_path: Path,
        output_path: Path,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        auto_white_balance: bool = False,
        **kwargs,
    ) -> Path:
        self.ensure_loaded()

        img = cv2.imread(str(input_path), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Не удалось прочитать изображение: {input_path}")

        result = self.process_frame(
            img,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            auto_white_balance=auto_white_balance,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), result)

        return output_path

    def process_frame(
        self,
        frame: np.ndarray,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        auto_white_balance: bool = False,
    ) -> np.ndarray:
        """Применяет цветокоррекцию к одному кадру в памяти."""
        self.ensure_loaded()

        result = frame.astype(np.float32)

        if auto_white_balance:
            result = self._auto_white_balance(result)

        result = np.clip(result * brightness, 0, 255)

        mean = result.mean()
        result = np.clip((result - mean) * contrast + mean, 0, 255)

        hsv = cv2.cvtColor(result.astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[..., 1] = np.clip(hsv[..., 1] * saturation, 0, 255)
        result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        return result

    @staticmethod
    def _auto_white_balance(img: np.ndarray) -> np.ndarray:
        """Простой авто-баланс белого через растяжку перцентилей по каждому каналу."""
        result = img.copy()
        for channel in range(3):
            channel_data = result[:, :, channel]
            low, high = np.percentile(channel_data, (1, 99))
            if high - low < 1e-5:
                continue
            result[:, :, channel] = np.clip((channel_data - low) * 255.0 / (high - low), 0, 255)
        return result
