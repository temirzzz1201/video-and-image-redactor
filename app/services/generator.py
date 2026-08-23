from pathlib import Path
from typing import Optional

import torch

from app.services.base import BaseService


class GeneratorService(BaseService):
    """
    Генерация изображений по текстовому промпту (text-to-image).

    Использует diffusers (Stable Diffusion). Если в self.model_dir лежат
    локальные веса — модель загружается из них, иначе используется
    self.model_id (веса будут скачаны с Hugging Face Hub при первом запуске).
    """

    def __init__(self, model_dir: Path, model_id: str = "runwayml/stable-diffusion-v1-5"):
        super().__init__(model_dir)
        self.model_id = model_id
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def load_model(self) -> None:
        from diffusers import StableDiffusionPipeline

        self.model_dir.mkdir(parents=True, exist_ok=True)
        has_local_weights = any(self.model_dir.glob("*"))
        source = str(self.model_dir) if has_local_weights else self.model_id

        self._model = StableDiffusionPipeline.from_pretrained(
            source,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            safety_checker=None,
        ).to(self.device)

    def process(
        self,
        input_path: Optional[Path],
        output_path: Path,
        prompt: str = "",
        negative_prompt: str = "",
        width: int = 512,
        height: int = 512,
        steps: int = 30,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        **kwargs,
    ) -> Path:
        if not prompt:
            raise ValueError("Промпт (prompt) не может быть пустым")

        self.ensure_loaded()

        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)

        result = self._model(
            prompt=prompt,
            negative_prompt=negative_prompt or None,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator,
        )

        image = result.images[0]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)

        return output_path
