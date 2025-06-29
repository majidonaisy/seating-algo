from sqlalchemy.orm import Session
from typing import List, Optional
from models import AssignmentIn, AssignmentOut, AssignRequest
from datetime import date
import time
import crud

# Import available solvers - prioritize new optimized algorithms
try:
    from simple_greedy_solver import assign_students_smart_greedy, assign_students_greedy
    GREEDY_AVAILABLE = True
    print("✅ Smart Greedy solver available")
except ImportError:
    GREEDY_AVAILABLE = False
    print("⚠️ Smart Greedy solver not available")

try:
    from ultra_fast_app import assign_students_to_rooms_ultra_fast
    ULTRA_FAST_AVAILABLE = True
    print("✅ Ultra-fast CP-SAT solver available")
except ImportError:
    ULTRA_FAST_AVAILABLE = False
    print("⚠️ Ultra-fast solver not available")

try:
    from numba_fast_app import assign_students_to_rooms_numba
    NUMBA_AVAILABLE = True
    print("✅ Numba solver available")
except ImportError:
    NUMBA_AVAILABLE = False
    print("⚠️ Numba solver not available")

# Fallback to original solver if needed
try:
    from app import assign_students_to_rooms
    ORIGINAL_AVAILABLE = True
    print("✅ Original CP-SAT solver available as fallback")
except ImportError:
    ORIGINAL_AVAILABLE = False
    print("⚠️ Original solver not available")

def process_assignment(db: Session, request: AssignRequest, solver_preference="smart_greedy"):
    """Process assignment with best available solver - Smart Greedy prioritized"""
    try:
        print("Processing assignment request...")
        start_time = time.time()
        
        students = [(student.student_id, student.exam_name) for student in request.students]
        room_tuples = [(room.room_id, room.rows, room.cols, room.skip_rows, room.skip_cols) 
                      for room in request.rooms]
        exam_room_restrictions = request.exam_room_restrictions or {}
        
        print(f"Assignment request: {len(students)} students, {len(room_tuples)} rooms")
        
        # Choose solver based on preference and availability
        result = None
        solver_used = ""
        
        if solver_preference == "smart_greedy" and GREEDY_AVAILABLE:
            print("🧠 Using Smart Greedy solver (recommended)...")
            result = assign_students_smart_greedy(
                students, room_tuples, exam_room_restrictions, timeout_seconds=30
            )
            solver_used = "Smart Greedy"
            
        elif solver_preference == "greedy" and GREEDY_AVAILABLE:
            print("🏃‍♂️ Using basic Greedy solver...")
            result = assign_students_greedy(
                students, room_tuples, exam_room_restrictions, timeout_seconds=30
            )
            solver_used = "Greedy"
            
        elif solver_preference == "ultra_fast" and ULTRA_FAST_AVAILABLE:
            print("🚀 Using Ultra-fast CP-SAT solver...")
            result = assign_students_to_rooms_ultra_fast(
                students, room_tuples, exam_room_restrictions, timeout_seconds=60
            )
            solver_used = "Ultra Fast CP-SAT"
            
        elif solver_preference == "numba" and NUMBA_AVAILABLE:
            print("⚡ Using Numba solver...")
            result = assign_students_to_rooms_numba(
                students, room_tuples, exam_room_restrictions, timeout_seconds=90
            )
            solver_used = "Numba"
            
        # Auto mode - try best available solvers in order of preference
        elif solver_preference == "auto":
            if GREEDY_AVAILABLE:
                print("🧠 Auto mode: Using Smart Greedy solver...")
                result = assign_students_smart_greedy(
                    students, room_tuples, exam_room_restrictions, timeout_seconds=30
                )
                solver_used = "Smart Greedy (Auto)"
            elif ULTRA_FAST_AVAILABLE:
                print("🚀 Auto mode: Using Ultra-fast solver...")
                result = assign_students_to_rooms_ultra_fast(
                    students, room_tuples, exam_room_restrictions, timeout_seconds=60
                )
                solver_used = "Ultra Fast CP-SAT (Auto)"
            elif NUMBA_AVAILABLE:
                print("⚡ Auto mode: Using Numba solver...")
                result = assign_students_to_rooms_numba(
                    students, room_tuples, exam_room_restrictions, timeout_seconds=90
                )
                solver_used = "Numba (Auto)"
            elif ORIGINAL_AVAILABLE:
                print("🐍 Auto mode: Using original solver...")
                result = assign_students_to_rooms(
                    students, room_tuples, exam_room_restrictions, timeout_seconds=180
                )
                solver_used = "Original CP-SAT (Auto)"
        
        # Fallback chain if preferred solver failed or unavailable
        if not result:
            print("Primary solver failed or unavailable, trying fallbacks...")
            
            # Try Smart Greedy first (fastest and most reliable)
            if GREEDY_AVAILABLE and solver_preference != "smart_greedy":
                print("🧠 Fallback: Trying Smart Greedy solver...")
                result = assign_students_smart_greedy(
                    students, room_tuples, exam_room_restrictions, timeout_seconds=30
                )
                if result:
                    solver_used = "Smart Greedy (Fallback)"
            
            # Try Ultra Fast CP-SAT
            if not result and ULTRA_FAST_AVAILABLE and solver_preference != "ultra_fast":
                print("🚀 Fallback: Trying Ultra-fast solver...")
                result = assign_students_to_rooms_ultra_fast(
                    students, room_tuples, exam_room_restrictions, timeout_seconds=60
                )
                if result:
                    solver_used = "Ultra Fast CP-SAT (Fallback)"
            
            # Try basic Greedy
            if not result and GREEDY_AVAILABLE and solver_preference != "greedy":
                print("🏃‍♂️ Fallback: Trying basic Greedy solver...")
                result = assign_students_greedy(
                    students, room_tuples, exam_room_restrictions, timeout_seconds=30
                )
                if result:
                    solver_used = "Greedy (Fallback)"
            
            # Try original solver as last resort
            if not result and ORIGINAL_AVAILABLE:
                print("🐍 Last resort: Using original solver...")
                result = assign_students_to_rooms(
                    students, room_tuples, exam_room_restrictions, timeout_seconds=120
                )
                if result:
                    solver_used = "Original CP-SAT (Last Resort)"
        
        if result is None:
            print(f"❌ All solvers failed to find a solution")
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
        print(f"✅ Assignment completed using {solver_used}")
        print(f"   - Total time: {total_time:.2f}s")
        print(f"   - Students assigned: {len(assignments)}/{len(students)}")
        print(f"   - Success rate: {len(assignments)/len(students)*100:.1f}%")
        
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
