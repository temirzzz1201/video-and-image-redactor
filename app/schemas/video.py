from pydantic import BaseModel, Field


class VideoUpscaleRequest(BaseModel):
    scale: int = Field(2, ge=1, le=4)
    face_enhance: bool = Field(False)


class VideoInterpolateRequest(BaseModel):
    target_fps: int = Field(60, ge=1, le=240)


class VideoColorCorrectRequest(BaseModel):
    brightness: float = Field(1.0, ge=0.0, le=3.0)
    contrast: float = Field(1.0, ge=0.0, le=3.0)
    saturation: float = Field(1.0, ge=0.0, le=3.0)


class VideoJobResponse(BaseModel):
    job_id: str
    status: str
