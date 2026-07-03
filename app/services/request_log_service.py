from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RequestLog


async def log_request(
    db: AsyncSession,
    client_key: str,
    endpoint: str,
    status_code: int,
    duration_ms: float,
):
    log = RequestLog(
        client_key=client_key,
        endpoint=endpoint,
        status_code=status_code,
        duration_ms=duration_ms,
    )

    db.add(log)
