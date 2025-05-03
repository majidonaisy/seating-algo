from sqlalchemy.orm import Session
from typing import List, Optional
import crud
from models import RoomIn


def create_room(db: Session, room: RoomIn):
    return crud.create_room(
        db, room.room_id, room.rows, room.cols, room.skip_rows
    )

def get_rooms(db: Session, skip: int = 0, limit: int = 100):
    return crud.get_rooms(db, skip, limit)

def get_room(db: Session, room_id: str):
    return crud.get_room(db, room_id)

def update_room(db: Session, room_id: str, room: RoomIn):
    return crud.update_room(
        db, room_id, room.rows, room.cols, room.skip_rows
    )

def delete_room(db: Session, room_id: str):
    return crud.delete_room(db, room_id)
