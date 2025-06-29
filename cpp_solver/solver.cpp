#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <iostream>
#include <chrono>
#include <ortools/sat/cp_model.h>

using namespace operations_research::sat;

struct Student {
    int id;
    std::string exam;
    
    Student() = default;
    Student(int i, const std::string& e) : id(i), exam(e) {}
};

struct Room {
    std::string id;
    int rows, cols;
    bool skip_rows, skip_cols;
    
    Room() = default;
    Room(const std::string& i, int r, int c, bool sr, bool sc) 
        : id(i), rows(r), cols(c), skip_rows(sr), skip_cols(sc) {}
};

struct Assignment {
    int student_id;
    std::string room_id;
    int row, col;
    
    Assignment() = default;
    Assignment(int sid, const std::string& rid, int r, int c) 
        : student_id(sid), room_id(rid), row(r), col(c) {}
};

class FastSeatingOptimizer {
private:
    std::vector<std::vector<std::pair<int, int>>> precompute_positions(const std::vector<Room>& rooms) {
        std::vector<std::vector<std::pair<int, int>>> room_positions;
        
        for (const auto& room : rooms) {
            std::vector<std::pair<int, int>> positions;
            
            for (int r = 0; r < room.rows; r++) {
                if (room.skip_rows && r % 2 != 0) continue;
                
                for (int c = 0; c < room.cols; c++) {
                    if (room.skip_cols && c % 2 != 0) continue;
                    positions.push_back({r, c});
                }
            }
            
            room_positions.push_back(positions);
            std::cout << "Room " << room.id << ": " << positions.size() << " positions" << std::endl;
        }
        
        return room_positions;
    }
    
    bool is_adjacent(const std::pair<int, int>& pos1, const std::pair<int, int>& pos2) {
        return std::abs(pos1.first - pos2.first) + std::abs(pos1.second - pos2.second) == 1;
    }

public:
    std::vector<Assignment> solve(
        const std::vector<Student>& students,
        const std::vector<Room>& rooms,
        const std::unordered_map<std::string, std::vector<std::string>>& restrictions,
        int timeout_seconds = 120
    ) {
        auto start_time = std::chrono::high_resolution_clock::now();
        
        std::cout << "Starting C++ solver with " << students.size() << " students and " 
                  << rooms.size() << " rooms" << std::endl;
        
        CpModelBuilder cp_model;
        
        // Precompute room positions
        auto room_positions = precompute_positions(rooms);
        
        // Calculate total capacity
        int total_capacity = 0;
        for (const auto& positions : room_positions) {
            total_capacity += positions.size();
        }
        
        std::cout << "Total capacity: " << total_capacity << ", Students: " << students.size() << std::endl;
        
        if (total_capacity < static_cast<int>(students.size())) {
            std::cout << "ERROR: Not enough capacity!" << std::endl;
            return {};
        }
        
        // Build exam groupings
        std::unordered_map<std::string, std::vector<int>> exam_to_students;
        std::unordered_map<int, std::string> exam_of;
        
        for (const auto& student : students) {
            exam_to_students[student.exam].push_back(student.id);
            exam_of[student.id] = student.exam;
        }
        
        // Create variables - using string keys for simplicity
        std::unordered_map<std::string, BoolVar> x;
        std::vector<BoolVar> y; // room usage variables
        
        // Create room usage variables
        for (size_t ki = 0; ki < rooms.size(); ki++) {
            y.push_back(cp_model.NewBoolVar());
        }
        
        // Create student assignment variables
        int variable_count = 0;
        for (const auto& student : students) {
            const std::string& exam = student.exam;
            
            for (size_t ki = 0; ki < rooms.size(); ki++) {
                // Check restrictions
                if (restrictions.find(exam) != restrictions.end()) {
                    const auto& allowed_rooms = restrictions.at(exam);
                    if (std::find(allowed_rooms.begin(), allowed_rooms.end(), rooms[ki].id) 
                        == allowed_rooms.end()) {
                        continue; // Skip this room for this exam
                    }
                }
                
                for (const auto& pos : room_positions[ki]) {
                    std::string var_key = std::to_string(student.id) + "_" + 
                                        std::to_string(ki) + "_" + 
                                        std::to_string(pos.first) + "_" + 
                                        std::to_string(pos.second);
                    x[var_key] = cp_model.NewBoolVar();
                    variable_count++;
                }
            }
        }
        
        std::cout << "Created " << variable_count << " variables" << std::endl;
        
        // Constraint 1: Each student sits exactly once
        for (const auto& student : students) {
            std::vector<BoolVar> student_vars;
            
            for (size_t ki = 0; ki < rooms.size(); ki++) {
                for (const auto& pos : room_positions[ki]) {
                    std::string var_key = std::to_string(student.id) + "_" + 
                                        std::to_string(ki) + "_" + 
                                        std::to_string(pos.first) + "_" + 
                                        std::to_string(pos.second);
                    
                    if (x.find(var_key) != x.end()) {
                        student_vars.push_back(x[var_key]);
                    }
                }
            }
            
            if (!student_vars.empty()) {
                cp_model.AddEquality(LinearExpr::Sum(student_vars), 1);
            }
        }
        
        // Constraint 2: No double booking + room usage linking
        for (size_t ki = 0; ki < rooms.size(); ki++) {
            for (const auto& pos : room_positions[ki]) {
                std::vector<BoolVar> seat_vars;
                
                for (const auto& student : students) {
                    std::string var_key = std::to_string(student.id) + "_" + 
                                        std::to_string(ki) + "_" + 
                                        std::to_string(pos.first) + "_" + 
                                        std::to_string(pos.second);
                    
                    if (x.find(var_key) != x.end()) {
                        seat_vars.push_back(x[var_key]);
                        // Link to room usage
                        cp_model.AddLessOrEqual(x[var_key], y[ki]);
                    }
                }
                
                if (!seat_vars.empty()) {
                    cp_model.AddLessOrEqual(LinearExpr::Sum(seat_vars), 1);
                }
            }
        }
        
        // Constraint 3: Separation constraints (optimized)
        int separation_count = 0;
        const int MAX_SEPARATION_CONSTRAINTS = 50000; // Limit to prevent explosion
        
        for (const auto& exam_group : exam_to_students) {
            if (exam_group.second.size() < 2) continue;
            
            const auto& studs = exam_group.second;
            
            for (size_t ki = 0; ki < rooms.size(); ki++) {
                const auto& positions = room_positions[ki];
                
                // Find adjacent pairs
                for (size_t i = 0; i < positions.size() && separation_count < MAX_SEPARATION_CONSTRAINTS; i++) {
                    for (size_t j = i + 1; j < positions.size() && separation_count < MAX_SEPARATION_CONSTRAINTS; j++) {
                        if (!is_adjacent(positions[i], positions[j])) continue;
                        
                        // Add constraints for all student pairs in same exam
                        for (size_t si = 0; si < studs.size() && separation_count < MAX_SEPARATION_CONSTRAINTS; si++) {
                            for (size_t sj = si + 1; sj < studs.size() && separation_count < MAX_SEPARATION_CONSTRAINTS; sj++) {
                                std::string var1 = std::to_string(studs[si]) + "_" + 
                                                 std::to_string(ki) + "_" + 
                                                 std::to_string(positions[i].first) + "_" + 
                                                 std::to_string(positions[i].second);
                                
                                std::string var2 = std::to_string(studs[sj]) + "_" + 
                                                 std::to_string(ki) + "_" + 
                                                 std::to_string(positions[j].first) + "_" + 
                                                 std::to_string(positions[j].second);
                                
                                if (x.find(var1) != x.end() && x.find(var2) != x.end()) {
                                    cp_model.AddLessOrEqual(LinearExpr::Sum({x[var1], x[var2]}), 1);
                                    separation_count++;
                                }
                            }
                        }
                    }
                }
            }
        }
        
        std::cout << "Added " << separation_count << " separation constraints" << std::endl;
        
        // Objective: minimize rooms used
        cp_model.Minimize(LinearExpr::Sum(y));
        
        // Solve
        CpSolver solver;
        solver.GetMutableParameters()->set_max_time_in_seconds(timeout_seconds);
        solver.GetMutableParameters()->set_num_search_workers(4);
        solver.GetMutableParameters()->set_search_branching(SatParameters::PORTFOLIO_SEARCH);
        solver.GetMutableParameters()->set_cp_model_presolve(true);
        
        std::cout << "Starting C++ solver..." << std::endl;
        const CpSolverResponse response = solver.Solve(cp_model.Build());
        
        auto solve_time = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::high_resolution_clock::now() - start_time
        ).count();
        
        std::cout << "C++ solver completed in " << solve_time << "ms" << std::endl;
        std::cout << "Status: " << static_cast<int>(response.status()) << std::endl;
        
        // Extract results
        std::vector<Assignment> assignments;
        
        if (response.status() == CpSolverStatus::OPTIMAL || 
            response.status() == CpSolverStatus::FEASIBLE) {
            
            for (const auto& student : students) {
                for (size_t ki = 0; ki < rooms.size(); ki++) {
                    for (const auto& pos : room_positions[ki]) {
                        std::string var_key = std::to_string(student.id) + "_" + 
                                            std::to_string(ki) + "_" + 
                                            std::to_string(pos.first) + "_" + 
                                            std::to_string(pos.second);
                        
                        if (x.find(var_key) != x.end() && 
                            SolutionBooleanValue(response, x[var_key])) {
                            assignments.emplace_back(student.id, rooms[ki].id, pos.first, pos.second);
                            break;
                        }
                    }
                }
            }
            
            std::cout << "C++ solver assigned " << assignments.size() << " students" << std::endl;
        }
        
        return assignments;
    }
};

PYBIND11_MODULE(fast_solver, m) {
    pybind11::class_<Student>(m, "Student")
        .def(pybind11::init<int, std::string>())
        .def_readwrite("id", &Student::id)
        .def_readwrite("exam", &Student::exam);
    
    pybind11::class_<Room>(m, "Room")
        .def(pybind11::init<std::string, int, int, bool, bool>())
        .def_readwrite("id", &Room::id)
        .def_readwrite("rows", &Room::rows)
        .def_readwrite("cols", &Room::cols)
        .def_readwrite("skip_rows", &Room::skip_rows)
        .def_readwrite("skip_cols", &Room::skip_cols);
    
    pybind11::class_<Assignment>(m, "Assignment")
        .def_readwrite("student_id", &Assignment::student_id)
        .def_readwrite("room_id", &Assignment::room_id)
        .def_readwrite("row", &Assignment::row)
        .def_readwrite("col", &Assignment::col);
    
    pybind11::class_<FastSeatingOptimizer>(m, "FastSeatingOptimizer")
        .def(pybind11::init<>())
        .def("solve", &FastSeatingOptimizer::solve);
}