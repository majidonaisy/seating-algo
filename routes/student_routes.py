from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import StudentIn, StudentOut
import services.student_service as student_service

router = APIRouter(
    prefix="/students",
    tags=["students"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentIn, db: Session = Depends(get_db)):
    return student_service.create_student(db, student)

@router.get("/", response_model=List[StudentOut])
def read_students(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    students = student_service.get_students(db, skip, limit)
    return students

@router.get("/{student_id}", response_model=StudentOut)
def read_student(student_id: int, db: Session = Depends(get_db)):
    student = student_service.get_student(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.put("/{student_id}", response_model=StudentOut)
def update_student(student_id: int, student: StudentIn, db: Session = Depends(get_db)):
    updated_student = student_service.update_student(db, student_id, student)
    if updated_student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return updated_student

@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    success = student_service.delete_student(db, student_id)
    if not success:
        raise HTTPException(status_code=404, detail="Student not found")
    return None
