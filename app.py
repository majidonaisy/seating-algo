from ortools.sat.python import cp_model

def assign_students_to_rooms(students, rooms, exam_room_restrictions=None):
    """
    students: list of (student_id, exam_name)
    rooms:    list of (room_id, rows, cols, skip_rows: bool, skip_cols: bool)
    exam_room_restrictions: dict of exam_name -> list of allowed room_ids
    returns:  dict student_id -> (room_id, row, col)
    """
    model = cp_model.CpModel()
    
    # Default to empty restrictions if None provided
    if exam_room_restrictions is None:
        exam_room_restrictions = {}

    # extract IDs
    student_ids = [s for s, _ in students]
    exam_of = {s: e for s, e in students}

    # build exam -> students map
    exam_to_students = {}
    for s, e in students:
        exam_to_students.setdefault(e, []).append(s)

    # 0) helper: for each room k, compute valid rows and columns
    valid_rows = {}
    valid_cols = {}
    for ki, (_, R, C, skip_rows, skip_cols) in enumerate(rooms):
        valid_rows[ki] = [r for r in range(R) if not skip_rows or r % 2 == 0]
        valid_cols[ki] = [c for c in range(C) if not skip_cols or c % 2 == 0]

    # Create room_id to index mapping for restrictions
    room_id_to_index = {room[0]: ki for ki, room in enumerate(rooms)}

    # 1) vars x[s, k, r, c]: student s in room k at (r,c)
    x = {}
    for si, s in enumerate(student_ids):
        exam = exam_of[s]
        for ki, (rid, R, C, skip_rows, skip_cols) in enumerate(rooms):
            # Check if this room is allowed for this exam
            if exam in exam_room_restrictions and rid not in exam_room_restrictions[exam]:
                # Skip creating variables for restricted combinations
                continue
                
            for r in valid_rows[ki]:
                for c in valid_cols[ki]:
                    x[s, ki, r, c] = model.NewBoolVar(f"x_{s}_{ki}_{r}_{c}")

    # 2) room-used indicator
    y = {ki: model.NewBoolVar(f"y_{ki}") for ki in range(len(rooms))}

    # 3) each student sits exactly once
    for s in student_ids:
        model.Add(
            sum(x.get((s, ki, r, c), 0)  # Use get() to handle missing keys
                for ki, (rid, R, C, _, _) in enumerate(rooms)
                for r in valid_rows[ki]
                for c in valid_cols[ki]
                if (s, ki, r, c) in x  # Check if the variable exists
            ) == 1
        )

    # 4) no double‑booking + link to y
    for ki, (_, R, C, _, _) in enumerate(rooms):
        for r in valid_rows[ki]:
            for c in valid_cols[ki]:
                model.Add(sum(x.get((s, ki, r, c), 0) for s in student_ids if (s, ki, r, c) in x) <= 1)
                for s in student_ids:
                    if (s, ki, r, c) in x:
                        model.Add(x[s, ki, r, c] <= y[ki])

    # 5) forbid horizontal and vertical neighbors for same‑exam
    for exam, studs in exam_to_students.items():
        if len(studs) < 2:
            continue
        for ki, (_, R, C, _, _) in enumerate(rooms):
            for r in valid_rows[ki]:
                # Horizontal separation
                for c in valid_cols[ki]:
                    for c2 in valid_cols[ki]:
                        if c2 <= c:
                            continue
                        for i in range(len(studs)):
                            for j in range(i + 1, len(studs)):
                                s1, s2 = studs[i], studs[j]
                                if (s1, ki, r, c) in x and (s2, ki, r, c2) in x:
                                    model.Add(x[s1,ki,r,c] + x[s2,ki,r,c2] <= 1)
                                if (s2, ki, r, c) in x and (s1, ki, r, c2) in x:
                                    model.Add(x[s2,ki,r,c] + x[s1,ki,r,c2] <= 1)
                # Vertical separation
                for c in valid_cols[ki]:
                    for r2 in range(r+1, R):
                        if r2 not in valid_rows[ki]:
                            continue
                        for i in range(len(studs)):
                            for j in range(i + 1, len(studs)):
                                s1, s2 = studs[i], studs[j]
                                if (s1, ki, r, c) in x and (s2, ki, r2, c) in x:
                                    model.Add(x[s1,ki,r,c] + x[s2,ki,r2,c] <= 1)
                                if (s2, ki, r, c) in x and (s1, ki, r2, c) in x:
                                    model.Add(x[s2,ki,r,c] + x[s1,ki,r2,c] <= 1)

    # 6) objective: minimize rooms used
    model.Minimize(sum(y.values()))

    # 7) solve
    solver = cp_model.CpSolver()
    # solver.parameters.max_time_in_seconds = 60
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    # 8) extract result
    result = {}
    for s in student_ids:
        for ki, (rid, R, C, _, _) in enumerate(rooms):
            for r in valid_rows[ki]:
                for c in valid_cols[ki]:
                    if (s, ki, r, c) in x and solver.Value(x[s, ki, r, c]):
                        result[s] = (rid, r, c)
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