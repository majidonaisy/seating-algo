from sqlalchemy.orm import Session
from typing import List, Optional
import crud
from models import AssignmentIn, AssignmentOut, AssignRequest
from app import assign_students_to_rooms
from datetime import date


def process_assignment(db: Session, request: AssignRequest):
    # Get students from database by IDs
    students = [(student_id, request.exam_name) for student_id in request.students]
    
    # Get room details from database
    room_details = []
    for room_id in request.rooms:
        room = crud.get_room(db, room_id)
        if room:
            room_details.append((room.room_id, room.rows, room.cols, room.skip_rows))
    
    # If no rooms found, return None
    if not room_details:
        return None
    
    # Call the assignment algorithm
    result = assign_students_to_rooms(students, room_details)
    if result is None:
        return None

    # Save assignments to database
    assignments = []
    for student_id, (rid, r, c) in result.items():
        db_assignment = crud.create_assignment(
            db=db,
            student_id=student_id,
            room_id=rid,
            exam_name=request.exam_name,
            row=r,
            col=c
        )
        assignments.append(AssignmentOut(
            id=db_assignment.id,
            student_id=db_assignment.student_id,
            room_id=db_assignment.room_id,
            exam_name=db_assignment.exam_name,
            row=db_assignment.row,
            col=db_assignment.col,
            date=db_assignment.date
        ))
    return assignments

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
