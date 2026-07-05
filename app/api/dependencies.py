#app/api/dependencies.py
from fastapi import Header

from app.core.config import settings
from app.core.security import validator
from fastapi import Header, HTTPException, status, Request


async def require_api_key(
    x_api_key: str = Header(alias="X-API-Key"),
):
    return validator.validate(x_api_key)


async def get_api_key(
    x_api_key: str = Header(alias="X-API-Key"),
) -> str:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )
    if x_api_key not in settings.allowed_api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return x_api_key