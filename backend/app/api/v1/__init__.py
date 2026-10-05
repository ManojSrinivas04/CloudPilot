from fastapi import APIRouter

from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.predict import router as predict_router
from backend.app.api.v1.recommendations import router as recommendations_router
from backend.app.api.v1.resources import router as resources_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(predict_router, tags=["Predictions"])
api_router.include_router(resources_router)
api_router.include_router(recommendations_router)

__all__ = ["api_router"]
