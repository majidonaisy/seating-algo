from sqlalchemy.orm import Session
from typing import List, Optional
import crud
from models import AssignmentIn, AssignmentOut, AssignRequest
from numba_fast_app import assign_students_to_rooms_numba
from app import assign_students_to_rooms
import time
from datetime import date


def process_assignment(db: Session, request: AssignRequest, use_numba=True):
    """Process assignment with optional Numba optimization"""
    try:
        print("Processing assignment request...")
        start_time = time.time()
        
        students = [(student.student_id, student.exam_name) for student in request.students]
        room_tuples = [(room.room_id, room.rows, room.cols, room.skip_rows, room.skip_cols) 
                      for room in request.rooms]
        exam_room_restrictions = request.exam_room_restrictions or {}
        
        # Choose algorithm
        if use_numba:
            print("Using Numba-optimized solver...")
            result = assign_students_to_rooms_numba(
                students, room_tuples, exam_room_restrictions, timeout_seconds=60
            )
        else:
            print("Using original Python solver...")
            result = assign_students_to_rooms(
                students, room_tuples, exam_room_restrictions, timeout_seconds=180
            )
        
        if result is None:
            print("Assignment algorithm returned None")
            return None

        # Convert to assignments
        assignments = []
        for student_id, (rid, r, c) in result.items():
            exam_name = next(s.exam_name for s in request.students 
                            if s.student_id == student_id)
            assignments.append(AssignmentOut(
                id=0, student_id=student_id, room_id=rid,
                exam_name=exam_name, row=r, col=c, date=date.today()
            ))
        
        total_time = time.time() - start_time
        print(f"Total processing time: {total_time:.2f}s")
        return assignments
        
    except Exception as e:
        print(f"Error in process_assignment: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_assignments(db: Session, skip: int = 0, limit: int = 100):
    db_assignments = crud.get_assignments(db, skip, limit)
    return [AssignmentOut(
        id=a.id,
        student_id=a.student_id,
        room_id=a.room_id,
        exam_name=a.exam_name,
        row=a.row,
        col=a.col,
        date=a.date
    ) for a in db_assignments]

def get_student_assignments(db: Session, student_id: int):
    db_assignments = crud.get_student_assignments(db, student_id)
    return [AssignmentOut(
        id=a.id,
        student_id=a.student_id,
        room_id=a.room_id,
        exam_name=a.exam_name,
        row=a.row,
        col=a.col,
        date=a.date
    ) for a in db_assignments]

def create_assignment(db: Session, assignment: AssignmentIn):
    return crud.create_assignment(
        db=db,
        student_id=assignment.student_id,
        room_id=assignment.room_id,
        exam_name=assignment.exam_name,
        row=assignment.row,
        col=assignment.col,
        assignment_date=assignment.date
    )
