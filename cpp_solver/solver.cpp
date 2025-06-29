#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <unordered_map>
#include <iostream>
#include <ortools/sat/cp_model.h>

using namespace operations_research::sat;

struct Student {
    int id;
    std::string exam;
};

struct Room {
    std::string id;
    int rows, cols;
    bool skip_rows, skip_cols;
};

struct Assignment {
    int student_id;
    std::string room_id;
    int row, col;
};

class FastSeatingOptimizer {
public:
    std::vector<Assignment> solve(
        const std::vector<Student>& students,
        const std::vector<Room>& rooms,
        const std::unordered_map<std::string, std::vector<std::string>>& restrictions,
        int timeout_seconds = 120
    ) {
        CpModelBuilder cp_model;
        
        // Precompute room positions (much faster in C++)
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
        }
        
        // Create variables (vectorized operations)
        std::unordered_map<std::string, BoolVar> variables;
        
        // Build constraints efficiently
        // ... (implement core CP-SAT logic in C++)
        
        // Solve
        CpSolver solver;
        solver.GetMutableParameters()->set_max_time_in_seconds(timeout_seconds);
        solver.GetMutableParameters()->set_num_search_workers(4);
        
        const CpSolverResponse response = solver.Solve(cp_model.Build());
        
        // Extract results
        std::vector<Assignment> assignments;
        if (response.status() == CpSolverStatus::OPTIMAL || 
            response.status() == CpSolverStatus::FEASIBLE) {
            // Extract solution...
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