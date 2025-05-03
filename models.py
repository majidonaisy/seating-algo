from pydantic import BaseModel
from typing import List

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
