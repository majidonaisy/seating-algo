"""
C++ Ultra-Fast Seating Assignment Solver
Compile with: g++ -O3 -std=c++17 seating_solver.cpp -o seating_solver
"""

cpp_solver_code = '''
#include <iostream>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <algorithm>
#include <chrono>
#include <random>

struct Student {
    int id;
    std::string exam;
};

struct Room {
    std::string id;
    int rows, cols;
    bool skip_rows, skip_cols;
    std::vector<std::pair<int, int>> positions;
};

struct Assignment {
    int student_id;
    std::string room_id;
    int row, col;
};

class UltraFastSeatingAssigner {
private:
    std::vector<Student> students;
    std::vector<Room> rooms;
    std::unordered_map<std::string, std::vector<int>> exam_to_students;
    std::unordered_map<int, std::string> student_to_exam;
    
public:
    void setStudents(const std::vector<Student>& studs) {
        students = studs;
        exam_to_students.clear();
        student_to_exam.clear();
        
        for (const auto& s : students) {
            exam_to_students[s.exam].push_back(s.id);
            student_to_exam[s.id] = s.exam;
        }
    }
    
    void setRooms(const std::vector<Room>& rms) {
        rooms = rms;
        
        // Precompute valid positions for each room
        for (auto& room : rooms) {
            room.positions.clear();
            for (int r = 0; r < room.rows; r++) {
                if (room.skip_rows && r % 2 != 0) continue;
                for (int c = 0; c < room.cols; c++) {
                    if (room.skip_cols && c % 2 != 0) continue;
                    room.positions.push_back({r, c});
                }
            }
        }
    }
    
    std::vector<Assignment> assignGreedy() {
        auto start = std::chrono::high_resolution_clock::now();
        
        std::vector<Assignment> assignments;
        std::unordered_set<std::string> used_positions; // "room_id:row:col"
        
        // Sort exams by number of students (largest first)
        std::vector<std::string> exam_order;
        for (const auto& [exam, studs] : exam_to_students) {
            exam_order.push_back(exam);
        }
        std::sort(exam_order.begin(), exam_order.end(), 
                 [this](const std::string& a, const std::string& b) {
                     return exam_to_students[a].size() > exam_to_students[b].size();
                 });
        
        // Assign each exam
        for (const std::string& exam : exam_order) {
            std::cout << "Assigning exam: " << exam << " (" 
                     << exam_to_students[exam].size() << " students)\\n";
            
            for (int student_id : exam_to_students[exam]) {
                bool assigned = false;
                
                // Try each room
                for (const auto& room : rooms) {
                    Assignment best_assignment = findBestPositionInRoom(
                        student_id, exam, room, used_positions, assignments
                    );
                    
                    if (best_assignment.student_id != -1) {
                        assignments.push_back(best_assignment);
                        std::string pos_key = best_assignment.room_id + ":" + 
                                            std::to_string(best_assignment.row) + ":" + 
                                            std::to_string(best_assignment.col);
                        used_positions.insert(pos_key);
                        assigned = true;
                        break;
                    }
                }
                
                if (!assigned) {
                    std::cout << "Failed to assign student " << student_id << "\\n";
                    return {}; // Return empty if can't assign all
                }
            }
        }
        
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
        std::cout << "C++ Greedy assignment completed in " << duration.count() << "ms\\n";
        
        return assignments;
    }
    
private:
    Assignment findBestPositionInRoom(int student_id, const std::string& exam, 
                                    const Room& room, 
                                    const std::unordered_set<std::string>& used_positions,
                                    const std::vector<Assignment>& current_assignments) {
        
        Assignment best{-1, "", -1, -1}; // Invalid assignment
        int best_score = -1;
        
        for (const auto& [row, col] : room.positions) {
            std::string pos_key = room.id + ":" + std::to_string(row) + ":" + std::to_string(col);
            
            if (used_positions.count(pos_key)) {
                continue; // Position already used
            }
            
            // Check adjacency constraints
            if (violatesAdjacencyConstraint(row, col, room, exam, current_assignments)) {
                continue;
            }
            
            // Score this position (prefer positions that maximize future options)
            int score = scorePosition(row, col, room, used_positions);
            
            if (score > best_score) {
                best = {student_id, room.id, row, col};
                best_score = score;
            }
        }
        
        return best;
    }
    
    bool violatesAdjacencyConstraint(int row, int col, const Room& room, 
                                   const std::string& exam,
                                   const std::vector<Assignment>& assignments) {
        
        // Check all adjacent positions
        std::vector<std::pair<int, int>> directions = {{-1,0}, {1,0}, {0,-1}, {0,1}};
        
        for (const auto& [dr, dc] : directions) {
            int adj_row = row + dr;
            int adj_col = col + dc;
            
            // Check if adjacent position is valid in this room
            bool valid_adj = false;
            for (const auto& [r, c] : room.positions) {
                if (r == adj_row && c == adj_col) {
                    valid_adj = true;
                    break;
                }
            }
            
            if (!valid_adj) continue;
            
            // Check if adjacent position has same exam student
            for (const auto& assignment : assignments) {
                if (assignment.room_id == room.id && 
                    assignment.row == adj_row && 
                    assignment.col == adj_col) {
                    
                    std::string adj_exam = student_to_exam[assignment.student_id];
                    if (adj_exam == exam) {
                        return true; // Violation found
                    }
                }
            }
        }
        
        return false;
    }
    
    int scorePosition(int row, int col, const Room& room, 
                     const std::unordered_set<std::string>& used_positions) {
        // Simple scoring: prefer positions with more free adjacent spaces
        int free_adjacent = 0;
        std::vector<std::pair<int, int>> directions = {{-1,0}, {1,0}, {0,-1}, {0,1}};
        
        for (const auto& [dr, dc] : directions) {
            int adj_row = row + dr;
            int adj_col = col + dc;
            
            // Check if adjacent position exists and is free
            for (const auto& [r, c] : room.positions) {
                if (r == adj_row && c == adj_col) {
                    std::string pos_key = room.id + ":" + std::to_string(adj_row) + ":" + std::to_string(adj_col);
                    if (!used_positions.count(pos_key)) {
                        free_adjacent++;
                    }
                    break;
                }
            }
        }
        
        return free_adjacent;
    }
};

// Python interface functions (for integration)
extern "C" {
    UltraFastSeatingAssigner* create_assigner() {
        return new UltraFastSeatingAssigner();
    }
    
    void destroy_assigner(UltraFastSeatingAssigner* assigner) {
        delete assigner;
    }
    
    void set_students(UltraFastSeatingAssigner* assigner, int* student_ids, 
                     char** exam_names, int count) {
        std::vector<Student> students;
        for (int i = 0; i < count; i++) {
            students.push_back({student_ids[i], std::string(exam_names[i])});
        }
        assigner->setStudents(students);
    }
    
    void set_rooms(UltraFastSeatingAssigner* assigner, char** room_ids, 
                  int* rows, int* cols, bool* skip_rows, bool* skip_cols, int count) {
        std::vector<Room> rooms;
        for (int i = 0; i < count; i++) {
            Room room;
            room.id = std::string(room_ids[i]);
            room.rows = rows[i];
            room.cols = cols[i]; 
            room.skip_rows = skip_rows[i];
            room.skip_cols = skip_cols[i];
            rooms.push_back(room);
        }
        assigner->setRooms(rooms);
    }
    
    int assign_greedy(UltraFastSeatingAssigner* assigner, int* student_ids,
                     char** room_ids, int* rows, int* cols, int max_assignments) {
        auto assignments = assigner->assignGreedy();
        
        int count = std::min((int)assignments.size(), max_assignments);
        for (int i = 0; i < count; i++) {
            student_ids[i] = assignments[i].student_id;
            strcpy(room_ids[i], assignments[i].room_id.c_str());
            rows[i] = assignments[i].row;
            cols[i] = assignments[i].col;
        }
        
        return count;
    }
}

// Test main function
int main() {
    std::cout << "🚀 Testing C++ Ultra-Fast Seating Assigner\\n";
    
    UltraFastSeatingAssigner assigner;
    
    // Test data
    std::vector<Student> students = {
        {1, "Math"}, {2, "Math"}, {3, "Math"}, {4, "Math"},
        {5, "Physics"}, {6, "Physics"}, {7, "Physics"}, {8, "Physics"},
        {9, "Chemistry"}, {10, "Chemistry"}, {11, "Chemistry"}, {12, "Chemistry"}
    };
    
    std::vector<Room> rooms = {
        {"RoomA", 3, 4, false, true},   // 6 seats
        {"RoomB", 3, 4, false, false},  // 12 seats
        {"RoomC", 2, 4, true, false}    // 4 seats
    };
    
    assigner.setStudents(students);
    assigner.setRooms(rooms);
    
    auto assignments = assigner.assignGreedy();
    
    if (!assignments.empty()) {
        std::cout << "✅ Successfully assigned " << assignments.size() << " students\\n";
        
        // Print assignments
        for (const auto& assignment : assignments) {
            std::cout << "Student " << assignment.student_id 
                     << " -> " << assignment.room_id 
                     << " (" << assignment.row << "," << assignment.col << ")\\n";
        }
    } else {
        std::cout << "❌ Assignment failed\\n";
    }
    
    return 0;
}
'''

# Save C++ code to file
with open("seating_solver.cpp", "w") as f:
    f.write(cpp_solver_code)

print("C++ solver code generated: seating_solver.cpp")
print("Compile with: g++ -O3 -std=c++17 seating_solver.cpp -o seating_solver")
print("Expected speedup: 50-100x faster than Python for large instances")
