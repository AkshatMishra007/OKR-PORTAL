import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ------------------------
# Load Environment Variables
# ------------------------
load_dotenv()

# ------------------------
# Database Configuration
# ------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:12345@localhost:5432/okr",
)

# ------------------------
# SQLAlchemy Engine
# ------------------------
engine = create_engine(
    DATABASE_URL, echo=True, pool_pre_ping=True  # Set to False in production
)

# ------------------------
# Base Model
# ------------------------
Base = declarative_base()

# ------------------------
# Database Session
# ------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ------------------------
# Dependency for FastAPI
# ------------------------
# change in the database


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


##ok we will provide the guide
