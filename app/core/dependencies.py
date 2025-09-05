from typing import Annotated, Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.base import get_db

# Database dependency
AsyncSession = Annotated[Session, Depends(get_db)]

# Pagination dependencies
from fastapi import Query

def get_pagination_params(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return")
):
    return {"skip": skip, "limit": limit}

PaginationParams = Annotated[dict, Depends(get_pagination_params)]