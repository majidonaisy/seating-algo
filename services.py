from typing import List, Tuple, Dict, Optional
from app import assign_students_to_rooms
from models import StudentIn, RoomIn, AssignmentOut

def process_assignment(
    students: List[StudentIn], 
    rooms: List[RoomIn]
) -> Optional[List[AssignmentOut]]:
    # prepare inputs for solver
    studs = [(s.student_id, s.exam_name) for s in students]
    rms = [(r.room_id, r.rows, r.cols, r.skip_rows) for r in rooms]

    result = assign_students_to_rooms(studs, rms)
    if result is None:
        return None

    assignments = [
        AssignmentOut(
            student_id=s,
            room_id=rid,
            row=r,
            col=c
        )
        for s, (rid, r, c) in result.items()
    ]
    return assignments
