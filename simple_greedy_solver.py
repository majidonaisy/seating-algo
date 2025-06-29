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
    
    # Step 4: Assign each exam group with improved strategy
    room_exam_counts = {rid: defaultdict(int) for rid in room_info.keys()}  # Track exams per room
    room_student_counts = {rid: 0 for rid in room_info.keys()}  # Track students per room
    
    for exam, exam_students in sorted_exams:
        print(f"Assigning {len(exam_students)} students for {exam}")
        
        # Get available rooms for this exam
        available_rooms = []
        for rid, info in room_info.items():
            if exam in exam_room_restrictions and rid not in exam_room_restrictions[exam]:
                continue
            available_rooms.append((rid, info))
        
        # Sort rooms by priority:
        # 1. Prefer rooms with the most available capacity
        # 2. Prefer rooms already in use (to avoid opening new rooms unnecessarily)
        def room_priority(room_item):
            rid, info = room_item
            available_capacity = len(info['positions']) - len(info['used'])
            students_in_room = room_student_counts[rid]
            exams_in_room = len(room_exam_counts[rid])
            
            # Encourage rooms with other exams (diversity)
            diversity_bonus = 0
            if students_in_room > 0 and exams_in_room > 0:
                diversity_bonus = -50  # Prefer rooms with other exams
            
            # Strongly penalize opening a new room if only a few students remain
            few_students_left = len(exam_students) <= 5
            empty_room_penalty = 0
            if students_in_room == 0 and few_students_left:
                empty_room_penalty = 1000  # Large penalty
            
            # Priority: fill up rooms, encourage diversity, avoid opening new rooms for few students
            priority = -available_capacity * 100 + diversity_bonus + empty_room_penalty
            return priority
        
        available_rooms.sort(key=room_priority)
        
        # Assign each student in this exam
        for student in exam_students:
            assigned = False
            
            # Try each available room in priority order
            for room_id, room_info_dict in available_rooms:
                position = find_valid_position(
                    student, exam, room_id, room_info_dict, student_to_exam
                )
                
                if position:
                    row, col = position
                    assignment[student] = (room_id, row, col)
                    room_info_dict['used'].add(position)
                    room_info_dict['assignments'][student] = position
                    
                    # Update tracking
                    room_exam_counts[room_id][exam] += 1
                    room_student_counts[room_id] += 1
                    
                    assigned = True
                    break
            
            if not assigned:
                print(f"Failed to assign student {student} (exam {exam})")
                # Try to continue with partial assignment
    
    # Print room utilization summary
    print("\n📊 Room Utilization Summary:")
    for rid, info in room_info.items():
        students_count = room_student_counts[rid]
        if students_count > 0:
            capacity = len(info['positions'])
            utilization = students_count / capacity * 100
            exams_in_room = list(room_exam_counts[rid].keys())
            exam_distribution = dict(room_exam_counts[rid])
            print(f"  {rid}: {students_count}/{capacity} students ({utilization:.1f}% full)")
            print(f"    Exams: {exam_distribution}")
        else:
            print(f"  {rid}: Empty (not used)")
    
    total_time = time.time() - start_time
    print(f"\nGreedy assignment completed in {total_time:.3f}s")
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
    Smart greedy with improved room utilization and exam diversity
    """
    print(f"🧠 Starting Smart Greedy assignment for {len(students)} students")
    start_time = time.time()
    
    # First try improved greedy
    assignment = assign_students_greedy(students, rooms, exam_room_restrictions, timeout_seconds//2)
    
    if not assignment or len(assignment) < len(students):
        print("Improved greedy failed, returning partial result...")
        return assignment
    
    # Analyze current assignment
    print("\n🔍 Analyzing assignment quality...")
    room_analysis = analyze_room_diversity(assignment, students)
    
    # Try to improve diversity and utilization
    print("📈 Improving assignment with diversity optimization...")
    improved = improve_assignment_diversity(assignment, students, rooms, room_analysis, max_iterations=50)
    
    # Try standard local search for further improvements
    if improved:
        print("🔄 Applying local search optimization...")
        final_improved = improve_assignment_local_search(improved, students, rooms, max_iterations=50)
        if final_improved:
            improved = final_improved
    
    total_time = time.time() - start_time
    print(f"Smart greedy completed in {total_time:.3f}s")
    
    # Final analysis
    print("\n📊 Final Assignment Analysis:")
    final_analysis = analyze_room_diversity(improved if improved else assignment, students)
    
    return improved if improved else assignment

def analyze_room_diversity(assignment, students):
    """Analyze exam diversity and room utilization"""
    if not assignment:
        return {}
    
    student_to_exam = {s: e for s, e in students}
    room_stats = defaultdict(lambda: {'exams': defaultdict(int), 'total': 0})
    
    # Collect room statistics
    for student, (room_id, row, col) in assignment.items():
        exam = student_to_exam[student]
        room_stats[room_id]['exams'][exam] += 1
        room_stats[room_id]['total'] += 1
    
    # Analyze each room
    analysis = {}
    single_exam_rooms = []
    
    for room_id, stats in room_stats.items():
        num_exams = len(stats['exams'])
        total_students = stats['total']
        exam_distribution = dict(stats['exams'])
        
        analysis[room_id] = {
            'num_exams': num_exams,
            'total_students': total_students,
            'exam_distribution': exam_distribution,
            'is_single_exam': num_exams == 1,
            'diversity_score': num_exams / max(total_students, 1)  # Higher is better
        }
        
        if num_exams == 1 and total_students > 1:
            single_exam_rooms.append(room_id)
            print(f"⚠️  Room {room_id}: Single exam ({list(exam_distribution.keys())[0]}) with {total_students} students")
        else:
            print(f"✅ Room {room_id}: {num_exams} exams, {total_students} students - {exam_distribution}")
    
    analysis['single_exam_rooms'] = single_exam_rooms
    analysis['total_rooms_used'] = len(room_stats)
    
    return analysis

def improve_assignment_diversity(assignment, students, rooms, room_analysis, max_iterations=50):
    """Improve assignment by promoting exam diversity within rooms"""
    if not assignment:
        return None
    
    current_assignment = assignment.copy()
    student_to_exam = {s: e for s, e in students}
    single_exam_rooms = room_analysis.get('single_exam_rooms', [])
    
    if not single_exam_rooms:
        print("✅ No single-exam rooms found, diversity is good!")
        return current_assignment
    
    print(f"🎯 Attempting to diversify {len(single_exam_rooms)} single-exam rooms...")
    
    improvements_made = 0
    
    for iteration in range(max_iterations):
        improved_this_iteration = False
        
        # For each single-exam room, try to find students from other rooms to swap
        for single_room in single_exam_rooms:
            single_room_students = [
                (s, pos) for s, pos in current_assignment.items() 
                if pos[0] == single_room
            ]
            
            if not single_room_students:
                continue
            
            single_exam = student_to_exam[single_room_students[0][0]]
            
            # Find students from other exams in different rooms
            for student, (room_id, row, col) in current_assignment.items():
                if room_id == single_room:
                    continue
                
                student_exam = student_to_exam[student]
                if student_exam == single_exam:
                    continue
                
                # Try to swap this student with someone from the single-exam room
                for single_student, (_, single_row, single_col) in single_room_students:
                    # Create potential swap
                    new_assignment = current_assignment.copy()
                    new_assignment[student] = (single_room, single_row, single_col)
                    new_assignment[single_student] = (room_id, row, col)
                    
                    # Check if swap is valid
                    if is_assignment_valid_local(new_assignment, students):
                        current_assignment = new_assignment
                        improvements_made += 1
                        improved_this_iteration = True
                        print(f"🔄 Swapped student {student} ({student_exam}) with {single_student} ({single_exam})")
                        
                        # Update single room list if this room now has diversity
                        new_analysis = analyze_room_diversity(current_assignment, students)
                        if single_room not in new_analysis.get('single_exam_rooms', []):
                            single_exam_rooms.remove(single_room)
                        break
                
                if improved_this_iteration:
                    break
            
            if improved_this_iteration:
                break
        
        if not improved_this_iteration:
            break
    
    print(f"🎉 Diversity improvements made: {improvements_made}")
    return current_assignment if improvements_made > 0 else assignment

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
    student_to_exam = {s: e for s, e
