import shutil
from pathlib import Path
from typing import Tuple

import cv2

from app.core.config import settings
from app.core.logging import logger
from app.services.color_processor import ColorProcessorService
from app.services.face_enhancer import FaceEnhancerService
from app.services.frame_interpolator import FrameInterpolatorService
from app.services.upscaler import UpscalerService
from app.utils.ffmpeg import extract_audio, extract_frames, frames_to_video, get_video_fps, mux_audio


class VideoProcessorService:
    """
    Оркестратор обработки видео: извлекает кадры через ffmpeg, прогоняет их
    через нужные сервисы (upscaler / face_enhancer / interpolator / color_processor),
    собирает видео обратно и восстанавливает звуковую дорожку.
    """

    def __init__(
        self,
        upscaler: UpscalerService,
        face_enhancer: FaceEnhancerService,
        interpolator: FrameInterpolatorService,
        color_processor: ColorProcessorService,
    ):
        self.upscaler = upscaler
        self.face_enhancer = face_enhancer
        self.interpolator = interpolator
        self.color_processor = color_processor

    def _prepare_job_dirs(self, job_id: str) -> Tuple[Path, Path]:
        frames_dir = settings.TEMP_DIR / "frames" / job_id
        out_frames_dir = settings.TEMP_DIR / "frames" / f"{job_id}_out"
        frames_dir.mkdir(parents=True, exist_ok=True)
        out_frames_dir.mkdir(parents=True, exist_ok=True)
        return frames_dir, out_frames_dir

    def _finalize(self, job_id: str, input_path: Path, output_path: Path, out_frames_dir: Path, fps: float) -> Path:
        """Собирает кадры из out_frames_dir в видео и домешивает исходный звук."""
        audio_path = settings.TEMP_DIR / "jobs" / f"{job_id}_audio.aac"
        has_audio = extract_audio(input_path, audio_path)

        silent_output = settings.TEMP_DIR / "jobs" / f"{job_id}_silent.mp4"
        frames_to_video(out_frames_dir, silent_output, fps=fps)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        if has_audio:
            mux_audio(silent_output, audio_path, output_path)
        else:
            shutil.move(str(silent_output), str(output_path))

        return output_path

    def upscale_video(
        self, job_id: str, input_path: Path, output_path: Path, scale: int = 2, face_enhance: bool = False
    ) -> Path:
        frames_dir, out_frames_dir = self._prepare_job_dirs(job_id)
        fps = get_video_fps(input_path)

        logger.info(f"[{job_id}] Извлечение кадров из {input_path}")
        frame_paths = extract_frames(input_path, frames_dir)

        for i, frame_path in enumerate(frame_paths):
            frame = cv2.imread(str(frame_path))
            processed = self.upscaler.process_frame(frame, scale=scale)

            processed = self.upscaler.enhance_details(
                processed,
                amount=0.25,
                sigma=1.0,
            )

            if face_enhance:
                processed = self.face_enhancer.process_frame(processed)

            cv2.imwrite(str(out_frames_dir / frame_path.name), processed)

            if i % 50 == 0:
                logger.info(f"[{job_id}] Обработано кадров: {i + 1}/{len(frame_paths)}")

        result = self._finalize(job_id, input_path, output_path, out_frames_dir, fps)
        self._cleanup(frames_dir, out_frames_dir)
        return result

    def interpolate_video(self, job_id: str, input_path: Path, output_path: Path, target_fps: int = 60) -> Path:
        frames_dir, out_frames_dir = self._prepare_job_dirs(job_id)
        original_fps = get_video_fps(input_path)

        multiplier = max(1, round(target_fps / original_fps))

        frame_paths = extract_frames(input_path, frames_dir)
        frames = [cv2.imread(str(p)) for p in frame_paths]

        logger.info(f"[{job_id}] Интерполяция {len(frames)} кадров с множителем x{multiplier}")
        interpolated = self.interpolator.interpolate_sequence(frames, target_multiplier=multiplier)

        for i, frame in enumerate(interpolated):
            cv2.imwrite(str(out_frames_dir / f"frame_{i:08d}.png"), frame)

        result = self._finalize(job_id, input_path, output_path, out_frames_dir, original_fps * multiplier)
        self._cleanup(frames_dir, out_frames_dir)
        return result

    def color_correct_video(
        self,
        job_id: str,
        input_path: Path,
        output_path: Path,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
    ) -> Path:
        frames_dir, out_frames_dir = self._prepare_job_dirs(job_id)
        fps = get_video_fps(input_path)

        frame_paths = extract_frames(input_path, frames_dir)

        for frame_path in frame_paths:
            frame = cv2.imread(str(frame_path))
            processed = self.color_processor.process_frame(
                frame, brightness=brightness, contrast=contrast, saturation=saturation,
            )
            cv2.imwrite(str(out_frames_dir / frame_path.name), processed)

        result = self._finalize(job_id, input_path, output_path, out_frames_dir, fps)
        self._cleanup(frames_dir, out_frames_dir)
        return result

    @staticmethod
    def _cleanup(*dirs: Path) -> None:
        for d in dirs:
            shutil.rmtree(d, ignore_errors=True)
