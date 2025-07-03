

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from contextlib import contextmanager

# === Load environment variables ===
load_dotenv()

# === Database URL ===
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smart_quiz.db")

# === Engine configuration ===
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True
)

# === Session factory ===
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# === Base class for all ORM models ===
Base = declarative_base()

# === FastAPI-compatible DB dependency ===
def get_db():
    """
    Yields a database session for use in FastAPI routes.
    Automatically closes the session after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === Optional: Context manager for scripts/jobs ===
@contextmanager
def db_session():
    """
    Use this for standalone scripts or background tasks:
    with db_session() as db: ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
