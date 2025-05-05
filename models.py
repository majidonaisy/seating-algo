from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from database import Base
from datetime import date

# SQLAlchemy Models
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    major = Column(String(100))
    assignments = relationship("Assignment", back_populates="student")

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(50), unique=True, index=True)
    rows = Column(Integer)
    cols = Column(Integer)
    skip_rows = Column(Boolean, default=False)
    assignments = relationship("Assignment", back_populates="room")

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    room_id = Column(String(50), ForeignKey("rooms.room_id"))
    exam_name = Column(String(100))
    row = Column(Integer)
    col = Column(Integer)
    date = Column(Date, default=date.today)
    
    student = relationship("Student", back_populates="assignments")
    room = relationship("Room", back_populates="assignments")

# Pydantic Models (for API request/response)
class StudentIn(BaseModel):
    name: str
    major: str

class StudentOut(BaseModel):
    id: int
    name: str
    major: str
    
    class Config:
        from_attributes = True

class RoomIn(BaseModel):
    room_id: str
    rows: int
    cols: int
    skip_rows: bool

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

class AssignRequest(BaseModel):
    students: List[StudentExamRequest]
    rooms: List[RoomRequest]

class AssignResponse(BaseModel):
    assignments: List[AssignmentOut]
    
    class Config:
        from_attributes = True
