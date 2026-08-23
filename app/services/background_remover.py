from pathlib import Path

from PIL import Image
from rembg import new_session, remove

from app.services.base import BaseService


class BackgroundRemoverService(BaseService):
    """Удаление фона с изображения (модели семейства RMBG / U2Net через rembg)."""

    def __init__(self, model_dir: Path, model_name: str = "u2net"):
        super().__init__(model_dir)
        self.model_name = model_name

    def load_model(self) -> None:
        # rembg сам находит/скачивает веса по имени модели, self.model_dir
        # используется как явное указание на директорию с моделями проекта.
        self._model = new_session(self.model_name)

    def process(self, input_path: Path, output_path: Path, return_mask: bool = False, **kwargs) -> Path:
        self.ensure_loaded()

        with Image.open(input_path) as img:
            img = img.convert("RGBA")
            result = remove(img, session=self._model, only_mask=return_mask)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.save(output_path)

        return output_path
