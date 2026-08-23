from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.core.logging import logger


class BaseService(ABC):
    """Базовый класс для всех сервисов обработки изображений и видео."""

    def __init__(self, model_dir: Path):
        self.model_dir = Path(model_dir)
        self._model: Any = None
        self.logger = logger

    @abstractmethod
    def load_model(self) -> None:
        """Загружает веса модели в память (ленивая инициализация)."""
        raise NotImplementedError

    def ensure_loaded(self) -> None:
        """Гарантирует, что модель загружена перед использованием."""
        if self._model is None:
            self.logger.info(f"Загрузка модели для {self.__class__.__name__}...")
            self.load_model()
            self.logger.info(f"Модель для {self.__class__.__name__} загружена.")

    @abstractmethod
    def process(self, input_path: Path, output_path: Path, **kwargs) -> Path:
        """Основной метод обработки. Возвращает путь к результату."""
        raise NotImplementedError
