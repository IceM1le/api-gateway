from app.core import rate_limiter
from app.main import app


@app.get("/")
async def root():
    return {"message": "API Gateway is running"}


@app.get("/test-rate")
async def test_rate():
    allowed = await rate_limiter.is_allowed("test-key-1")
    return {"allowed": allowed}
