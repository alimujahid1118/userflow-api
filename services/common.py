from typing import Annotated
from .database import Sessionlocal
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from auth.models import User
from datetime import datetime, timedelta, timezone

SECRET_KEY = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

def get_user_authenticate(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("id")
        exp = payload.get("exp")

        if username is None or user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        if datetime.now(timezone.utc).timestamp() > exp:
            raise HTTPException(status_code=401, detail="Session expired.")
        
        return {"username": username, "id": user_id}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

user_dependency = Annotated[dict, Depends(get_user_authenticate)]

def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not bcrypt_context.verify(password, user.hashed_password):
        return None
    return user

def create_access_token(username: str, user_id: int, expiry: timedelta = timedelta(minutes=20)):
    now = datetime.now(timezone.utc)
    expires = now + expiry
    encode = {"sub": username, "id": user_id, "exp": expires}
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(username: str, user_id: int, expiry: timedelta = timedelta(days=7)):
    now = datetime.now(timezone.utc)
    expires = now + expiry
    encode = {"sub": username, "id": user_id, "scope": "refresh_token", "exp": expires}
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
