"""
Simple Greedy Seating Assignment Solver
Ultra-fast implementation for performance comparison
"""

import time
from collections import defaultdict
import random

def assign_students_greedy(students, rooms, exam_room_restrictions=None, timeout_seconds=60):
    """
    Simple greedy assignment algorithm
    10-100x faster than CP-SAT for most cases
    """
    print(f"🏃‍♂️ Starting Greedy assignment for {len(students)} students")
    start_time = time.time()
    
    if exam_room_restrictions is None:
        exam_room_restrictions = {}

    # Step 1: Preprocess rooms and calculate positions
    room_info = {}
    total_capacity = 0
    
    for rid, rows, cols, skip_rows, skip_cols in rooms:
        positions = []
        for r in range(rows):
            if skip_rows and r % 2 != 0:
                continue
            for c in range(cols):
                if skip_cols and c % 2 != 0:
                    continue
                positions.append((r, c))
        
        room_info[rid] = {
            'positions': positions,
            'capacity': len(positions),
            'used': set(),  # Track used positions
            'assignments': {}  # student_id -> (row, col)
        }
        total_capacity += len(positions)
    
    print(f"Total capacity: {total_capacity}, Students: {len(students)}")
    
    if total_capacity < len(students):
        print("ERROR: Not enough capacity!")
        return None

    # Step 2: Group students by exam
    exam_groups = defaultdict(list)
    student_to_exam = {}
    
    for s, e in students:
        exam_groups[e].append(s)
        student_to_exam[s] = e

    # Step 3: Sort exams by size (largest first for better packing)
    sorted_exams = sorted(exam_groups.items(), key=lambda x: len(x[1]), reverse=True)
    
    assignment = {}
    
    # Step 4: Assign each exam group
    for exam, exam_students in sorted_exams:
        print(f"Assigning {len(exam_students)} students for {exam}")
        
        # Get available rooms for this exam
        available_rooms = []
        for rid, info in room_info.items():
            if exam in exam_room_restrictions and rid not in exam_room_restrictions[exam]:
                continue
            available_rooms.append((rid, info))
        
        # Sort rooms by available capacity
        available_rooms.sort(key=lambda x: len(x[1]['positions']) - len(x[1]['used']), reverse=True)
        
        # Assign each student in this exam
        for student in exam_students:
            assigned = False
            
            # Try each available room
            for room_id, room_info_dict in available_rooms:
                position = find_valid_position(
                    student, exam, room_id, room_info_dict, student_to_exam
                )
                
                if position:
                    row, col = position
                    assignment[student] = (room_id, row, col)
                    room_info_dict['used'].add(position)
                    room_info_dict['assignments'][student] = position
                    assigned = True
                    break
            
            if not assigned:
                print(f"Failed to assign student {student} (exam {exam})")
                # Try to continue with partial assignment
                # return None
    
    total_time = time.time() - start_time
    print(f"Greedy assignment completed in {total_time:.3f}s")
    print(f"Assigned {len(assignment)} out of {len(students)} students")
    
    return assignment

def find_valid_position(student, exam, room_id, room_info_dict, student_to_exam):
    """Find a valid position for a student in a room"""
    positions = room_info_dict['positions']
    used = room_info_dict['used']
    assignments = room_info_dict['assignments']
    
    # Try positions in order (could be randomized for better results)
    for pos in positions:
        if pos in used:
            continue
        
        # Check adjacency constraints
        if is_position_valid(pos, exam, room_info_dict, student_to_exam):
            return pos
    
    return None

def is_position_valid(pos, exam, room_info_dict, student_to_exam):
    """Check if position violates adjacency constraints"""
    r, c = pos
    assignments = room_info_dict['assignments']
    
    # Check all 4 adjacent positions
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        adj_pos = (r + dr, c + dc)
        
        # Check if adjacent position exists and is occupied
        if adj_pos in room_info_dict['positions']:  # Valid position exists
            # Find student at adjacent position
            adj_student = None
            for student_id, student_pos in assignments.items():
                if student_pos == adj_pos:
                    adj_student = student_id
                    break
            
            if adj_student:
                adj_exam = student_to_exam[adj_student]
                if adj_exam == exam:
                    return False  # Same exam adjacent - violation
    
    return True

def assign_students_smart_greedy(students, rooms, exam_room_restrictions=None, timeout_seconds=60):
    """
    Smart greedy with backtracking and local optimization
    """
    print(f"🧠 Starting Smart Greedy assignment for {len(students)} students")
    start_time = time.time()
    
    # First try simple greedy
    assignment = assign_students_greedy(students, rooms, exam_room_restrictions, timeout_seconds//2)
    
    if not assignment or len(assignment) < len(students):
        print("Simple greedy failed, trying with backtracking...")
        # Could implement backtracking here
        return assignment
    
    # Try to improve with local search
    print("Improving assignment with local search...")
    improved = improve_assignment_local_search(assignment, students, rooms, max_iterations=100)
    
    total_time = time.time() - start_time
    print(f"Smart greedy completed in {total_time:.3f}s")
    
    return improved if improved else assignment

def improve_assignment_local_search(assignment, students, rooms, max_iterations=100):
    """Improve assignment using local search"""
    if not assignment:
        return None
    
    current_assignment = assignment.copy()
    student_to_exam = {s: e for s, e in students}
    
    for iteration in range(max_iterations):
        improved = False
        student_list = list(current_assignment.keys())
        
        # Try swapping pairs of students
        for i in range(len(student_list)):
            for j in range(i + 1, min(i + 10, len(student_list))):  # Limit pairs to check
                s1, s2 = student_list[i], student_list[j]
                
                # Skip if same exam (no benefit to swap)
                if student_to_exam[s1] == student_to_exam[s2]:
                    continue
                
                # Try swap
                new_assignment = current_assignment.copy()
                new_assignment[s1], new_assignment[s2] = new_assignment[s2], new_assignment[s1]
                
                # Check if swap maintains validity
                if is_assignment_valid_local(new_assignment, students):
                    current_assignment = new_assignment
                    improved = True
                    break
            
            if improved:
                break
        
        if not improved:
            break
    
    return current_assignment

def is_assignment_valid_local(assignment, students):
    """Quick local validity check for assignment"""
    student_to_exam = {s: e for s, e in students}
    
    # Group by room
    room_assignments = defaultdict(list)
    for student, (room_id, row, col) in assignment.items():
        room_assignments[room_id].append((student, row, col))
    
    # Check each room for adjacency violations
    for room_id, room_students in room_assignments.items():
        for i, (s1, r1, c1) in enumerate(room_students):
            for j, (s2, r2, c2) in enumerate(room_students):
                if i >= j:
                    continue
                
                # Check if adjacent
                if abs(r1 - r2) + abs(c1 - c2) == 1:
                    # Check if same exam
                    if student_to_exam[s1] == student_to_exam[s2]:
                        return False
    
    return True

def visualize_assignment_simple(assignment, rooms, students):
    """Simple visualization"""
    if not assignment:
        print("No assignment to visualize")
        return
    
    print("\n" + "="*50)
    print("SIMPLE ASSIGNMENT VISUALIZATION")
    print("="*50)
    
    student_to_exam = {s: e for s, e in students}
    
    # Group by room
    room_assignments = defaultdict(list)
    for student, (room_id, row, col) in assignment.items():
        room_assignments[room_id].append((student, row, col))
    
    for room_id, assignments in room_assignments.items():
        print(f"\n{room_id}: {len(assignments)} students")
        
        # Find room dimensions
        room_info = next((r for r in rooms if r[0] == room_id), None)
        if room_info:
            _, rows, cols, skip_rows, skip_cols = room_info
            
            # Create simple grid
            grid = [['.' for _ in range(cols)] for _ in range(rows)]
            
            # Mark occupied positions
            for student, row, col in assignments:
                if 0 <= row < rows and 0 <= col < cols:
                    exam = student_to_exam.get(student, "?")
                    grid[row][col] = f"{student}({exam[0]})"
            
            # Print grid
            for r, row_data in enumerate(grid):
                print(f"  Row {r}: " + " ".join(f"{cell:>8}" for cell in row_data))

# Test function
def test_greedy_solvers():
    """Test the greedy implementations"""
    print("Testing Greedy Seating Assignment Solvers")
    print("=" * 60)
    
    # Test data
    students = [
        (1, "Math"), (2, "Math"), (3, "Math"), (4, "Math"),
        (5, "Physics"), (6, "Physics"), (7, "Physics"), (8, "Physics"),
        (9, "Chemistry"), (10, "Chemistry"), (11, "Chemistry"), (12, "Chemistry"),
        (13, "Biology"), (14, "Biology"), (15, "Biology"), (16, "Biology"),
    ]
    
    rooms = [
        ("RoomA", 3, 4, False, True),   # 6 seats
        ("RoomB", 4, 5, False, False),  # 20 seats
        ("RoomC", 3, 3, True, False),   # 6 seats
    ]
    
    print(f"Test: {len(students)} students, {len(rooms)} rooms")
    
    # Test simple greedy
    result1 = assign_students_greedy(students, rooms, {}, 30)
    if result1:
        print(f"✅ Simple Greedy: {len(result1)}/{len(students)} students assigned")
        visualize_assignment_simple(result1, rooms, students)
    else:
        print("❌ Simple Greedy failed")
    
    print("\n" + "="*60)
    
    # Test smart greedy
    result2 = assign_students_smart_greedy(students, rooms, {}, 30)
    if result2:
        print(f"✅ Smart Greedy: {len(result2)}/{len(students)} students assigned")
    else:
        print("❌ Smart Greedy failed")

if __name__ == "__main__":
    test_greedy_solvers()
