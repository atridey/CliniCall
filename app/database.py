from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Check for Vercel environment variables
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = os.getenv("POSTGRES_URL")

# If we are on a non-Windows environment (e.g. Vercel/Linux) and have no DB URL, fail fast
# This prevents falling back to SQLite which is read-only on Vercel
if os.name != "nt" and not SQLALCHEMY_DATABASE_URL:
    # Debug info
    print("DEBUG: Environment Variables Keys:", list(os.environ.keys()))
    raise RuntimeError("Deployment Error: No DATABASE_URL or POSTGRES_URL found. Please add the 'Vercel Postgres' integration in the Vercel Dashboard.")

# Fallback for local development (Windows)
if not SQLALCHEMY_DATABASE_URL:
    print("WARNING: Using local SQLite database.")
    SQLALCHEMY_DATABASE_URL = "sqlite:///./clinicall.db"

# Vercel provides postgres:// but SQLAlchemy needs postgresql://
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

if "sqlite" in SQLALCHEMY_DATABASE_URL:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
