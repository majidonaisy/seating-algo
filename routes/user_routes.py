from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from sqlalchemy.orm import Session
from pydantic import BaseModel

import models
import crud
from database import get_db
from auth import (
    authenticate_user, 
    create_access_token, 
    get_current_active_user, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register", response_model=models.UserOut)
def create_user(user: models.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    return crud.create_user(db=db, email=user.email, name=user.name, password=user.password)

@router.post("/token", response_model=models.Token)
async def login_for_access_token(login: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, login.email, login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=models.UserOut)
async def read_users_me(current_user = Depends(get_current_active_user)):
    return current_user

@router.get("/{user_id}", response_model=models.UserOut)
def read_user(user_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/", response_model=list[models.UserOut])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), 
              current_user = Depends(get_current_active_user)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users