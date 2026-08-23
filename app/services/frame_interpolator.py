from pathlib import Path
from typing import List

import cv2
import numpy as np

from app.services.base import BaseService


class FrameInterpolatorService(BaseService):
    """
    Интерполяция кадров для повышения FPS видео.

    Базовая реализация использует оптический поток Farneback для
    генерации промежуточных кадров — работает без GPU и без внешних весов.
    Для продакшн-качества сюда можно подключить модель RIFE, положив
    её веса в self.model_dir и переопределив load_model/interpolate_pair.
    """

    def load_model(self) -> None:
        # Оптический поток не требует предзагруженной модели.
        self._model = "farneback-optical-flow"

    def process(self, input_path: Path, output_path: Path, **kwargs) -> Path:
        raise NotImplementedError(
            "FrameInterpolatorService работает с последовательностями кадров через "
            "interpolate_sequence()/interpolate_pair(); полный видео-пайплайн "
            "собирается в VideoProcessorService."
        )

    def interpolate_pair(self, frame_a: np.ndarray, frame_b: np.ndarray, num_intermediate: int = 1) -> List[np.ndarray]:
        """Генерирует num_intermediate кадров между frame_a и frame_b."""
        self.ensure_loaded()

        gray_a = cv2.cvtColor(frame_a, cv2.COLOR_BGR2GRAY)
        gray_b = cv2.cvtColor(frame_b, cv2.COLOR_BGR2GRAY)

        flow = cv2.calcOpticalFlowFarneback(gray_a, gray_b, None, 0.5, 3, 15, 3, 5, 1.2, 0)

        h, w = frame_a.shape[:2]
        grid_x, grid_y = np.meshgrid(np.arange(w), np.arange(h))

        result_frames: List[np.ndarray] = []
        for i in range(1, num_intermediate + 1):
            t = i / (num_intermediate + 1)

            map_x = (grid_x + flow[..., 0] * t).astype(np.float32)
            map_y = (grid_y + flow[..., 1] * t).astype(np.float32)

            warped = cv2.remap(frame_a, map_x, map_y, interpolation=cv2.INTER_LINEAR)
            blended = cv2.addWeighted(warped, 1 - t, frame_b, t, 0)

            result_frames.append(blended)

        return result_frames

    def interpolate_sequence(self, frames: List[np.ndarray], target_multiplier: int = 2) -> List[np.ndarray]:
        """Увеличивает частоту кадров последовательности в target_multiplier раз."""
        if target_multiplier < 2:
            return frames

        num_intermediate = target_multiplier - 1
        result: List[np.ndarray] = []

        for i in range(len(frames) - 1):
            result.append(frames[i])
            result.extend(self.interpolate_pair(frames[i], frames[i + 1], num_intermediate))

        result.append(frames[-1])
        return result
