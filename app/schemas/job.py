from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class JobType(str, Enum):
    PHOTO_UPSCALE = "photo_upscale"
    PHOTO_FACE_ENHANCE = "photo_face_enhance"
    PHOTO_BACKGROUND_REMOVE = "photo_background_remove"
    PHOTO_OBJECT_REMOVE = "photo_object_remove"
    PHOTO_COLOR_CORRECT = "photo_color_correct"
    VIDEO_UPSCALE = "video_upscale"
    VIDEO_FACE_ENHANCE = "video_face_enhance"
    VIDEO_INTERPOLATE = "video_interpolate"
    VIDEO_COLOR_CORRECT = "video_color_correct"
    GENERATE_IMAGE = "generate_image"


class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus = JobStatus.PENDING
    job_type: JobType


class JobStatusResponse(BaseModel):
    job_id: str
    job_type: JobType
    status: JobStatus
    progress: float = Field(0.0, ge=0.0, le=100.0)
    result_path: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    meta: Dict[str, Any] = Field(default_factory=dict)
