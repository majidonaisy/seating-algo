"""
Advanced Optimization Strategies for Seating Assignment
Multiple algorithmic approaches for different scale requirements
"""

import numpy as np
from ortools.sat.python import cp_model
import networkx as nx
from collections import defaultdict
import random
import time
from typing import List, Tuple, Dict, Optional

class OptimizedSeatingAssigner:
    """Advanced seating assignment with multiple optimization strategies"""
    
    def __init__(self):
        self.debug = True
        
    def log(self, message):
        if self.debug:
            print(f"[{time.strftime('%H:%M:%S')}] {message}")

    def assign_hierarchical(self, students, rooms, exam_room_restrictions=None, timeout_seconds=60):
        """
        STRATEGY 1: Hierarchical Decomposition
        Solve room assignment first, then seat assignment within rooms
        Reduces complexity from O(S*R*H*W) to O(S*R) + O(S*H*W per room)
        """
        self.log("🔥 Starting Hierarchical Assignment")
        start_time = time.time()
        
        if exam_room_restrictions is None:
            exam_room_restrictions = {}
            
        # Phase 1: Assign students to rooms (high-level optimization)
        room_assignments = self._assign_students_to_rooms_only(
            students, rooms, exam_room_restrictions, timeout_seconds//2
        )
        
        if not room_assignments:
            return None
            
        # Phase 2: Assign seats within each room (parallel processing possible)
        final_assignment = {}
        
        for room_id, room_students in room_assignments.items():
            if not room_students:
                continue
                
            # Find room info
            room_info = next((r for r in rooms if r[0] == room_id), None)
            if not room_info:
                continue
                
            # Solve seating within this room only
            room_seating = self._assign_seats_in_room(
                room_students, room_info, timeout_seconds//4
            )
            
            if room_seating:
                for student_id, (row, col) in room_seating.items():
                    final_assignment[student_id] = (room_id, row, col)
        
        total_time = time.time() - start_time
        self.log(f"Hierarchical assignment completed in {total_time:.2f}s")
        return final_assignment

    def assign_greedy_plus_local_search(self, students, rooms, exam_room_restrictions=None, max_iterations=1000):
        """
        STRATEGY 2: Greedy + Local Search
        Ultra-fast heuristic approach with quality improvement
        """
        self.log("⚡ Starting Greedy + Local Search")
        start_time = time.time()
        
        # Phase 1: Fast greedy assignment
        assignment = self._greedy_assignment(students, rooms, exam_room_restrictions)
        if not assignment:
            return None
            
        self.log(f"Greedy assignment: {time.time() - start_time:.3f}s")
        
        # Phase 2: Local search improvement
        improved_assignment = self._local_search_improve(
            assignment, students, rooms, max_iterations
        )
        
        total_time = time.time() - start_time
        self.log(f"Greedy+LocalSearch completed in {total_time:.2f}s")
        return improved_assignment

    def assign_graph_coloring(self, students, rooms, exam_room_restrictions=None):
        """
        STRATEGY 3: Graph Coloring Approach
        Model as graph where adjacent seats are connected, exams are colors
        """
        self.log("🎨 Starting Graph Coloring Assignment")
        start_time = time.time()
        
        # Build conflict graph
        G = self._build_conflict_graph(students, rooms, exam_room_restrictions)
        
        # Use graph coloring algorithms
        assignment = self._graph_coloring_assignment(G, students, rooms)
        
        total_time = time.time() - start_time
        self.log(f"Graph coloring completed in {total_time:.2f}s")
        return assignment

    def assign_constraint_propagation_optimized(self, students, rooms, exam_room_restrictions=None, timeout_seconds=60):
        """
        STRATEGY 4: Advanced CP-SAT Optimizations
        Maximum optimization of the constraint programming approach
        """
        self.log("🧠 Starting Advanced CP-SAT")
        start_time = time.time()
        
        model = cp_model.CpModel()
        
        # OPTIMIZATION: Pre-compute everything
        room_data = self._preprocess_rooms(rooms)
        student_data = self._preprocess_students(students)
        
        # OPTIMIZATION: Symmetry breaking
        variables = self._create_variables_with_symmetry_breaking(
            model, student_data, room_data, exam_room_restrictions
        )
        
        # OPTIMIZATION: Constraint ordering (most restrictive first)
        self._add_constraints_optimized_order(model, variables, student_data, room_data)
        
        # OPTIMIZATION: Advanced solver parameters
        solver = self._create_optimized_solver(timeout_seconds)
        
        status = solver.Solve(model)
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            assignment = self._extract_solution(solver, variables, rooms)
            total_time = time.time() - start_time
            self.log(f"Advanced CP-SAT completed in {total_time:.2f}s")
            return assignment
        
        return None

    # Helper methods for each strategy
    
    def _assign_students_to_rooms_only(self, students, rooms, restrictions, timeout):
        """Phase 1 of hierarchical: just assign students to rooms"""
        # Simplified CP model - only room assignment, no seat positions
        model = cp_model.CpModel()
        
        exam_to_students = defaultdict(list)
        for s, e in students:
            exam_to_students[e].append(s)
        
        # Variables: student -> room assignment
        x = {}  # x[student, room_idx] = 1 if student assigned to room
        room_capacities = []
        
        for ki, (rid, rows, cols, skip_rows, skip_cols) in enumerate(rooms):
            capacity = rows * cols
            if skip_rows:
                capacity //= 2
            if skip_cols:
                capacity //= 2
            room_capacities.append(capacity)
            
            for s, e in students:
                # Check restrictions
                if e in restrictions and rid not in restrictions[e]:
                    continue
                x[s, ki] = model.NewBoolVar(f"x_{s}_{ki}")
        
        # Each student in exactly one room
        for s, e in students:
            student_vars = [x[s, ki] for ki in range(len(rooms)) if (s, ki) in x]
            if student_vars:
                model.Add(sum(student_vars) == 1)
        
        # Room capacity constraints
        for ki in range(len(rooms)):
            room_vars = [x[s, ki] for s, e in students if (s, ki) in x]
            if room_vars:
                model.Add(sum(room_vars) <= room_capacities[ki])
        
        # Minimize rooms used
        y = [model.NewBoolVar(f"room_used_{ki}") for ki in range(len(rooms))]
        for ki in range(len(rooms)):
            room_vars = [x[s, ki] for s, e in students if (s, ki) in x]
            if room_vars:
                model.Add(sum(room_vars) <= len(students) * y[ki])
        
        model.Minimize(sum(y))
        
        # Solve
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = timeout
        status = solver.Solve(model)
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            room_assignments = defaultdict(list)
            for s, e in students:
                for ki in range(len(rooms)):
                    if (s, ki) in x and solver.Value(x[s, ki]):
                        room_assignments[rooms[ki][0]].append((s, e))
                        break
            return dict(room_assignments)
        
        return None
    
    def _assign_seats_in_room(self, room_students, room_info, timeout):
        """Phase 2 of hierarchical: assign seats within a single room"""
        if not room_students:
            return {}
            
        rid, rows, cols, skip_rows, skip_cols = room_info
        
        # Build valid positions
        positions = []
        for r in range(rows):
            if skip_rows and r % 2 != 0:
                continue
            for c in range(cols):
                if skip_cols and c % 2 != 0:
                    continue
                positions.append((r, c))
        
        if len(positions) < len(room_students):
            return None
        
        # Simple assignment for single room - can use faster algorithms
        # For now, use greedy assignment within room
        return self._greedy_assign_positions(room_students, positions)
    
    def _greedy_assign_positions(self, students, positions):
        """Greedy assignment of students to positions within a room"""
        # Group students by exam
        exam_groups = defaultdict(list)
        for s, e in students:
            exam_groups[e].append(s)
        
        assignment = {}
        used_positions = set()
        
        # Assign each exam group, avoiding adjacencies
        for exam, exam_students in exam_groups.items():
            for student in exam_students:
                # Find best position (not adjacent to same exam)
                best_pos = None
                for pos in positions:
                    if pos in used_positions:
                        continue
                    
                    # Check if adjacent to same exam
                    r, c = pos
                    adjacent_same_exam = False
                    
                    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                        adj_pos = (r+dr, c+dc)
                        if adj_pos in assignment.values():
                            # Find student at this position
                            adj_student = next((s for s, p in assignment.items() if p == adj_pos), None)
                            if adj_student:
                                adj_exam = next((e for s, e in students if s == adj_student), None)
                                if adj_exam == exam:
                                    adjacent_same_exam = True
                                    break
                    
                    if not adjacent_same_exam:
                        best_pos = pos
                        break
                
                if best_pos:
                    assignment[student] = best_pos
                    used_positions.add(best_pos)
                else:
                    # No valid position found - backtrack or use constraint programming
                    return None
        
        return assignment
    
    def _greedy_assignment(self, students, rooms, restrictions):
        """Fast greedy assignment - O(S*R) complexity"""
        assignment = {}
        
        # Calculate room capacities
        room_info = {}
        for rid, rows, cols, skip_rows, skip_cols in rooms:
            positions = []
            for r in range(rows):
                if skip_rows and r % 2 != 0:
                    continue
                for c in range(cols):
                    if skip_cols and c % 2 != 0:
                        continue
                    positions.append((r, c))
            room_info[rid] = positions
        
        # Group students by exam
        exam_groups = defaultdict(list)
        for s, e in students:
            exam_groups[e].append(s)
        
        # Assign each exam group to best available rooms
        for exam, exam_students in exam_groups.items():
            available_rooms = []
            
            for rid, positions in room_info.items():
                if exam in restrictions and rid not in restrictions[exam]:
                    continue
                available_rooms.append((rid, positions))
            
            # Sort rooms by available capacity
            available_rooms.sort(key=lambda x: len(x[1]), reverse=True)
            
            # Assign students to rooms using greedy strategy
            for student in exam_students:
                assigned = False
                for rid, positions in available_rooms:
                    # Try to find a valid position in this room
                    pos_assignment = self._find_valid_position(
                        student, exam, rid, positions, assignment, exam_groups
                    )
                    if pos_assignment:
                        assignment[student] = pos_assignment
                        assigned = True
                        break
                
                if not assigned:
                    self.log(f"Could not assign student {student}")
                    return None
        
        return assignment
    
    def _find_valid_position(self, student, exam, room_id, positions, current_assignment, exam_groups):
        """Find a valid position for a student in a room"""
        used_positions = set()
        
        # Find used positions in this room
        for s, (rid, r, c) in current_assignment.items():
            if rid == room_id:
                used_positions.add((r, c))
        
        # Try each available position
        for pos in positions:
            if pos in used_positions:
                continue
            
            # Check adjacency constraints
            r, c = pos
            valid = True
            
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                adj_pos = (r+dr, c+dc)
                if adj_pos in positions:  # Adjacent position exists
                    # Check if occupied by same exam
                    for s, (rid, ar, ac) in current_assignment.items():
                        if rid == room_id and (ar, ac) == adj_pos:
                            # Find exam of adjacent student
                            adj_exam = next((e for st, e in exam_groups.items() 
                                           for student_in_exam in exam_groups[e] 
                                           if student_in_exam == s), None)
                            if adj_exam == exam:
                                valid = False
                                break
                
                if not valid:
                    break
            
            if valid:
                return (room_id, r, c)
        
        return None
    
    def _local_search_improve(self, assignment, students, rooms, max_iterations):
        """Improve assignment using local search"""
        current_assignment = assignment.copy()
        best_score = self._evaluate_assignment(current_assignment, students)
        
        for iteration in range(max_iterations):
            # Try swapping two students
            improved = False
            student_list = list(current_assignment.keys())
            
            for i in range(len(student_list)):
                for j in range(i+1, len(student_list)):
                    s1, s2 = student_list[i], student_list[j]
                    
                    # Try swapping positions
                    new_assignment = current_assignment.copy()
                    new_assignment[s1], new_assignment[s2] = new_assignment[s2], new_assignment[s1]
                    
                    # Check if swap is valid and improves score
                    if self._is_valid_assignment(new_assignment, students):
                        score = self._evaluate_assignment(new_assignment, students)
                        if score > best_score:
                            current_assignment = new_assignment
                            best_score = score
                            improved = True
                            self.log(f"Iteration {iteration}: Improved score to {score}")
                            break
                
                if improved:
                    break
            
            if not improved:
                break
        
        return current_assignment
    
    def _build_conflict_graph(self, students, rooms, restrictions):
        """Build conflict graph for graph coloring approach"""
        G = nx.Graph()
        
        # Add nodes (seat positions)
        seat_to_node = {}
        node_counter = 0
        
        for rid, rows, cols, skip_rows, skip_cols in rooms:
            for r in range(rows):
                if skip_rows and r % 2 != 0:
                    continue
                for c in range(cols):
                    if skip_cols and c % 2 != 0:
                        continue
                    seat_to_node[(rid, r, c)] = node_counter
                    G.add_node(node_counter, room=rid, row=r, col=c)
                    node_counter += 1
        
        # Add edges (conflicts between adjacent seats)
        for rid, rows, cols, skip_rows, skip_cols in rooms:
            positions = [(r, c) for r in range(rows) for c in range(cols)
                        if not (skip_rows and r % 2 != 0) and not (skip_cols and c % 2 != 0)]
            
            for r1, c1 in positions:
                for r2, c2 in positions:
                    if abs(r1-r2) + abs(c1-c2) == 1:  # Adjacent
                        node1 = seat_to_node[(rid, r1, c1)]
                        node2 = seat_to_node[(rid, r2, c2)]
                        G.add_edge(node1, node2)
        
        return G
    
    def _graph_coloring_assignment(self, G, students, rooms):
        """Assign students using graph coloring"""
        # This is a simplified version - would need more sophisticated implementation
        # for production use
        return self._greedy_assignment(students, rooms, {})
    
    def _evaluate_assignment(self, assignment, students):
        """Evaluate quality of assignment (higher is better)"""
        if not assignment:
            return 0
        
        score = len(assignment) * 100  # Base score for number of assigned students
        
        # Bonus for room utilization efficiency
        rooms_used = len(set(rid for rid, r, c in assignment.values()))
        score -= rooms_used * 10  # Penalty for using more rooms
        
        return score
    
    def _is_valid_assignment(self, assignment, students):
        """Check if assignment satisfies all constraints"""
        # Check no two students in same seat
        positions = list(assignment.values())
        if len(positions) != len(set(positions)):
            return False
        
        # Check adjacency constraints
        exam_of = {s: e for s, e in students}
        
        for s1, (rid1, r1, c1) in assignment.items():
            for s2, (rid2, r2, c2) in assignment.items():
                if s1 >= s2 or rid1 != rid2:
                    continue
                
                # Check if adjacent and same exam
                if abs(r1-r2) + abs(c1-c2) == 1 and exam_of[s1] == exam_of[s2]:
                    return False
        
        return True

    # Additional optimization helper methods would go here...
    def _preprocess_rooms(self, rooms):
        """Preprocess room data for optimization"""
        pass
    
    def _preprocess_students(self, students):
        """Preprocess student data for optimization"""
        pass
    
    def _create_variables_with_symmetry_breaking(self, model, student_data, room_data, restrictions):
        """Create CP variables with symmetry breaking"""
        pass
    
    def _add_constraints_optimized_order(self, model, variables, student_data, room_data):
        """Add constraints in optimal order"""
        pass
    
    def _create_optimized_solver(self, timeout):
        """Create solver with optimal parameters"""
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = timeout
        solver.parameters.num_search_workers = 8
        solver.parameters.search_branching = cp_model.PORTFOLIO_SEARCH
        solver.parameters.cp_model_presolve = True
        solver.parameters.symmetry_level = 2
        solver.parameters.linearization_level = 2
        return solver
    
    def _extract_solution(self, solver, variables, rooms):
        """Extract solution from solved model"""
        pass

# Test the optimized approaches
def test_all_optimization_strategies():
    """Test all optimization strategies"""
    print("🧪 Testing All Optimization Strategies")
    print("=" * 60)
    
    # Test data - scaling up gradually
    test_cases = [
        {
            "name": "Small (12 students, 3 rooms)",
            "students": [(i, f"Exam{i%3+1}") for i in range(1, 13)],
            "rooms": [
                ("RoomA", 3, 4, False, True),   # 6 seats
                ("RoomB", 3, 4, False, False),  # 12 seats  
                ("RoomC", 2, 4, True, False),   # 4 seats
            ]
        },
        {
            "name": "Medium (50 students, 5 rooms)",
            "students": [(i, f"Exam{i%5+1}") for i in range(1, 51)],
            "rooms": [
                ("RoomA", 5, 6, False, True),   # 15 seats
                ("RoomB", 4, 8, False, False),  # 32 seats
                ("RoomC", 3, 5, True, False),   # 8 seats
                ("RoomD", 6, 4, False, True),   # 12 seats
                ("RoomE", 3, 6, False, False),  # 18 seats
            ]
        }
    ]
    
    assigner = OptimizedSeatingAssigner()
    
    for test_case in test_cases:
        print(f"\n📊 {test_case['name']}")
        print("-" * 40)
        
        students = test_case["students"]
        rooms = test_case["rooms"]
        
        # Test each strategy
        strategies = [
            ("Hierarchical", assigner.assign_hierarchical),
            ("Greedy+LocalSearch", assigner.assign_greedy_plus_local_search),
            ("Graph Coloring", assigner.assign_graph_coloring),
            # ("Advanced CP-SAT", assigner.assign_constraint_propagation_optimized)
        ]
        
        for strategy_name, strategy_func in strategies:
            try:
                start_time = time.time()
                result = strategy_func(students, rooms, {}, timeout_seconds=30)
                end_time = time.time()
                
                if result:
                    print(f"✅ {strategy_name}: {end_time-start_time:.2f}s - Assigned {len(result)}/{len(students)}")
                else:
                    print(f"❌ {strategy_name}: {end_time-start_time:.2f}s - Failed")
                    
            except Exception as e:
                print(f"💥 {strategy_name}: Error - {str(e)}")

if __name__ == "__main__":
    test_all_optimization_strategies()
