from pathlib import Path

import cv2

from app.services.base import BaseService


class ObjectRemoverService(BaseService):
    """
    Удаление объектов с изображения по бинарной маске.

    По умолчанию используется классический inpainting OpenCV (алгоритм Telea),
    который не требует весов модели и работает быстро на CPU. Для более
    качественного результата на сложных сценах сюда можно подключить модель
    LaMa — положить её веса в self.model_dir и переопределить load_model/process.
    """

    def load_model(self) -> None:
        # Классический inpainting не требует загрузки внешних весов.
        self._model = "opencv-telea"

    def process(self, input_path: Path, output_path: Path, mask_path: str = "", **kwargs) -> Path:
        self.ensure_loaded()

        if not mask_path:
            raise ValueError("Не указан путь к маске (mask_path)")

        img = cv2.imread(str(input_path), cv2.IMREAD_COLOR)
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)

        if img is None:
            raise ValueError(f"Не удалось прочитать изображение: {input_path}")
        if mask is None:
            raise ValueError(f"Не удалось прочитать маску: {mask_path}")

        if mask.shape[:2] != img.shape[:2]:
            mask = cv2.resize(mask, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)

        _, binary_mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

        result = cv2.inpaint(img, binary_mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), result)

        return output_path
