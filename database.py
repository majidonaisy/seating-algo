from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Use SQLite for simplicity - replace with your preferred database URL
SQLALCHEMY_DATABASE_URL = "mssql+pyodbc://sa:s%40DB-utilities-server%4001100101%23@10.50.66.193:1433/?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&Encrypt=yes"

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