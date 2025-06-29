import time

def test_cpp_solver():
    try:
        from fast_solver import FastSeatingOptimizer, Student, Room
        print("✅ C++ extension imported successfully!")
        
        # Test data
        students_data = [
            (1, "Math"), (2, "Math"), (3, "Math"), (4, "Math"),
            (5, "Physics"), (6, "Physics"), (7, "Physics"), (8, "Physics"),
            (9, "Chemistry"), (10, "Chemistry"), (11, "Chemistry"), (12, "Chemistry"),
        ]
        
        rooms_data = [
            ("RoomA", 3, 4, False, True),   # 6 seats
            ("RoomB", 3, 4, False, False),  # 12 seats
            ("RoomC", 2, 4, True, False),   # 4 seats
        ]
        
        # Convert to C++ objects
        cpp_students = [Student(s_id, exam) for s_id, exam in students_data]
        cpp_rooms = [Room(rid, rows, cols, skip_r, skip_c) 
                     for rid, rows, cols, skip_r, skip_c in rooms_data]
        
        restrictions = {}  # No restrictions for test
        
        print(f"Testing with {len(cpp_students)} students and {len(cpp_rooms)} rooms")
        
        # Run C++ solver
        optimizer = FastSeatingOptimizer()
        start_time = time.time()
        assignments = optimizer.solve(cpp_students, cpp_rooms, restrictions, 60)
        cpp_time = time.time() - start_time
        
        print(f"C++ solver completed in {cpp_time:.3f}s")
        print(f"Assigned {len(assignments)} students")
        
        # Display results
        if assignments:
            print("\nAssignments:")
            for assignment in assignments:
                print(f"Student {assignment.student_id} -> {assignment.room_id} ({assignment.row}, {assignment.col})")
            return True
        else:
            print("No solution found")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import C++ extension: {e}")
        return False
    except Exception as e:
        print(f"❌ C++ solver test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_cpp_solver()
    if success:
        print("🎉 C++ solver test passed!")
    else:
        print("💥 C++ solver test failed!")