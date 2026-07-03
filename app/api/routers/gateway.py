from fastapi import APIRouter, Depends

from app.api.dependencies import require_api_key

router = APIRouter(
    prefix="/api",
    tags=["Gateway"],
)


@router.get("/test")
async def test(api_key: str = Depends(require_api_key)):
    return {
        "message": "Authentication successful",
        "client": api_key,
    }
