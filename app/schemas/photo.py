from typing import Optional

from pydantic import BaseModel, Field


class UpscaleRequest(BaseModel):
    scale: int = Field(2, ge=1, le=4, description="Во сколько раз увеличить изображение")
    face_enhance: bool = Field(False, description="Дополнительно улучшить лица после апскейла")


class UpscaleResponse(BaseModel):
    job_id: str
    output_path: Optional[str] = None


class FaceEnhanceRequest(BaseModel):
    upscale: int = Field(1, ge=1, le=4)
    fidelity: float = Field(0.5, ge=0.0, le=1.0, description="Баланс между качеством и похожестью на оригинал")


class BackgroundRemoveRequest(BaseModel):
    return_mask: bool = Field(False, description="Вернуть маску вместо результата с прозрачным фоном")


class ObjectRemoveRequest(BaseModel):
    mask_path: str = Field(..., description="Путь к бинарной маске удаляемого объекта")


class ColorCorrectRequest(BaseModel):
    brightness: float = Field(1.0, ge=0.0, le=3.0)
    contrast: float = Field(1.0, ge=0.0, le=3.0)
    saturation: float = Field(1.0, ge=0.0, le=3.0)
    auto_white_balance: bool = Field(False)


class PhotoProcessResponse(BaseModel):
    job_id: str
    output_path: Optional[str] = None
