import numpy as np
from numba import jit, prange
from ortools.sat.python import cp_model
import time

@jit(nopython=True)
def compute_room_positions_numba(rooms_data):
    """Fast room position computation using Numba"""
    # rooms_data: array of [rows, cols, skip_rows, skip_cols]
    all_positions = []
    capacities = []
    
    for i in range(len(rooms_data)):
        rows, cols, skip_rows, skip_cols = rooms_data[i]
        positions = []
        
        for r in range(rows):
            if skip_rows == 1 and r % 2 != 0:
                continue
            for c in range(cols):
                if skip_cols == 1 and c % 2 != 0:
                    continue
                positions.append((r, c))
        
        all_positions.append(positions)
        capacities.append(len(positions))
    
    return all_positions, capacities

@jit(nopython=True)
def check_adjacent_positions(pos1, pos2):
    """Fast adjacency check"""
    r1, c1 = pos1
    r2, c2 = pos2
    return abs(r1 - r2) + abs(c1 - c2) == 1

def assign_students_to_rooms_numba(students, rooms, exam_room_restrictions=None, timeout_seconds=120):
    """Numba-optimized assignment function"""
    print(f"Starting Numba-optimized assignment for {len(students)} students")
    start_time = time.time()
    
    if exam_room_restrictions is None:
        exam_room_restrictions = {}

    # Convert rooms to NumPy array for Numba
    rooms_data = np.array([
        [R, C, int(skip_rows), int(skip_cols)] 
        for rid, R, C, skip_rows, skip_cols in rooms
    ])
    
    # Fast position computation
    room_positions, capacities = compute_room_positions_numba(rooms_data)
    total_capacity = sum(capacities)
    
    print(f"Numba preprocessing took {time.time() - start_time:.3f}s")
    print(f"Total capacity: {total_capacity}, Students: {len(students)}")
    
    if total_capacity < len(students):
        print("ERROR: Not enough room capacity!")
        return None

    # Build exam groupings (regular Python - fast enough)
    exam_to_students = {}
    exam_of = {}
    student_ids = []
    
    for s, e in students:
        exam_to_students.setdefault(e, []).append(s)
        exam_of[s] = e
        student_ids.append(s)

    # Continue with optimized CP-SAT
    model = cp_model.CpModel()
    
    # Create variables only for valid combinations
    x = {}
    for s in student_ids:
        exam = exam_of[s]
        for ki, (rid, R, C, skip_rows, skip_cols) in enumerate(rooms):
            # Check restrictions
            if exam in exam_room_restrictions and rid not in exam_room_restrictions[exam]:
                continue
            
            for r, c in room_positions[ki]:
                x[s, ki, r, c] = model.NewBoolVar(f"x_{s}_{ki}_{r}_{c}")

    # Room usage variables
    y = {ki: model.NewBoolVar(f"y_{ki}") for ki in range(len(rooms))}

    # Constraints
    # 1. Each student sits exactly once
    for s in student_ids:
        valid_vars = [x[s, ki, r, c] for ki in range(len(rooms)) 
                     for r, c in room_positions[ki] if (s, ki, r, c) in x]
        if valid_vars:
            model.Add(sum(valid_vars) == 1)

    # 2. No double booking + room usage linking
    for ki in range(len(rooms)):
        for r, c in room_positions[ki]:
            seat_vars = [x[s, ki, r, c] for s in student_ids if (s, ki, r, c) in x]
            if seat_vars:
                model.Add(sum(seat_vars) <= 1)
                for s in student_ids:
                    if (s, ki, r, c) in x:
                        model.Add(x[s, ki, r, c] <= y[ki])

    # 3. Separation constraints (optimized with Numba adjacency check)
    print("Adding separation constraints...")
    separation_count = 0
    
    for exam, studs in exam_to_students.items():
        if len(studs) < 2:
            continue
            
        for ki in range(len(rooms)):
            positions = room_positions[ki]
            
            # Use Numba for fast adjacency computation
            for i, pos1 in enumerate(positions):
                for j, pos2 in enumerate(positions):
                    if i >= j:
                        continue
                    
                    # Fast adjacency check using Numba
                    if check_adjacent_positions(pos1, pos2):
                        r1, c1 = pos1
                        r2, c2 = pos2
                        
                        # Add constraints for all student pairs in same exam
                        for si in range(len(studs)):
                            for sj in range(si + 1, len(studs)):
                                s1, s2 = studs[si], studs[sj]
                                if (s1, ki, r1, c1) in x and (s2, ki, r2, c2) in x:
                                    model.Add(x[s1, ki, r1, c1] + x[s2, ki, r2, c2] <= 1)
                                    separation_count += 1

    print(f"Added {separation_count} separation constraints")

    # Objective: minimize rooms used
    model.Minimize(sum(y.values()))

    # Solve with optimized parameters
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout_seconds
    solver.parameters.num_search_workers = 4
    solver.parameters.search_branching = cp_model.PORTFOLIO_SEARCH
    solver.parameters.cp_model_presolve = True

    print("Starting solver...")
    solve_start = time.time()
    status = solver.Solve(model)
    solve_time = time.time() - solve_start
    
    print(f"Solver completed in {solve_time:.2f}s")
    print(f"Status: {status}")

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    # Extract results
    result = {}
    for s in student_ids:
        for ki in range(len(rooms)):
            for r, c in room_positions[ki]:
                if (s, ki, r, c) in x and solver.Value(x[s, ki, r, c]):
                    rid = rooms[ki][0]
                    result[s] = (rid, r, c)
                    break

    total_time = time.time() - start_time
    print(f"Total assignment time: {total_time:.2f}s (Numba optimized)")
    return result

def visualize_assignment(assignment, rooms, students):
    """Simple visualization of the assignment"""
    if not assignment:
        print("No assignment to visualize")
        return
    
    print("\n" + "="*50)
    print("ASSIGNMENT VISUALIZATION")
    print("="*50)
    
    # Group by room
    room_assignments = {}
    for student_id, (room_id, row, col) in assignment.items():
        if room_id not in room_assignments:
            room_assignments[room_id] = []
        room_assignments[room_id].append((student_id, row, col))
    
    # Display each room
    for room_id, assignments in room_assignments.items():
        print(f"\nRoom {room_id}:")
        
        # Find room dimensions
        room_info = next((r for r in rooms if r[0] == room_id), None)
        if room_info:
            _, rows, cols, skip_rows, skip_cols = room_info
            
            # Create grid
            grid = [['.' for _ in range(cols)] for _ in range(rows)]
            
            # Mark skipped positions
            for r in range(rows):
                for c in range(cols):
                    if (skip_rows and r % 2 != 0) or (skip_cols and c % 2 != 0):
                        grid[r][c] = 'X'  # Skipped
            
            # Place students
            for student_id, row, col in assignments:
                if 0 <= row < rows and 0 <= col < cols:
                    # Find exam for this student
                    exam = next((e for s, e in students if s == student_id), "?")
                    grid[row][col] = f"{student_id}({exam[0]})"
            
            # Print grid
            for r, row_data in enumerate(grid):
                print(f"Row {r}: " + " ".join(f"{cell:>8}" for cell in row_data))
        
        print(f"Students in {room_id}: {len(assignments)}")

# Test function
def test_numba_performance():
    """Test the Numba implementation"""
    print("Testing Numba-optimized seating assignment...")
    
    # Test data
    students = [
        (1, "Mathematics"), (2, "Mathematics"), (3, "Mathematics"), (4, "Mathematics"),
        (5, "Physics"), (6, "Physics"), (7, "Physics"), (8, "Physics"),
        (9, "Chemistry"), (10, "Chemistry"), (11, "Chemistry"), (12, "Chemistry"),
    ]
    
    rooms = [
        ("RoomA", 3, 4, False, True),   # 6 seats (skip columns)
        ("RoomB", 3, 4, False, False),  # 12 seats (no skipping)
        ("RoomC", 2, 4, True, False),   # 4 seats (skip rows)
    ]
    
    # No restrictions for this test
    restrictions = {}
    
    print(f"Test scenario:")
    print(f"- Students: {len(students)}")
    print(f"- Rooms: {len(rooms)}")
    print(f"- Room details:")
    for rid, rows, cols, skip_r, skip_c in rooms:
        capacity = rows * cols
        if skip_r:
            capacity = capacity // 2
        if skip_c:
            capacity = capacity // 2
        print(f"  {rid}: {rows}x{cols} ({'skip_rows' if skip_r else 'all_rows'}, {'skip_cols' if skip_c else 'all_cols'}) = ~{capacity} seats")
    
    # Run the assignment
    print("\n" + "="*50)
    result = assign_students_to_rooms_numba(students, rooms, restrictions, timeout_seconds=60)
    
    if result:
        print(f"\n✅ SUCCESS: Assigned {len(result)} out of {len(students)} students")
        visualize_assignment(result, rooms, students)
        
        # Verify no adjacent same-exam students
        print("\n" + "="*30)
        print("VALIDATION CHECKS")
        print("="*30)
        
        violations = 0
        exam_of = {s: e for s, e in students}
        
        # Group assignments by room
        room_assignments = {}
        for student_id, (room_id, row, col) in result.items():
            if room_id not in room_assignments:
                room_assignments[room_id] = []
            room_assignments[room_id].append((student_id, row, col))
        
        # Check adjacency violations
        for room_id, assignments in room_assignments.items():
            for i, (s1, r1, c1) in enumerate(assignments):
                for j, (s2, r2, c2) in enumerate(assignments):
                    if i >= j:
                        continue
                    
                    # Check if adjacent
                    if abs(r1 - r2) + abs(c1 - c2) == 1:
                        # Check if same exam
                        if exam_of[s1] == exam_of[s2]:
                            print(f"❌ VIOLATION: Students {s1} and {s2} (both {exam_of[s1]}) are adjacent in {room_id} at ({r1},{c1}) and ({r2},{c2})")
                            violations += 1
        
        if violations == 0:
            print("✅ All separation constraints satisfied!")
        else:
            print(f"❌ Found {violations} separation violations")
            
    else:
        print("❌ FAILED: No solution found")
        return False
    
    return True

if __name__ == "__main__":
    success = test_numba_performance()
    if success:
        print("\n🎉 Numba optimization test completed successfully!")
    else:
        print("\n💥 Test failed - check your algorithm")