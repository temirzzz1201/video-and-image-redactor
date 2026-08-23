from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "VideoEnhancer"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    INPUT_DIR: Path = DATA_DIR / "input"
    OUTPUT_DIR: Path = DATA_DIR / "output"
    TEMP_DIR: Path = DATA_DIR / "temp"
    LOGS_DIR: Path = DATA_DIR / "logs"

    MODELS_DIR: Path = BASE_DIR / "models"
    CODEFORMER_DIR: Path = MODELS_DIR / "codeformer"
    GFPGAN_DIR: Path = MODELS_DIR / "gfpgan"
    REALESRGAN_DIR: Path = MODELS_DIR / "realesrgan"
    RMBG_DIR: Path = MODELS_DIR / "rmbg"
    VIDEO_MODELS_DIR: Path = MODELS_DIR / "video"

    ALLOWED_PHOTO_EXT: List[str] = [".jpg", ".jpeg", ".png", ".webp", ".bmp"]
    ALLOWED_VIDEO_EXT: List[str] = [".mp4", ".mov", ".avi", ".mkv", ".webm"]

    MAX_UPLOAD_SIZE_MB: int = 500

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    DEVICE: str = "cuda"  # "cuda" или "cpu"
    FFMPEG_BIN: str = "ffmpeg"
    FFPROBE_BIN: str = "ffprobe"

    def ensure_dirs(self) -> None:
        """Создаёт все рантайм-директории, если их ещё нет."""
        dirs_to_create = [
            self.INPUT_DIR / "photos",
            self.INPUT_DIR / "videos",
            self.OUTPUT_DIR / "photos",
            self.OUTPUT_DIR / "video",
            self.TEMP_DIR / "frames",
            self.TEMP_DIR / "jobs",
            self.TEMP_DIR / "previews",
            self.LOGS_DIR,
        ]
        for directory in dirs_to_create:
            directory.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
