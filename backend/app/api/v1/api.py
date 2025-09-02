from app.api.v1.endpoints import health
from fastapi import APIRouter

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
# api_router.include_router(data_sources.router, prefix="/data-sources", tags=["data-sources"])
# api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
# api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
