import shutil
import uuid
from pathlib import Path
from typing import Optional


def unique_filename(original_name: str) -> str:
    """Генерирует уникальное имя файла, сохраняя оригинальное расширение."""
    ext = Path(original_name).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"


def safe_copy(src: Path, dest_dir: Path, new_name: Optional[str] = None) -> Path:
    """Копирует файл в dest_dir, создавая директорию при необходимости."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / (new_name or src.name)
    shutil.copy2(src, dest)
    return dest


def cleanup_dir(path: Path, keep_dir: bool = True) -> None:
    """Полностью очищает содержимое директории."""
    if not path.exists():
        return
    for item in path.iterdir():
        if item.is_dir():
            shutil.rmtree(item, ignore_errors=True)
        else:
            item.unlink(missing_ok=True)
    if not keep_dir:
        path.rmdir()


def human_readable_size(num_bytes: int) -> str:
    """Переводит размер в байтах в удобочитаемый вид (KB/MB/GB)."""
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
