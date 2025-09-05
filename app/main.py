from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.models.base import engine
from app.models import models
from app.api.routes import router
from app.api.simple_analytics_routes import router as analytics_router
from app.api.planning import router as planning_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    models.Base.metadata.create_all(bind=engine)
    yield
    # Clean up on shutdown (if needed)

app = FastAPI(
    title="OpenFP&A API",
    description="Modern Financial Planning & Analysis System",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1/analytics")
app.include_router(planning_router, prefix="/api/v1/planning")

@app.get("/")
async def read_root():
    return {
        "message": "OpenFP&A API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )