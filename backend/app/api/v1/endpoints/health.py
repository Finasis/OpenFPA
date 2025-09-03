from typing import Annotated, Any, Dict

import redis
from app.core.config import settings
from app.core.database import get_db
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "FP&A Platform API",
        "version": settings.VERSION,
    }


@router.get("/ready", response_model=Dict[str, Any])
async def readiness_check(db: Annotated[Session, Depends(get_db)]):
    """
    Readiness check - verifies all dependencies are available.
    """
    checks = {"database": False, "redis": False}

    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        checks["database_error"] = str(e)

    # Check Redis
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        checks["redis"] = True
    except Exception as e:
        checks["redis_error"] = str(e)

    # Overall status
    all_healthy = all([checks["database"], checks["redis"]])

    return {"status": "ready" if all_healthy else "not ready", "checks": checks}


@router.get("/live", response_model=Dict[str, str])
async def liveness_check():
    """
    Liveness check - simple endpoint to verify the service is running.
    """
    return {"status": "alive"}
