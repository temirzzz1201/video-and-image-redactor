# VideoEnhancer

AI-редактор фото и видео: апскейл, улучшение лиц, удаление фона/объектов,
цветокоррекция, интерполяция кадров и генерация изображений по тексту.

## Структура проекта

```
VideoEnhancer/
├── app/
│   ├── api/                 # HTTP-слой (FastAPI роуты, DI)
│   │   ├── deps.py
│   │   └── routes/
│   │       ├── photo.py
│   │       ├── video.py
│   │       └── jobs.py
│   ├── core/                 # конфиг и логирование
│   │   ├── config.py
│   │   └── logging.py
│   ├── schemas/               # Pydantic DTO
│   │   ├── job.py
│   │   ├── photo.py
│   │   └── video.py
│   ├── services/               # бизнес-логика обработки
│   │   ├── base.py
│   │   ├── upscaler.py
│   │   ├── face_enhancer.py
│   │   ├── background_remover.py
│   │   ├── object_remover.py
│   │   ├── color_processor.py
│   │   ├── frame_interpolator.py
│   │   ├── generator.py
│   │   ├── photo_editor.py
│   │   └── video_processor.py
│   ├── utils/
│   │   ├── ffmpeg.py
│   │   └── files.py
│   ├── workers/                # Celery
│   │   ├── celery_app.py
│   │   └── tasks.py
│   └── main.py
├── data/                        # рантайм-данные (в .gitignore)
│   ├── input/{photos,videos}
│   ├── output/{photos,video}
│   ├── temp/{frames,jobs,previews}
│   └── logs/app.log
├── models/                      # веса моделей (в .gitignore)
│   ├── codeformer/
│   ├── gfpgan/GFPGANv1.4.pth
│   ├── realesrgan/RealESRGAN_x2plus.pth
│   ├── rmbg/
│   └── video/
├── frontend/
├── third_party/Real-ESRGAN/
├── scripts/
├── requirements.txt
├── start.sh
└── .gitignore
```

## Запуск

Перед запуском нужны:

- **Redis** (брокер и backend Celery): `redis-server`
- **ffmpeg** в PATH (для видео-пайплайна)
- Веса моделей, положенные в соответствующие папки `models/`:
  - `models/realesrgan/RealESRGAN_x2plus.pth`
  - `models/gfpgan/GFPGANv1.4.pth`

```bash
chmod +x start.sh
./start.sh
```

Это создаст venv, установит зависимости, запустит Celery-воркер в фоне
и поднимет FastAPI на `http://localhost:8000`.

Документация API (Swagger) доступна на `http://localhost:8000/docs`.

## Основные эндпоинты

| Метод | Путь                           | Описание                  |
| ----- | ------------------------------ | ------------------------- |
| POST  | `/api/photo/upscale`           | Апскейл фото              |
| POST  | `/api/photo/face-enhance`      | Улучшение лиц на фото     |
| POST  | `/api/photo/remove-background` | Удаление фона             |
| POST  | `/api/photo/remove-object`     | Удаление объекта по маске |
| POST  | `/api/photo/color-correct`     | Цветокоррекция фото       |
| POST  | `/api/video/upscale`           | Апскейл видео             |
| POST  | `/api/video/interpolate`       | Повышение FPS видео       |
| POST  | `/api/video/color-correct`     | Цветокоррекция видео      |
| GET   | `/api/jobs/{job_id}`           | Статус фоновой задачи     |

Все операции асинхронные: эндпоинт сразу возвращает `job_id`,
а результат проверяется через `/api/jobs/{job_id}`.

curl -X POST "http://127.0.0.1:8000/api/video/upscale?scale=2&face_enhance=false" \
 -F "file=@/home/zero/Desktop/VideoEnhancer/data/input/videos/test.mp4"
