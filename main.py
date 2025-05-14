from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
import models
from database import engine

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Student Exam Room Assignment API",
    description="API for optimally assigning students to exam rooms",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include all routes
app.include_router(router, prefix="/api/v1")
    
@app.get("/")
def read_root():
    return {"message": "Welcome to the Student Exam Room Assignment API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
