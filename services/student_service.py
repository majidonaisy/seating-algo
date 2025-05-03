from sqlalchemy.orm import Session
from typing import List, Optional
import crud
from models import StudentIn, StudentOut


def create_student(db: Session, student: StudentIn):
    return crud.create_student(db, student.name, student.major)

def get_students(db: Session, skip: int = 0, limit: int = 100) -> List[StudentOut]:
    return crud.get_students(db, skip, limit)

def get_student(db: Session, student_id: int) -> StudentOut:
    return crud.get_student(db, student_id)

def update_student(db: Session, student_id: int, student: StudentIn) -> StudentOut:
    return crud.update_student(db, student_id, student.name, student.major)

def delete_student(db: Session, student_id: int) -> bool:
    return crud.delete_student(db, student_id)
