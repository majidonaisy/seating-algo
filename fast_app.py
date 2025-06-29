from fast_solver import FastSeatingOptimizer, Student, Room

def assign_students_to_rooms_fast(students, rooms, exam_room_restrictions=None, timeout_seconds=120):
    """Fast C++ implementation wrapper"""
    if exam_room_restrictions is None:
        exam_room_restrictions = {}
    
    # Convert to C++ objects
    cpp_students = [Student(s, e) for s, e in students]
    cpp_rooms = [Room(rid, R, C, skip_rows, skip_cols) for rid, R, C, skip_rows, skip_cols in rooms]
    
    # Use C++ solver
    optimizer = FastSeatingOptimizer()
    assignments = optimizer.solve(cpp_students, cpp_rooms, exam_room_restrictions, timeout_seconds)
    
    # Convert back to Python format
    result = {}
    for assignment in assignments:
        result[assignment.student_id] = (assignment.room_id, assignment.row, assignment.col)
    
    return result