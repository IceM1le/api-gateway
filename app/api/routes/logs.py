from fastapi import Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.router import router
from app.db.dependencies import get_db
from app.db.models import RequestLog


@router.get("/logs")
async def get_logs(
    client_key: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    query = select(RequestLog)

    if client_key:
        query = query.where(RequestLog.client_key == client_key)

    query = query.order_by(RequestLog.id.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    return result.scalars().all()
@router.get("/stats/{client_key}")
async def get_stats(client_key: str, db: AsyncSession = Depends(get_db)):

    result = await db.execute(
        select(
            func.count(RequestLog.id),
            func.avg(RequestLog.duration_ms),
            func.max(RequestLog.duration_ms),
            func.min(RequestLog.duration_ms),
        ).where(RequestLog.client_key == client_key)
    )

    total, avg, max_v, min_v = result.first()

    return {
        "client_key": client_key,
        "total_requests": total or 0,
        "avg_latency_ms": float(avg or 0),
        "max_latency_ms": float(max_v or 0),
        "min_latency_ms": float(min_v or 0),
    }
