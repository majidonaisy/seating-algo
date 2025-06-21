from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Use SQLite for simplicity - replace with your preferred database URL
SQLALCHEMY_DATABASE_URL = "postgresql://distribution_cxzv_user:JYksx3GPf4iGQwKPXV3L155M7IIxU0yG@dpg-d1b9jauuk2gs739h1j90-a.oregon-postgres.render.com/distribution_cxzv"

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()