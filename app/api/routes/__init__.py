from fastapi import APIRouter

from app.api.routes import jobs, photo, video

api_router = APIRouter()
api_router.include_router(photo.router)
api_router.include_router(video.router)
api_router.include_router(jobs.router)
