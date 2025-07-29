from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from challenge_api.app.config import Config

# Create engine with SQLAlchemy 2.0 style
engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
    poolclass=StaticPool,
    echo=False  # Set to True for SQL debugging
)

# Create session factory with SQLAlchemy 2.0 style
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create declarative base with SQLAlchemy 2.0 style
Base = declarative_base()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
