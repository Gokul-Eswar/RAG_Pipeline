"""Security module for authentication and authorization."""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
"""Security module for authentication and authorization.

This module implements authentication backed by Redis. It keeps compatibility
with previous in-memory fallbacks when Redis is not available.
"""

from datetime import datetime, timedelta
import os
import json
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from src.utils.config import Config
from src.infrastructure.cache.redis import RedisCache

# Password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# API Key scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# Token models
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _redis_client():
    return RedisCache()._client


def _get_user_record(username: str) -> Optional[Dict[str, Any]]:
    client = _redis_client()
    if not client:
        return None
    val = client.get(f"user:{username}")
    if not val:
        return None
    try:
        return json.loads(val)
    except Exception:
        return None


def get_user(username: str) -> Optional[UserInDB]:
    """Return a UserInDB object for the given username, or None."""
    rec = _get_user_record(username)
    if not rec:
        return None
    return UserInDB(username=rec.get("username"), hashed_password=rec.get("hashed_password"), disabled=rec.get("disabled", False))


def _get_api_key_record(key_id: str) -> Optional[Dict[str, Any]]:
    client = _redis_client()
    if not client:
        return None
    val = client.get(f"api_key:{key_id}")
    if not val:
        return None
    try:
        return json.loads(val)
    except Exception:
        return None


def create_user(username: str, password: str, disabled: bool = False) -> bool:
    """Create a user in Redis. Returns True on success."""
    client = _redis_client()
    if not client:
        return False
    record = {
        "username": username,
        "hashed_password": get_password_hash(password),
        "disabled": disabled,
        "api_keys": []
    }
    try:
        client.set(f"user:{username}", json.dumps(record))
        return True
    except Exception:
        return False


def store_api_key(key_id: str, username: str, secret: str) -> bool:
    client = _redis_client()
    if not client:
        return False
    record = {
        "username": username,
        "hashed_secret": get_password_hash(secret)
    }
    try:
        client.set(f"api_key:{key_id}", json.dumps(record))
        # add key id to user's api_keys list
        user_rec = _get_user_record(username)
        if user_rec is not None:
            keys = user_rec.get("api_keys", [])
            if key_id not in keys:
                keys.append(key_id)
                user_rec["api_keys"] = keys
                client.set(f"user:{username}", json.dumps(user_rec))
        return True
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    # Try Redis-backed users first
    user_rec = _get_user_record(token_data.username)
    if user_rec:
        return User(username=user_rec["username"], disabled=user_rec.get("disabled", False))

    # Fallback to old in-memory admin for compatibility
    # (keeps behavior for tests or local dev)
    # If no user found, fail
    raise credentials_exception


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def verify_api_key(api_key: str = Depends(api_key_header)):
    if not api_key:
        return None

    # 1. Check Service Keys (Config)
    if api_key in Config.API_KEYS:
        return api_key

    # 2. Check User Keys
    # Format: sk_<id>_<secret>
    if api_key.startswith("sk_") and "_" in api_key[3:]:
        parts = api_key.split("_")
        if len(parts) >= 3:
            key_id = parts[1]
            secret = "_".join(parts[2:])

            key_data = _get_api_key_record(key_id)
            if key_data and verify_password(secret, key_data.get("hashed_secret", "")):
                return api_key

    # If API keys are configured, reject invalid keys
    if Config.API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key
    return api_key
