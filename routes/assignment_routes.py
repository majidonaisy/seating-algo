from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import AssignRequest, AssignResponse, AssignmentOut, AssignmentIn
import services.assignment_service as assignment_service

router = APIRouter(
    prefix="/assignments",
    tags=["assignments"],
    responses={404: {"description": "Not found"}},
)

@router.post("/assign", response_model=AssignResponse)
def assign(req: AssignRequest, db: Session = Depends(get_db)):
    assignments = assignment_service.process_assignment(db, req)
    if assignments is None:
        raise HTTPException(status_code=400, detail="No valid arrangement found within time limit")
    
    return AssignResponse(assignments=assignments)

@router.post("/", response_model=AssignmentOut)
def create_assignment(assignment: AssignmentIn, db: Session = Depends(get_db)):
    return assignment_service.create_assignment(db, assignment)

@router.get("/", response_model=List[AssignmentOut])
def read_assignments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    assignments = assignment_service.get_assignments(db, skip, limit)
    return assignments

@router.get("/student/{student_id}", response_model=List[AssignmentOut])
def read_student_assignments(student_id: int, db: Session = Depends(get_db)):
    assignments = assignment_service.get_student_assignments(db, student_id)
    return assignments
