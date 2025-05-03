from fastapi import APIRouter, HTTPException
from models import AssignRequest, AssignResponse
from services import process_assignment

router = APIRouter()

@router.post("/assign", response_model=AssignResponse)
def assign(req: AssignRequest):
    assignments = process_assignment(req.students, req.rooms)
    if assignments is None:
        raise HTTPException(status_code=400, detail="No valid arrangement found within time limit")
    
    return AssignResponse(assignments=assignments)
