"""Security module for authentication and authorization."""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from src.utils.config import Config

# Password hashing

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")





# OAuth2 scheme

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")



# API Key scheme

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)



# Mock database of users

# In production, this would come from a real database

fake_users_db = {

    "admin": {

        "username": "admin",

        "hashed_password": pwd_context.hash("admin"),

        "disabled": False,

        "api_keys": [] # List of key IDs

    }

}



# Mock database for API key lookups (key_id -> {username, hashed_secret})

fake_api_key_db = {}



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

    """Verify a password against a hash."""

    return pwd_context.verify(plain_password, hashed_password)



def get_password_hash(password: str) -> str:

    """Hash a password."""

    return pwd_context.hash(password)



def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:

    """Create a new JWT access token."""

    to_encode = data.copy()

    if expires_delta:

        expire = datetime.utcnow() + expires_delta

    else:

        expire = datetime.utcnow() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm="HS256")

    return encoded_jwt



async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:

    """Validate JWT token and return current user."""

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

    

    # Check mock DB

    if token_data.username in fake_users_db:

        user_data = fake_users_db[token_data.username]

        user = User(username=user_data["username"], disabled=user_data["disabled"])

    else:

        raise credentials_exception

        

    if user is None:

        raise credentials_exception

    return user



async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:

    """Check if the current user is active."""

    if current_user.disabled:

        raise HTTPException(status_code=400, detail="Inactive user")

    return current_user



async def verify_api_key(api_key: str = Depends(api_key_header)):

    """Validate API Key."""

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

            

            if key_id in fake_api_key_db:

                key_data = fake_api_key_db[key_id]

                if verify_password(secret, key_data["hashed_secret"]):

                    return api_key



    # If we got here and keys are required/configured, fail

    if Config.API_KEYS or fake_api_key_db: 

         raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail="Invalid API Key",

        )

    return api_key
