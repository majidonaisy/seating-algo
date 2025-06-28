from sqlalchemy.orm import Session
import models
from typing import List, Optional
from datetime import date
from auth import get_password_hash


# User CRUD operations
def create_user(db: Session, email: str, name: str, password: str):
    hashed_password = get_password_hash(password)
    db_user = models.User(email=email, name=name, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).order_by(models.User.id).offset(skip).limit(limit).all()

def update_user(db: Session, user_id: int, name: Optional[str] = None, 
                email: Optional[str] = None, is_active: Optional[bool] = None):
    db_user = get_user(db, user_id)
    if db_user:
        if name is not None:
            db_user.name = name
        if email is not None:
            db_user.email = email
        if is_active is not None:
            db_user.is_active = is_active
        db.commit()
        db.refresh(db_user)
    return db_user


# Student CRUD operations
def create_student(db: Session, name: str, major: str):
    db_student = models.Student(name=name, major=major)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def get_students(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Student).order_by(models.Student.id).offset(skip).limit(limit).all()

def get_student(db: Session, student_id: int):
    return db.query(models.Student).filter(models.Student.id == student_id).first()

def update_student(db: Session, student_id: int, name: str, major: str):
    db_student = get_student(db, student_id)
    if db_student:
        db_student.name = name
        db_student.major = major
        db.commit()
        db.refresh(db_student)
    return db_student

def delete_student(db: Session, student_id: int):
    db_student = get_student(db, student_id)
    if db_student:
        db.delete(db_student)
        db.commit()
        return True
    return False


# Room CRUD operations
def create_room(db: Session, room_id: str, rows: int, cols: int, skip_rows: bool):
    db_room = models.Room(room_id=room_id, rows=rows, cols=cols, skip_rows=skip_rows)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

def get_rooms(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Room).order_by(models.Room.id).offset(skip).limit(limit).all()

def get_room(db: Session, room_id: str):
    return db.query(models.Room).filter(models.Room.room_id == room_id).first()

def update_room(db: Session, room_id: str, rows: Optional[int] = None, 
                cols: Optional[int] = None, skip_rows: Optional[bool] = None):
    db_room = get_room(db, room_id)
    if db_room:
        if rows is not None:
            db_room.rows = rows
        if cols is not None:
            db_room.cols = cols
        if skip_rows is not None:
            db_room.skip_rows = skip_rows
        db.commit()
        db.refresh(db_room)
    return db_room

def delete_room(db: Session, room_id: str):
    db_room = get_room(db, room_id)
    if db_room:
        db.delete(db_room)
        db.commit()
        return True
    return False


# Assignment CRUD operations
def create_assignment(db: Session, student_id: int, room_id: str, exam_name: str, row: int, col: int, assignment_date: Optional[date] = None):
    db_assignment = models.Assignment(
        student_id=student_id,
        room_id=room_id,
        exam_name=exam_name,
        row=row,
        col=col,
        date=assignment_date if assignment_date else date.today()
    )
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

def get_assignments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Assignment).order_by(models.Assignment.id).offset(skip).limit(limit).all()

def get_student_assignments(db: Session, student_id: int):
    return db.query(models.Assignment).filter(models.Assignment.student_id == student_id).all()

def get_room_assignments(db: Session, room_id: str):
    return db.query(models.Assignment).filter(models.Assignment.room_id == room_id).all()

def delete_assignment(db: Session, assignment_id: int):
    db_assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if db_assignment:
        db.delete(db_assignment)
        db.commit()
        return True
    return False
