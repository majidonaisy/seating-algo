from ortools.sat.python import cp_model

def assign_students_to_rooms(students, rooms, exam_room_restrictions=None, timeout_seconds=300):
    """Enhanced version with performance optimizations and debugging"""
    print(f"Starting assignment with {len(students)} students and {len(rooms)} rooms")
    print(f"Students: {students}")
    print(f"Rooms: {rooms}")
    print(f"Restrictions: {exam_room_restrictions}")
    
    model = cp_model.CpModel()
    
    if exam_room_restrictions is None:
        exam_room_restrictions = {}

    # Precompute valid positions for each room
    room_positions = {}
    total_capacity = 0
    for ki, (rid, R, C, skip_rows, skip_cols) in enumerate(rooms):
        positions = []
        for r in range(R):
            if skip_rows and r % 2 != 0:
                continue
            for c in range(C):
                if skip_cols and c % 2 != 0:
                    continue
                positions.append((r, c))
        room_positions[ki] = positions
        total_capacity += len(positions)
        print(f"Room {rid}: {len(positions)} available positions")
    
    print(f"Total capacity: {total_capacity}, Students: {len(students)}")
    
    if total_capacity < len(students):
        print("ERROR: Not enough room capacity for all students!")
        return None
    
    # Build exam groupings
    exam_to_students = {}
    exam_of = {}
    student_ids = []
    
    for s, e in students:
        exam_to_students.setdefault(e, []).append(s)
        exam_of[s] = e
        student_ids.append(s)
    
    print(f"Exam groups: {exam_to_students}")
    
    # OPTIMIZATION 1: Pre-filter valid room-student combinations
    valid_assignments = {}
    for s in student_ids:
        exam = exam_of[s]
        valid_assignments[s] = []
        for ki, (rid, R, C, skip_rows, skip_cols) in enumerate(rooms):
            # Skip rooms not allowed for this exam
            if exam in exam_room_restrictions and rid not in exam_room_restrictions[exam]:
                print(f"Student {s} (exam {exam}) cannot use room {rid} due to restrictions")
                continue
            valid_assignments[s].append(ki)
    
    # Check if all students have at least one valid room
    for s in student_ids:
        if not valid_assignments[s]:
            print(f"ERROR: Student {s} has no valid rooms!")
            return None
    
    print("All students have valid room assignments")

    # 1) Create variables only for valid combinations
    x = {}
    variable_count = 0
    for s in student_ids:
        for ki in valid_assignments[s]:
            for r, c in room_positions[ki]:
                x[s, ki, r, c] = model.NewBoolVar(f"x_{s}_{ki}_{r}_{c}")
                variable_count += 1
    
    print(f"Created {variable_count} variables")

    # 2) room-used indicator
    y = {ki: model.NewBoolVar(f"y_{ki}") for ki in range(len(rooms))}

    # 3) each student sits exactly once
    constraint_count = 0
    for s in student_ids:
        valid_vars = []
        for ki in valid_assignments[s]:
            for r, c in room_positions[ki]:
                if (s, ki, r, c) in x:
                    valid_vars.append(x[s, ki, r, c])
        
        if not valid_vars:
            print(f"ERROR: No valid variables for student {s}")
            return None
            
        model.Add(sum(valid_vars) == 1)
        constraint_count += 1

    # 4) no double‑booking + link to y
    for ki in range(len(rooms)):
        for r, c in room_positions[ki]:
            seat_vars = [x[s, ki, r, c] for s in student_ids if (s, ki, r, c) in x]
            if seat_vars:
                model.Add(sum(seat_vars) <= 1)
                constraint_count += 1
                
                # Link to room usage
                for s in student_ids:
                    if (s, ki, r, c) in x:
                        model.Add(x[s, ki, r, c] <= y[ki])
                        constraint_count += 1

    print(f"Added {constraint_count} basic constraints")

    # 5) SIMPLIFIED separation constraints - only for adjacent positions
    separation_constraints = 0
    for exam, studs in exam_to_students.items():
        if len(studs) < 2:
            continue
            
        for ki in range(len(rooms)):
            positions = room_positions[ki]
            
            # Create adjacency map
            adjacent_map = {}
            for r, c in positions:
                adjacent_map[(r, c)] = []
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    adj_pos = (r + dr, c + dc)
                    if adj_pos in positions:
                        adjacent_map[(r, c)].append(adj_pos)
            
            # Add separation constraints
            for (r1, c1), neighbors in adjacent_map.items():
                for (r2, c2) in neighbors:
                    for i, s1 in enumerate(studs):
                        for j, s2 in enumerate(studs):
                            if i >= j:  # Avoid duplicate constraints
                                continue
                            if (s1, ki, r1, c1) in x and (s2, ki, r2, c2) in x:
                                model.Add(x[s1, ki, r1, c1] + x[s2, ki, r2, c2] <= 1)
                                separation_constraints += 1

    print(f"Added {separation_constraints} separation constraints")

    # 6) objective: minimize rooms used
    model.Minimize(sum(y.values()))

    # 7) OPTIMIZED SOLVER SETTINGS
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout_seconds
    solver.parameters.num_search_workers = 4
    solver.parameters.search_branching = cp_model.PORTFOLIO_SEARCH
    solver.parameters.cp_model_presolve = True
    solver.parameters.symmetry_level = 1  # Reduced for speed
    solver.parameters.linearization_level = 1  # Reduced for speed
    solver.parameters.enumerate_all_solutions = False

    print("Starting solver...")
    status = solver.Solve(model)
    
    print(f"Solver status: {status}")
    print(f"Solver statistics:")
    print(f"  - Runtime: {solver.WallTime():.2f}s")
    print(f"  - Conflicts: {solver.NumConflicts()}")
    print(f"  - Branches: {solver.NumBranches()}")
    
    if status == cp_model.OPTIMAL:
        print("Found optimal solution!")
    elif status == cp_model.FEASIBLE:
        print("Found feasible solution!")
    else:
        print(f"No solution found. Status: {status}")
        return None

    # 8) extract result
    result = {}
    rooms_used = 0
    for ki in range(len(rooms)):
        if solver.Value(y[ki]):
            rooms_used += 1
            
    print(f"Solution uses {rooms_used} rooms")
    
    for s in student_ids:
        for ki in valid_assignments[s]:
            for r, c in room_positions[ki]:
                if (s, ki, r, c) in x and solver.Value(x[s, ki, r, c]):
                    rid = rooms[ki][0]
                    result[s] = (rid, r, c)
                    break
    
    print(f"Assigned {len(result)} students")
    return result

def visualize_assignment(assignment, rooms, students):
    """
    Prints a simple terminal map of each room's seating:
    student IDs or '...' for empty seats.
    """
    # build student → exam map
    exam_of = {s: e for s, e in students}
    for rid, R, C, skip_rows, skip_cols in rooms:
        print(f"\nRoom {rid} ({R} rows x {C} cols):")
        # build empty grid
        grid = [['...' for _ in range(C)] for __ in range(R)]
        # fill with assigned student IDs + exam
        for student, (room_id, r, c) in assignment.items():
            if room_id == rid:
                grid[r][c] = f"{student}({exam_of[student]})"
        # print each row
        for r in range(R):
            print(' '.join(cell.ljust(8) for cell in grid[r]))
    print()

# Example usage with room restrictions
if __name__ == "__main__":
    import random

    # for reproducibility
    random.seed(42)

    # generate test set
    NUM_STUDENTS = 150
    NUM_EXAMS = 5
    # EXAMS = [f"Exam{i}" for i in range(1, NUM_EXAMS + 1)]

    EXAMS = ["Exam1", "Exam2", "Exam3", "Exam4"]

    # studs = [
    #     (f"S{idx:03d}", random.choice(EXAMS))
    #     for idx in range(1, NUM_STUDENTS + 1)
    # ]

    studs = [
    (1, "Exam1"),
    (2, "Exam1"),
    (3, "Exam1"),
    (4, "Exam1"),
    (5, "Exam2"),
    (6, "Exam2"),
    (7, "Exam2"),
    (8, "Exam2"),
    (9, "Exam3"),
    (10, "Exam3"),
    (11, "Exam3"),
    (12, "Exam3"),
    (13, "Exam4"),
    (14, "Exam4"),
    (15, "Exam4"),
    (16, "Exam4")
]

    rms = [
        
        ( "RoomA",  2,  4,  False, True),
        ( "RoomB",  2,  3,  False, False),
        ( "RoomC",  5,  2,  False, True),
        ( "RoomD", 3, 2,  False, False)
    ]

    # define rooms
    # rms = [
    #     ("RoomA", 8, 8, True),
    #     ("RoomB", 10, 10, True),
    #     ("RoomC", 10, 8, False),
    #     ("RoomD", 8, 15, True),
    #     # ("RoomE", 12, 5, False),
    # ]

    # Define exam room restrictions
    # exam_room_restrictions = {
    #     "Exam1": ["RoomA", "RoomB"],
    #     "Exam3": ["RoomD", "RoomE"]
    # }

    exam_room_restrictions = {}
    #     "Exam1": ["RoomA", "RoomB"],
    #     "Exam2": ["RoomC", "RoomD"],
    #     "Exam3": ["RoomE"],
    # }
    # Note: Exams not in this dict (like Exam2, Exam4, etc.) can be assigned to any room

    assignment = assign_students_to_rooms(studs, rms, exam_room_restrictions)
    if assignment is None:
        print("No valid arrangement found within time limit.")
    else:
        visualize_assignment(assignment, rms, studs)