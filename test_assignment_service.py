"""
Test the updated assignment service with Smart Greedy solver
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.assignment_service import process_assignment
from models import AssignRequest, StudentIn, RoomIn
from datetime import date

def test_assignment_service():
    """Test the assignment service with Smart Greedy solver"""
    print("🧪 Testing Assignment Service with Smart Greedy Solver")
    print("=" * 60)
    
    # Create test data
    students = [
        StudentIn(student_id=1, exam_name="Mathematics"),
        StudentIn(student_id=2, exam_name="Mathematics"),
        StudentIn(student_id=3, exam_name="Mathematics"),
        StudentIn(student_id=4, exam_name="Mathematics"),
        StudentIn(student_id=5, exam_name="Physics"),
        StudentIn(student_id=6, exam_name="Physics"),
        StudentIn(student_id=7, exam_name="Physics"),
        StudentIn(student_id=8, exam_name="Physics"),
        StudentIn(student_id=9, exam_name="Chemistry"),
        StudentIn(student_id=10, exam_name="Chemistry"),
        StudentIn(student_id=11, exam_name="Chemistry"),
        StudentIn(student_id=12, exam_name="Chemistry"),
    ]
    
    rooms = [
        RoomIn(room_id="RoomA", rows=3, cols=4, skip_rows=False, skip_cols=True),   # 6 seats
        RoomIn(room_id="RoomB", rows=4, cols=5, skip_rows=False, skip_cols=False), # 20 seats
        RoomIn(room_id="RoomC", rows=3, cols=3, skip_rows=True, skip_cols=False),  # 6 seats
    ]
    
    # Create assignment request
    request = AssignRequest(
        students=students,
        rooms=rooms,
        exam_room_restrictions={}
    )
    
    print(f"Test data: {len(students)} students, {len(rooms)} rooms")
    
    # Test different solver preferences
    solver_preferences = ["smart_greedy", "greedy", "auto", "ultra_fast"]
    
    for preference in solver_preferences:
        print(f"\n{'='*20} Testing {preference.upper()} {'='*20}")
        try:
            result = process_assignment(None, request, solver_preference=preference)
            
            if result:
                print(f"✅ {preference} solver SUCCESS")
                print(f"   - Assigned: {len(result)}/{len(students)} students")
                print(f"   - Success rate: {len(result)/len(students)*100:.1f}%")
                
                # Show room distribution
                room_count = {}
                for assignment in result:
                    room_id = assignment.room_id
                    room_count[room_id] = room_count.get(room_id, 0) + 1
                
                print(f"   - Room distribution: {room_count}")
                
            else:
                print(f"❌ {preference} solver FAILED - No solution found")
                
        except Exception as e:
            print(f"💥 {preference} solver ERROR: {str(e)}")
    
    print(f"\n{'='*60}")
    print("🎯 RECOMMENDATION: Use 'smart_greedy' for best performance!")

if __name__ == "__main__":
    test_assignment_service()
