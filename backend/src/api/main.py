from fastapi import FastAPI
from pydantic import BaseModel


class HealthResponse(BaseModel):
    healthy: bool
    service: str
    version: str


app = FastAPI(
    title="Verity API",
    version="0.1.0",
    description="UXR Platform Backend",
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(healthy=True, service="verity-backend", version="0.1.0")
