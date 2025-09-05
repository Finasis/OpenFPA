from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from typing import Generator
from app.core.config import settings

DATABASE_URL = settings.get_database_url

# SQLAlchemy 2.0 style engine with future flag
engine = create_engine(
    DATABASE_URL, 
    echo=False, 
    pool_pre_ping=True,
    future=True  # Enable SQLAlchemy 2.0 behavior
)

# Session factory configuration
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False  # Better for async patterns
)

# SQLAlchemy 2.0 style declarative base
class Base(DeclarativeBase):
    pass

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()