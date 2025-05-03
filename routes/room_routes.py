from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import RoomIn
import services.room_service as room_service

router = APIRouter(
    prefix="/rooms",
    tags=["rooms"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_room(room: RoomIn, db: Session = Depends(get_db)):
    return room_service.create_room(db, room)

@router.get("/", response_model=List[RoomIn])
def read_rooms(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    rooms = room_service.get_rooms(db, skip, limit)
    return rooms

@router.get("/{room_id}", response_model=RoomIn)
def read_room(room_id: str, db: Session = Depends(get_db)):
    room = room_service.get_room(db, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@router.put("/{room_id}", response_model=RoomIn)
def update_room(room_id: str, room: RoomIn, db: Session = Depends(get_db)):
    updated_room = room_service.update_room(db, room_id, room)
    if updated_room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return updated_room

@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(room_id: str, db: Session = Depends(get_db)):
    success = room_service.delete_room(db, room_id)
    if not success:
        raise HTTPException(status_code=404, detail="Room not found")
    return None
