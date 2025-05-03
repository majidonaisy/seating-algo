from database import engine
import models

# Create all tables defined in models.py
models.Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")