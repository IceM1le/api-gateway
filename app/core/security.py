from fastapi import HTTPException, status

from app.core.config import settings


class APIKeyValidator:

    def validate(self, api_key: str) -> str:
        if api_key not in settings.api_keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )

        return api_key


validator = APIKeyValidator()