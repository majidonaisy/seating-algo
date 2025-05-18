from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Use SQLite for simplicity - replace with your preferred database URL
SQLALCHEMY_DATABASE_URL = "postgresql://seatingdb_user:nRIjmpnUoQ7s6yAzTCFs1AxO9fkxJwpX@dpg-d0kp4nl6ubrc73bfpgug-a/seatingdb"

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