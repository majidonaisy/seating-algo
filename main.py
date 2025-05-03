from fastapi import FastAPI
from routes import router

app = FastAPI(
    title="Student Exam Room Assignment API",
    description="API for optimally assigning students to exam rooms",
    version="1.0.0"
)

app.include_router(router)
