from app.main import app


@app.get("/")
async def root():
    return {"message": "API Gateway is running"}
