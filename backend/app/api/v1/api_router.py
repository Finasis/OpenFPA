from app.api.v1.endpoints import health
from fastapi import APIRouter

api_router = APIRouter()

# Include the health router with a prefix
api_router.include_router(health.router, prefix="/health", tags=["health"])
