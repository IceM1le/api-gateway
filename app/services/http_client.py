import aiohttp
from fastapi import HTTPException
from app.core.circuit_breaker import CircuitBreaker


class HttpClient:
    def __init__(self, circuit_breaker: CircuitBreaker):
        self.cb = circuit_breaker

    async def get(self, url: str):
        if not self.cb.allow_request():
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable (circuit open)"
            )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status >= 400:
                        raise Exception("Upstream error")

                    data = await resp.json()

            self.cb.success()
            return data

        except Exception:
            self.cb.failure()
            raise HTTPException(
                status_code=502,
                detail="Upstream service error"
            )