from sqlalchemy.orm import Session
from typing import List, Optional
import crud
from models import AssignmentIn, AssignmentOut, AssignRequest
from app import assign_students_to_rooms
from datetime import date


def process_assignment(db: Session, request: AssignRequest):
    try:
        print("Processing assignment request...")
        
        # Extract student_id and exam_name from each student object
        students = [(student.student_id, student.exam_name) for student in request.students]
        print(f"Students: {students}")
        
        # Convert RoomRequest objects to tuples
        room_tuples = []
        for room in request.rooms:
            room_tuples.append((room.room_id, room.rows, room.cols, room.skip_rows, room.skip_cols))
        print(f"Room tuples: {room_tuples}")
        
        # Pass exam_room_restrictions to the assignment algorithm
        exam_room_restrictions = request.exam_room_restrictions or {}
        print(f"Restrictions: {exam_room_restrictions}")
        
        # Increase timeout for complex assignments
        result = assign_students_to_rooms(students, room_tuples, exam_room_restrictions, timeout_seconds=180)
        
        if result is None:
            print("Assignment algorithm returned None")
            return None

        # Create assignments list
        assignments = []
        for student_id, (rid, r, c) in result.items():
            # Find the exam_name for this student_id
            exam_name = next(student.exam_name for student in request.students 
                             if student.student_id == student_id)
            
            # Create assignment object
            assignment = AssignmentOut(
                id=0,  # Will be set by database
                student_id=student_id,
                room_id=rid,
                exam_name=exam_name,
                row=r,
                col=c,
                date=date.today()
            )
            assignments.append(assignment)
        
        print(f"Created {len(assignments)} assignments")
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
