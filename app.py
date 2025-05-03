from ortools.sat.python import cp_model

def assign_students_to_rooms(students, rooms):
    """
    students: list of (student_id, exam_name)
    rooms:    list of (room_id, rows, cols, skip_rows: bool)
    returns:  dict student_id -> (room_id, row, col)
    """
    model = cp_model.CpModel()

    # extract IDs
    student_ids = [s for s, _ in students]
    exam_of    = {s: e for s, e in students}

    # build exam -> students map
    exam_to_students = {}
    for s, e in students:
        exam_to_students.setdefault(e, []).append(s)

    # 0) helper: for each room k, compute valid rows
    valid_rows = {}
    for ki, (_, R, _, skip_rows) in enumerate(rooms):
        valid_rows[ki] = [r for r in range(R) if not skip_rows or r % 2 == 0]

    # 1) vars x[s, k, r, c]: student s in room k at (r,c)
    x = {}
    for si, s in enumerate(student_ids):
        for ki, (rid, R, C, skip_rows) in enumerate(rooms):
            for r in valid_rows[ki]:
                for c in range(C):
                    x[s, ki, r, c] = model.NewBoolVar(f"x_{s}_{ki}_{r}_{c}")

    # 2) room-used indicator
    y = {ki: model.NewBoolVar(f"y_{ki}") for ki in range(len(rooms))}

    # 3) each student sits exactly once
    for s in student_ids:
        model.Add(
            sum(x[s, ki, r, c]
                for ki, (_, R, C, _) in enumerate(rooms)
                for r in valid_rows[ki]
                for c in range(C)
            ) == 1
        )

    # 4) no double‑booking + link to y
    for ki, (_, R, C, _) in enumerate(rooms):
        for r in valid_rows[ki]:
            for c in range(C):
                model.Add(sum(x[s, ki, r, c] for s in student_ids) <= 1)
                for s in student_ids:
                    model.Add(x[s, ki, r, c] <= y[ki])

    # 5) forbid horizontal neighbors for same‑exam
    for exam, studs in exam_to_students.items():
        if len(studs) < 2:
            continue
        for ki, (_, R, C, _) in enumerate(rooms):
            for r in valid_rows[ki]:
                for c in range(C - 1):
                    for i in range(len(studs)):
                        for j in range(i + 1, len(studs)):
                            s1, s2 = studs[i], studs[j]
                            model.Add(x[s1,ki,r,c] + x[s2,ki,r,c+1] <= 1)
                            model.Add(x[s2,ki,r,c] + x[s1,ki,r,c+1] <= 1)

    # 6) objective: minimize rooms used
    model.Minimize(sum(y.values()))

    # 7) solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    # 8) extract result
    result = {}
    for s in student_ids:
        for ki, (rid, R, C, _) in enumerate(rooms):
            for r in valid_rows[ki]:
                for c in range(C):
                    if solver.Value(x[s, ki, r, c]):
                        result[s] = (rid, r, c)
    return result

def visualize_assignment(assignment, rooms, students):
    """
    Prints a simple terminal map of each room's seating:
    student IDs or '...' for empty seats.
    """
    # build student → exam map
    exam_of = {s: e for s, e in students}
    for rid, R, C, skip_rows in rooms:
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

if __name__ == "__main__":
    import random

    # for reproducibility
    random.seed(42)

    # generate a much larger test set
    NUM_STUDENTS = 200
    NUM_EXAMS    = 10
    EXAMS        = [f"Exam{i}" for i in range(1, NUM_EXAMS + 1)]
    studs = [
        (f"S{idx:03d}", random.choice(EXAMS))
        for idx in range(1, NUM_STUDENTS + 1)
    ]

    # define several rooms with varying sizes and skip_rows flags
    rms = [
        ("RoomA", 8, 8, True),
        ("RoomB", 10, 10, True),
        ("RoomC", 10,  8, False),
        ("RoomD",  8, 15, True),
        ("RoomE", 12,  5, False),
    ]

    # (optional) bump up solver time for larger problem
    # solver.parameters.max_time_in_seconds = 60

    assignment = assign_students_to_rooms(studs, rms)
    if assignment is None:
        print("No valid arrangement found within time limit.")
    else:
        visualize_assignment(assignment, rms, studs)