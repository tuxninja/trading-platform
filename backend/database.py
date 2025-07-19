from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import logging

from config import config
from exceptions import DatabaseError

logger = logging.getLogger(__name__)

# Create engine with improved configuration
engine = create_engine(
    config.DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    } if config.DATABASE_URL.startswith("sqlite") else {},
    poolclass=StaticPool if config.DATABASE_URL.startswith("sqlite") else None,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,
    pool_recycle=3600
)

logger.info(f"Database engine created for: {config.DATABASE_URL}")

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get database session with error handling
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise DatabaseError(f"Database operation failed: {str(e)}")
    finally:
        db.close() 