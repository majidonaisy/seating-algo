import datetime
from simple_greedy_solver import assign_students_greedy

# Test data: students with the new schema
students = [
    {
        "file_number": 1,
        "name": "Alice",
        "major": "Physics",
        "examination_date": datetime.date(2025, 7, 10),
        "course_code": "PHY101",
        "course_name": "Physics I",
        "language": "EN",
        "academic_year": "2024/2025",
        "time": "09:00"
    },
    {
        "file_number": 2,
        "name": "Bob",
        "major": "Mathematics",
        "examination_date": datetime.date(2025, 7, 10),
        "course_code": "MTH101",
        "course_name": "Calculus I",
        "language": "EN",
        "academic_year": "2024/2025",
        "time": "09:00"
    },
    {
        "file_number": 3,
        "name": "Charlie",
        "major": "Physics",
        "examination_date": datetime.date(2025, 7, 10),
        "course_code": "PHY101",
        "course_name": "Physics I",
        "language": "EN",
        "academic_year": "2024/2025",
        "time": "09:00"
    },
    {
        "file_number": 4,
        "name": "Diana",
        "major": "Mathematics",
        "examination_date": datetime.date(2025, 7, 10),
        "course_code": "MTH101",
        "course_name": "Calculus I",
        "language": "EN",
        "academic_year": "2024/2025",
        "time": "09:00"
    }
]

# Test data: rooms
rooms = [
    ("RoomA", 2, 2, False, 0),  # 2x2 room, no skipped rows/cols
    ("RoomB", 2, 2, False, 0)
]

# No exam_room_restrictions for this test
assignments = assign_students_greedy(students, rooms)

print("\nAssignments:")
for a in assignments:
    print(a)

# Simple assertions
assert len(assignments) == len(students), "All students should be assigned"
assigned_file_numbers = {a.file_number for a in assignments}
assert assigned_file_numbers == {1, 2, 3, 4}, "All file_numbers should be present"
print("\nTest passed!")
