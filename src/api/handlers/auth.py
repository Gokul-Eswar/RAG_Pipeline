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
    get_user,
    store_api_key,
)
from src.utils.config import Config

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)

def _get_user_for_login(username: str):
    return get_user(username)

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = _get_user_for_login(form_data.username)
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
    
    # Persist API key in Redis-backed store
    store_api_key(key_id, current_user.username, key_secret)
    
    return {
        "api_key": raw_key,
        "key_id": key_id,
        "message": "Store this key safely. It will not be shown again."
    }
