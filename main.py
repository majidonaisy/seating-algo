from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from app import assign_students_to_rooms

app = FastAPI()

class StudentIn(BaseModel):
    student_id: str
    exam_name: str

class RoomIn(BaseModel):
    room_id: str
    rows: int
    cols: int
    skip_rows: bool

class AssignmentOut(BaseModel):
    student_id: str
    room_id: str
    row: int
    col: int

class AssignRequest(BaseModel):
    students: List[StudentIn]
    rooms: List[RoomIn]

class AssignResponse(BaseModel):
    assignments: List[AssignmentOut]

@app.post("/assign", response_model=AssignResponse)
def assign(req: AssignRequest):
    # prepare inputs for solver
    studs = [(s.student_id, s.exam_name) for s in req.students]
    rms  = [(r.room_id, r.rows, r.cols, r.skip_rows) for r in req.rooms]

    result = assign_students_to_rooms(studs, rms)
    if result is None:
        raise HTTPException(status_code=400, detail="No valid arrangement found within time limit")

    assignments = [
        AssignmentOut(
            student_id=s,
            room_id=rid,
            row=r,
            col=c
        )
        for s, (rid, r, c) in result.items()
    ]
    return AssignResponse(assignments=assignments)
