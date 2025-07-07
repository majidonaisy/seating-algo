from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from database import Base
from datetime import date, datetime

# SQLAlchemy Models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True)
    name = Column(String(100))
    hashed_password = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(Date, default=date.today)

# class Student(Base):
#     __tablename__ = "students"

#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(100), index=True)
#     major = Column(String(100))
#     assignments = relationship("Assignment", back_populates="student")

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(50), unique=True, index=True)
    rows = Column(Integer)
    cols = Column(Integer)
    skip_rows = Column(Boolean, default=False)
    skip_cols = Column(Integer, default=0)  # <-- changed from Boolean to Integer
    # assignments = relationship("Assignment", back_populates="room")

# class Assignment(Base):
#     __tablename__ = "assignments"

#     id = Column(Integer, primary_key=True, index=True)
#     student_id = Column(Integer, ForeignKey("students.id"))
#     room_id = Column(String(50), ForeignKey("rooms.room_id"))
#     exam_name = Column(String(100))
#     row = Column(Integer)
#     col = Column(Integer)
#     date = Column(Date, default=date.today)
    
#     student = relationship("Student", back_populates="assignments")
#     room = relationship("Room", back_populates="assignments")

# Pydantic Models (for API request/response)
# User models for authentication
class UserBase(BaseModel):
    email: str
    name: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: date
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class StudentIn(BaseModel):
    name: str
    major: str

class StudentOut(BaseModel):
    file_number: int
    examination_date: date
    course_code: str
    course_name: str
    language: str
    academic_year: str
    time: str

    class Config:
        from_attributes = True

class RoomIn(BaseModel):
    room_id: str
    rows: int
    cols: int
    skip_rows: bool
    skip_cols: int  # <-- changed to int

class AssignmentIn(BaseModel):
    student_id: int
    room_id: str
    exam_name: str
    row: int
    col: int
    date: Optional[date] = None

class AssignmentOut(BaseModel):
    id: int
    student_id: int
    room_id: str
    exam_name: str
    row: int
    col: int
    date: date
    
    class Config:
        from_attributes = True

class StudentExamRequest(BaseModel):
    student_id: int
    exam_name: str

class RoomRequest(BaseModel):
    room_id: str
    rows: int
    cols: int
    skip_rows: bool
    skip_cols: int  # <-- changed to int

class AssignRequest(BaseModel):
    students: List[StudentExamRequest]
    rooms: List[RoomRequest]
    exam_room_restrictions: Optional[Dict[str, List[str]]] = None

class AssignResponse(BaseModel):
    assignments: List[AssignmentOut]
    
    class Config:
        from_attributes = True

class AssignmentWithStudentOut(BaseModel):
    file_number: int
    name: str
    major: str
    examination_date: date
    course_code: str
    course_name: str
    language: str
    academic_year: str
    time: str
    room_id: str
    row: int
    col: int
    date: date

    class Config:
        from_attributes = True
