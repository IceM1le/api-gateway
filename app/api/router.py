from fastapi import APIRouter

from app.api.routers.gateway import router as gateway_router
from app.api.routers.health import router as health_router
from app.api.routers.metrics import router as metrics_router
router = APIRouter()



router.include_router(metrics_router)
router.include_router(gateway_router)