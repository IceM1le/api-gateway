#app/api/dependencies.py
from fastapi import Header

from app.core.security import validator


async def require_api_key(
    x_api_key: str = Header(alias="X-API-Key"),
):
    return validator.validate(x_api_key)