from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

from app.core.config import settings
from app.services.base import BaseService


class UpscalerService(BaseService):
    """
    Real-ESRGAN upscaler.

    Используется как для отдельных изображений,
    так и для кадров видео.

    Модель:
        RealESRGAN_x2plus.pth

    GPU:
        NVIDIA CUDA, если доступна.

    CPU:
        используется автоматически, если CUDA недоступна.
    """

    def __init__(
        self,
        model_dir: Path,
        model_name: str = "RealESRGAN_x2plus.pth",
    ):
        super().__init__(model_dir)

        self.model_name = model_name

        # ---------------------------------------------------------
        # Device
        # ---------------------------------------------------------

        if settings.DEVICE == "cuda" and torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"

        # ---------------------------------------------------------
        # GPU information
        # ---------------------------------------------------------

        if self.device == "cuda":
            self.gpu_name = torch.cuda.get_device_name(0)

            print("=" * 60)
            print("Real-ESRGAN")
            print("=" * 60)
            print("Device:", self.device)
            print("GPU:", self.gpu_name)
            print("PyTorch:", torch.__version__)
            print("CUDA:", torch.version.cuda)
            print("=" * 60)

        else:
            self.gpu_name = None

            print("=" * 60)
            print("Real-ESRGAN")
            print("=" * 60)
            print("Device: CPU")
            print("WARNING: CUDA недоступна")
            print("=" * 60)

    def load_model(self) -> None:
        """
        Загружает Real-ESRGAN один раз.

        Модель загружается только при первом вызове ensure_loaded().
        """

        model_path = self.model_dir / self.model_name

        # ---------------------------------------------------------
        # Проверяем модель
        # ---------------------------------------------------------

        if not model_path.exists():
            raise FileNotFoundError(
                f"\n"
                f"Файл модели не найден:\n"
                f"{model_path}\n\n"
                f"Ожидается:\n"
                f"{self.model_name}\n"
            )

        print()
        print("=" * 60)
        print("Загрузка Real-ESRGAN")
        print("=" * 60)
        print("Model:", model_path)
        print("Device:", self.device)

        # ---------------------------------------------------------
        # Архитектура Real-ESRGAN x2
        # ---------------------------------------------------------

        arch = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=2,
        )

        # ---------------------------------------------------------
        # Tile
        # ---------------------------------------------------------
        #
        # RTX 3050 Ti Laptop имеет 4 GB VRAM.
        #
        # 256 — хороший стартовый размер.
        #
        # Если будет CUDA out of memory:
        #
        #   256 -> 192 -> 128
        #
        # Если всё работает и VRAM позволяет:
        #
        #   256 -> 320
        #
        # Но для начала оставляем 256.
        #

        tile_size = 256
        tile_pad = 20

        # ---------------------------------------------------------
        # FP16
        # ---------------------------------------------------------
        #
        # На NVIDIA CUDA используем half precision.
        #
        # Это значительно уменьшает использование VRAM.
        #

        use_half = self.device == "cuda"

        print("Tile:", tile_size)
        print("Tile pad:", tile_pad)
        print("FP16:", use_half)

        # ---------------------------------------------------------
        # Создаём RealESRGANer
        # ---------------------------------------------------------

        self._model = RealESRGANer(
            scale=2,
            model_path=str(model_path),
            model=arch,
            tile=tile_size,
            tile_pad=tile_pad,
            pre_pad=0,
            half=use_half,
            device=self.device,
        )

        # ---------------------------------------------------------
        # Проверяем CUDA
        # ---------------------------------------------------------

        if self.device == "cuda":

            torch.cuda.empty_cache()

            allocated = torch.cuda.memory_allocated(0) / 1024 / 1024
            reserved = torch.cuda.memory_reserved(0) / 1024 / 1024

            print()
            print("GPU:", torch.cuda.get_device_name(0))
            print(f"VRAM allocated: {allocated:.0f} MB")
            print(f"VRAM reserved:  {reserved:.0f} MB")

        print()
        print("Real-ESRGAN: модель загружена")
        print("=" * 60)
        print()

    def process(
            self,
            input_path: Path,
            output_path: Path,
            scale: int = 2,
            **kwargs,
        ) -> Path:
            """Обрабатывает изображение и сохраняет результат. """

            self.ensure_loaded()

            # ---------------------------------------------------------
            # Читаем изображение
            # ---------------------------------------------------------

            if input_path.suffix.lower() == ".avif":
                # AVIF читаем через Pillow
                with Image.open(input_path) as pil_img:
                    pil_img = pil_img.convert("RGB")
                    img = np.array(pil_img)

                # Pillow: RGB
                # OpenCV / Real-ESRGAN: BGR
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            else:
                # JPG / PNG / WEBP / BMP
                img = cv2.imread(
                    str(input_path),
                    cv2.IMREAD_UNCHANGED,
                )

            if img is None:
                raise ValueError(
                    f"Не удалось прочитать изображение:\n"
                    f"{input_path}"
                )

            # ---------------------------------------------------------
            # Real-ESRGAN
            # ---------------------------------------------------------

            output, _ = self._model.enhance(
                img,
                outscale=scale,
            )

            # ---------------------------------------------------------
            # Сохраняем
            # ---------------------------------------------------------

            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            success = cv2.imwrite(
                str(output_path),
                output,
            )

            if not success:
                raise RuntimeError(
                    f"Не удалось сохранить изображение:\n"
                    f"{output_path}"
                )

            return output_path

    def process_frame(
        self,
        frame: np.ndarray,
        scale: int = 2,
    ) -> np.ndarray:
        """
        Обрабатывает один кадр видео в памяти.

        Это основной метод, который используется
        VideoProcessorService.
        """

        self.ensure_loaded()

        if frame is None:
            raise ValueError(
                "Получен пустой кадр."
            )

        if not isinstance(frame, np.ndarray):
            raise TypeError(
                f"Ожидался numpy.ndarray, получен: "
                f"{type(frame)}"
            )

        # ---------------------------------------------------------
        # Real-ESRGAN
        # ---------------------------------------------------------

        output, _ = self._model.enhance(
            frame,
            outscale=scale,
        )

        # ---------------------------------------------------------
        # Очищаем неиспользуемую CUDA память
        # ---------------------------------------------------------
        #
        # Не вызываем empty_cache() после каждого кадра:
        # это сильно замедлит видео.
        #
        # Поэтому память чистится только при необходимости
        # или после всей обработки.
        #

        return output

    def enhance_details(
        self,
        frame: np.ndarray,
        amount: float = 0.25,
        sigma: float = 1.0,
    ) -> np.ndarray:
        """
        Лёгкое повышение локальной резкости после Real-ESRGAN.

        amount:
            0.15 — очень мягко
            0.25 — рекомендованный старт
            0.35 — заметно
            0.50+ — уже агрессивно
        """

        if frame is None:
            raise ValueError("Получен пустой кадр.")

        blurred = cv2.GaussianBlur(
            frame,
            (0, 0),
            sigma,
        )

        sharpened = cv2.addWeighted(
            frame,
            1.0 + amount,
            blurred,
            -amount,
            0,
        )

        return np.clip(sharpened, 0, 255).astype(np.uint8)

    def clear_cuda_cache(self) -> None:
        """
        Очищает неиспользуемую память CUDA.
        """

        if self.device == "cuda":
            torch.cuda.empty_cache()

    def get_gpu_info(self) -> dict:
        """
        Возвращает информацию о GPU.
        """

        if self.device != "cuda":
            return {
                "device": "cpu",
                "cuda": False,
                "gpu": None,
            }

        return {
            "device": "cuda",
            "cuda": True,
            "gpu": torch.cuda.get_device_name(0),
            "cuda_version": torch.version.cuda,
            "pytorch_version": torch.__version__,
            "memory_allocated_mb": round(
                torch.cuda.memory_allocated(0) / 1024 / 1024,
                2,
            ),
            "memory_reserved_mb": round(
                torch.cuda.memory_reserved(0) / 1024 / 1024,
                2,
            ),
        }
