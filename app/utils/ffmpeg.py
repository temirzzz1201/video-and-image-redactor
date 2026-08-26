import json
import subprocess
from pathlib import Path
from typing import List

from app.core.config import settings
from app.core.logging import logger


def _run(cmd: List[str]) -> subprocess.CompletedProcess:
    logger.debug(f"Выполнение команды: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Команда завершилась с ошибкой: {result.stderr}")
        raise RuntimeError(f"Ошибка выполнения ffmpeg/ffprobe: {result.stderr}")
    return result


def get_video_fps(video_path: Path) -> float:
    """Возвращает FPS видеофайла через ffprobe."""
    cmd = [
        settings.FFPROBE_BIN, "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate",
        "-of", "json", str(video_path),
    ]
    result = _run(cmd)
    data = json.loads(result.stdout)
    rate_str = data["streams"][0]["r_frame_rate"]
    num, den = rate_str.split("/")
    return float(num) / float(den)


def extract_frames(video_path: Path, output_dir: Path, pattern: str = "frame_%08d.png") -> List[Path]:
    """Разбивает видео на кадры-изображения в output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        settings.FFMPEG_BIN, "-y", "-i", str(video_path),
        str(output_dir / pattern),
    ]
    _run(cmd)
    return sorted(output_dir.glob("frame_*.png"))

def frames_to_video(
    frames_dir: Path,
    output_path: Path,
    fps: float,
    pattern: str = "frame_%08d.png",
) -> Path:
    """Собирает видео обратно из последовательности кадров."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        settings.FFMPEG_BIN,
        "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / pattern),

        # Качественное кодирование H.264
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",

        # Совместимость с большинством плееров
        "-pix_fmt", "yuv420p",

        str(output_path),
    ]

    _run(cmd)
    return output_path


def extract_audio(video_path: Path, output_path: Path) -> bool:
    """Извлекает аудиодорожку. Возвращает False, если у видео нет звука."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        settings.FFMPEG_BIN, "-y", "-i", str(video_path),
        "-vn", "-acodec", "copy", str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0


def mux_audio(video_path: Path, audio_path: Path, output_path: Path) -> Path:
    """Склеивает беззвучное видео с аудиодорожкой в один файл."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        settings.FFMPEG_BIN, "-y",
        "-i", str(video_path), "-i", str(audio_path),
        "-c:v", "copy", "-c:a", "aac", "-shortest",
        str(output_path),
    ]
    _run(cmd)
    return output_path
