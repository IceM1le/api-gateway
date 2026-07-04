from fastapi import APIRouter

from app.services.health_service import HealthService

router = APIRouter()

service = HealthService()


@router.get("/health")
async def health():
    return await service.health()