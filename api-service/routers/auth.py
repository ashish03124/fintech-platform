# api-service/routers/auth.py
import os
import uuid
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from database import get_db
from models.models import User
from services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = auth_service.get_password_hash(user_data.password)
    user = User(
        id=str(uuid.uuid4()),
        email=user_data.email,
        hashed_password=hashed_pw,
        full_name=user_data.full_name,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token_data = {"user_id": user.id, "email": user.email, "role": "user"}
    return TokenResponse(
        access_token=auth_service.create_access_token(token_data),
        refresh_token=auth_service.create_refresh_token(token_data),
    )


@router.post("/token", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login with email and password, returns JWT tokens."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not auth_service.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    token_data = {"user_id": user.id, "email": user.email, "role": "user"}
    return TokenResponse(
        access_token=auth_service.create_access_token(token_data),
        refresh_token=auth_service.create_refresh_token(token_data),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """Get a new access token using a refresh token."""
    new_token = auth_service.refresh_access_token(refresh_token)
    if not new_token:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    return TokenResponse(
        access_token=new_token,
        refresh_token=refresh_token,
    )
