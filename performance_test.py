"""
Performance Comparison Test
Compares different optimization strategies
"""

import time
import sys
import os

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_data(num_students, num_exams, num_rooms):
    """Generate test data of varying sizes"""
    students = [(i, f"Exam{i % num_exams + 1}") for i in range(1, num_students + 1)]
    
    rooms = []
    for i in range(num_rooms):
        # Vary room sizes
        rows = 3 + (i % 4)  # 3-6 rows
        cols = 4 + (i % 3)  # 4-6 cols
        skip_rows = i % 3 == 0  # Some rooms skip rows
        skip_cols = i % 2 == 0  # Some rooms skip cols
        rooms.append((f"Room{chr(65+i)}", rows, cols, skip_rows, skip_cols))
    
    return students, rooms

def test_solver_performance():
    """Test all available solvers with different problem sizes"""
    print("🧪 SEATING ASSIGNMENT SOLVER PERFORMANCE COMPARISON")
    print("=" * 70)
    
    test_cases = [
        {"name": "Small", "students": 12, "exams": 3, "rooms": 3},
        {"name": "Medium", "students": 30, "exams": 4, "rooms": 4},
        {"name": "Large", "students": 60, "exams": 5, "rooms": 6},
        {"name": "XLarge", "students": 100, "exams": 6, "rooms": 8},
    ]
    
    # Import available solvers - ONLY NEW OPTIMIZED ALGORITHMS
    solvers = []
    
    # Simple greedy solver (fastest, always works)
    try:
        from simple_greedy_solver import assign_students_greedy, assign_students_smart_greedy
        solvers.append(("Greedy", assign_students_greedy, 30))
        solvers.append(("Smart Greedy", assign_students_smart_greedy, 30))
        print("✅ Greedy solvers loaded")
    except ImportError:
        print("⚠️ Greedy solvers not available")
    
    # Ultra fast solver (optimized CP-SAT)
    try:
        from ultra_fast_app import assign_students_to_rooms_ultra_fast
        solvers.append(("Ultra Fast CP-SAT", assign_students_to_rooms_ultra_fast, 30))
        print("✅ Ultra fast CP-SAT solver loaded")
    except ImportError:
        print("⚠️ Ultra fast solver not available")
    
    # Numba optimized solver (if working)
    try:
        from numba_fast_app import assign_students_to_rooms_numba
        solvers.append(("Numba Optimized", assign_students_to_rooms_numba, 30))
        print("✅ Numba solver loaded")
    except ImportError:
        print("⚠️ Numba solver not available")
    
    if not solvers:
        print("❌ No solvers available for testing")
        return
    
    print(f"Found {len(solvers)} solvers to test")
    print()
    
    # Results storage
    results = {}
    
    for test_case in test_cases:
        print(f"📊 {test_case['name']} Problem ({test_case['students']} students, {test_case['rooms']} rooms)")
        print("-" * 50)
        
        students, rooms = create_test_data(
            test_case['students'], 
            test_case['exams'], 
            test_case['rooms']
        )
        
        # Calculate problem size metrics
        total_positions = sum(
            len([(r, c) for r in range(rows) for c in range(cols)
                if not (skip_rows and r % 2 != 0) and not (skip_cols and c % 2 != 0)])
            for _, rows, cols, skip_rows, skip_cols in rooms
        )
        
        print(f"Problem size: {len(students)} students, {total_positions} total seats")
        
        test_results = {}
        
        for solver_name, solver_func, timeout in solvers:
            try:
                print(f"Testing {solver_name}...", end=" ", flush=True)
                
                start_time = time.time()
                result = solver_func(students, rooms, {}, timeout)
                end_time = time.time()
                
                duration = end_time - start_time
                
                if result and len(result) > 0:
                    success_rate = len(result) / len(students) * 100
                    print(f"✅ {duration:.3f}s ({success_rate:.1f}% assigned)")
                    test_results[solver_name] = {
                        'time': duration,
                        'success': True,
                        'assigned': len(result),
                        'success_rate': success_rate
                    }
                else:
                    print(f"❌ {duration:.3f}s (Failed)")
                    test_results[solver_name] = {
                        'time': duration,
                        'success': False,
                        'assigned': 0,
                        'success_rate': 0
                    }
                    
            except Exception as e:
                print(f"💥 Error: {str(e)[:50]}...")
                test_results[solver_name] = {
                    'time': timeout,
                    'success': False,
                    'assigned': 0,
                    'success_rate': 0,
                    'error': str(e)
                }
        
        results[test_case['name']] = test_results
        print()
    
    # Summary report
    print("📈 PERFORMANCE SUMMARY")
    print("=" * 70)
    
    # Create performance comparison table
    print(f"{'Solver':<20} {'Small':<12} {'Medium':<12} {'Large':<12} {'XLarge':<12}")
    print("-" * 70)
    
    for solver_name, _, _ in solvers:
        row = f"{solver_name:<20}"
        for test_case in test_cases:
            test_name = test_case['name']
            if test_name in results and solver_name in results[test_name]:
                result = results[test_name][solver_name]
                if result['success']:
                    row += f"{result['time']:.3f}s      "
                else:
                    row += "FAILED      "
            else:
                row += "N/A         "
        print(row)
    
    print()
    
    # Find best solver for each problem size
    print("🏆 BEST SOLVER BY PROBLEM SIZE")
    print("-" * 40)
    
    for test_case in test_cases:
        test_name = test_case['name']
        if test_name in results:
            best_solver = None
            best_time = float('inf')
            
            for solver_name, result in results[test_name].items():
                if result['success'] and result['success_rate'] >= 95:
                    if result['time'] < best_time:
                        best_time = result['time']
                        best_solver = solver_name
            
            if best_solver:
                print(f"{test_name:>8}: {best_solver} ({best_time:.3f}s)")
            else:
                print(f"{test_name:>8}: No successful solver")
    
    print()
    print("💡 RECOMMENDATIONS FOR OPTIMIZED ALGORITHMS")
    print("-" * 45)
    print("• Greedy: Ultra-fast, 95%+ success rate, use for quick results")
    print("• Smart Greedy: Slightly slower, better quality, best for most cases")
    print("• Ultra Fast CP-SAT: Optimal solutions, use when quality is critical")
    print("• Numba Optimized: Good balance of speed and optimality")
    print("• For 1000+ students: Consider C++ implementation or distributed approach")

if __name__ == "__main__":
    test_solver_performance()
