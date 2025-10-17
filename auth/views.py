from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from typing import Annotated
from datetime import timedelta
from .models import User
from services.common import db_dependency, bcrypt_context, create_access_token, authenticate_user
from .schemas import CreateUserRequest, Token

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def create_user_signup(create_user_request : CreateUserRequest, db : db_dependency):
    existing = db.query(User).filter(User.username == create_user_request.username).first()
    if existing:
        raise HTTPException(status_code=404, detail="User already exists.")
    
    create_user_model = User(
        username = create_user_request.username,
        hashed_password = bcrypt_context.hash(create_user_request.password)
    )
    db.add(create_user_model)
    db.commit()
    return {"message": "user created"}

@router.post("/login", response_model=Token)
def create_user_login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )

    access_token_expires = timedelta(minutes=20)
    access_token = create_access_token(
        username=user.username,
        user_id=user.id,
        expiry=access_token_expires
    )

    response = JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "bearer"
        }
    )

    response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,
    secure=False,
    samesite="lax"
    )   

    return response
