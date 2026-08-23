import logging
import sys
from logging.handlers import RotatingFileHandler

from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Настраивает и возвращает единый логгер приложения."""
    logger = logging.getLogger("videoenhancer")

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    log_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    log_file_path = settings.LOGS_DIR / "app.log"
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    logger.propagate = False

    return logger


logger = setup_logging()
