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
    try:
        print(f"Received assignment request with {len(req.students)} students and {len(req.rooms)} rooms")
        # Pass full student info to the service (new schema)
        assignments = assignment_service.process_assignment(db, req)
        
        if assignments is None:
            raise HTTPException(
                status_code=400, 
                detail="No valid seating arrangement found. Possible causes: insufficient room capacity, conflicting restrictions, or timeout exceeded."
            )
        
        if len(assignments) == 0:
            raise HTTPException(
                status_code=400,
                detail="No students were assigned seats. Check your input data."
            )
        
        print(f"Successfully created {len(assignments)} assignments")
        return AssignResponse(assignments=assignments)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in assign route: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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
