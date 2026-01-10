"""Authentication routes."""

import secrets
from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from src.api.security import (
    Token,
    User,
    create_access_token,
    get_password_hash,
    verify_password,
    UserInDB,
    get_current_active_user,
    fake_users_db,
    fake_api_key_db
)
from src.utils.config import Config

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(fake_users_db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/api-key", response_model=dict)
async def generate_api_key(
    current_user: User = Depends(get_current_active_user)
):
    """Generate a new API key for the current user."""
    # Generate random ID and Secret
    key_id = secrets.token_urlsafe(8)
    key_secret = secrets.token_urlsafe(32)
    
    raw_key = f"sk_{key_id}_{key_secret}"
    
    # Hash the secret
    hashed_secret = get_password_hash(key_secret)
    
    # Store in mock DB
    # 1. Add key ID to user's list
    if current_user.username in fake_users_db:
        # We need to access the mutable dict in the db
        fake_users_db[current_user.username]["api_keys"].append(key_id)
        
        # 2. Add to global key lookup
        fake_api_key_db[key_id] = {
            "username": current_user.username,
            "hashed_secret": hashed_secret,
            "created_at": "now" # In real app, use datetime
        }
    
    return {
        "api_key": raw_key,
        "key_id": key_id,
        "message": "Store this key safely. It will not be shown again."
    }
