from fastapi import FastAPI

from app.api.routes_admin import router as admin_router
from app.api.routes_aml import router as aml_router
from app.api.routes_requests import router as requests_router

app = FastAPI(title="TronSecure Compliance API", version="0.1.0")

app.include_router(aml_router, prefix="/api/v1")
app.include_router(requests_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
