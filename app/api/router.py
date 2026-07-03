from fastapi import APIRouter

from app.api.routers.gateway import router as gateway_router
from app.api.routers.health import router as health_router

router = APIRouter()

router.include_router(health_router)
router.include_router(gateway_router)