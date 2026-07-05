from fastapi import Header, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.dependencies import AsyncSessionLocal
from app.services.api_key_service import ApiKeyService


async def get_api_key(
        x_api_key: str = Header(alias="X-API-Key"),
        request: Request = None
) -> str:
    async with AsyncSessionLocal() as db:
        service = ApiKeyService(db)
        api_key = await service.validate(x_api_key)
        if not api_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

        request.state.api_key_obj = api_key
        return x_api_key
