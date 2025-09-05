from fastapi import APIRouter
from .expense_routes import router as expense_router
from .revenue_routes import router as revenue_router

# Create main planning router
router = APIRouter(tags=["Planning"])

# Include sub-routers
router.include_router(expense_router)
router.include_router(revenue_router)

__all__ = ["router"]