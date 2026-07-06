from fastapi import APIRouter
from app.api.v1 import auth
from app.api.v1 import tasks

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
from app.api.v1 import datasets

api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
