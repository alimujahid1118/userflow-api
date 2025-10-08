from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import Sessionlocal, User, Profile as ProfileModel, Posts as PostsModel
from starlette import status
from passlib.context import CryptContext
from schemas import CreateUserRequest, ProfileSchema, Token, PostsSchema
from jose import jwt, JWTError
from typing import Annotated
from datetime import datetime, timedelta, timezone

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

SECRET_KEY = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/signup", status_code=status.HTTP_201_CREATED)

def create_user_signup(create_user_request : CreateUserRequest, db : db_dependency):
    create_user_model = User(
        username = create_user_request.username,
        hashed_password = bcrypt_context.hash(create_user_request.password)
    )
    db.add(create_user_model)
    db.commit()
    return {"message": "user created"}

@router.post("/login", response_model= Token)

def create_user_login(form_data : Annotated[OAuth2PasswordRequestForm, Depends()], db : db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    
    token = create_access_token(user.username, user.id, timedelta(minutes=20))

    profile = ProfileSchema

    return {"access_token" : token, "token_type" : "bearer"}

def authenticate_user(username : str, password : str, db : db_dependency):
    user = db.query(User).filter(User.username == username and bcrypt_context.hash(password) == User.hashed_password).first()
    if user is None:
        return None
    if bcrypt_context.verify(password, user.hashed_password) is None:
        return False
    if bcrypt_context.verify(password, user.hashed_password):
        return user

def create_access_token(username : str, user_id : int, expiry : timedelta):
    encode = {"sub" : username, "id" : user_id}
    now = datetime.now(timezone.utc)
    expires = now + expiry
    encode.update({"exp" : expires})

    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user_authenticate(token : Annotated[str , Depends(oauth2_bearer)]):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    user_id = payload.get("id")
    if username is None or user_id is None:
        raise HTTPException(status_code=401, detail= "Unauthorized request.")
    return {"username" : username, "id" : user_id}

user_dependency = Annotated[dict, Depends(get_user_authenticate)]

@router.get("/", status_code= status.HTTP_200_OK)

def get_user(user : user_dependency, db : db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail= "Unauthorized request.")
    return {"User" : user}

@router.post("/create-profile", status_code=status.HTTP_201_CREATED)

def create_profile(profile : ProfileSchema, user : user_dependency, db : db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail= "Unauthorized request.")
    existing_profile = db.query(ProfileModel).filter(ProfileModel.id == user["id"])
    if existing_profile is None:
        raise HTTPException(status_code=404, detail="Unable to fetch Profile.")
    new_profile = ProfileModel(
        name = profile.name,
        bio = profile.bio,
        user_id = user["id"]
    )
    db.add(new_profile)
    db.commit()

@router.get("/get-profile", status_code=status.HTTP_200_OK)

def get_profile(user : user_dependency, db : db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail= "Unauthorized request.")
    profile = db.query(ProfileModel).filter(ProfileModel.id == user["id"]).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="Unable to fetch Profile.")
    return profile

@router.put("/update-profile", status_code=status.HTTP_201_CREATED)

def update_profile(profile : ProfileSchema, user : user_dependency, db : db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail= "Unauthorized request.")
    existing_profile= db.query(ProfileModel).filter(ProfileModel.user_id == user["id"]).first()
    if existing_profile is None:
        raise HTTPException(status_code=404 , detail= "Unable to find a Profile")
    
    existing_profile.name = profile.name
    existing_profile.bio = profile.bio

    db.commit()
    db.refresh(existing_profile)

@router.delete("/delete-profile", status_code=status.HTTP_200_OK)

def delete_profile(user : user_dependency, db : db_dependency):
    profile = db.query(ProfileModel).filter(ProfileModel.id == user["id"]).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile doesn't exist")
    db.delete(profile)
    db.commit()

@router.post("/create-post", status_code=status.HTTP_201_CREATED)

def create_post(user : user_dependency, posts : PostsSchema, db : db_dependency):
    user = db.query(User).filter(User.id == user["id"]).first()
    if user is None:
        raise HTTPException(status_code=404, detail= "User not found.")
    profile = db.query(ProfileModel).filter(ProfileModel.user_id == user.id).first()
    if profile is None:
        raise HTTPException(status_code=404, detail= "Profile not found.")
    if profile:
        new_post = PostsModel(
            content = posts.content,
            user_id = user.id,
            profile_id = profile.id
        )
        db.add(new_post)
        db.commit()

@router.get("/get-post", status_code= status.HTTP_200_OK)

def get_post(user : user_dependency, db : db_dependency):
    user = db.query(User).filter(User.id == user["id"]).first()
    if user is None:
        raise HTTPException(status_code=404, detail= "User not found.")
    all_post = db.query(PostsModel).filter(PostsModel.user_id == user.id).all()
    if not all_post:
        raise HTTPException(status_code=404, detail= "Post(s) not found.")
    return [{ "content" : post.content} 
            for post in all_post]

@router.put("/update-post", status_code=status.HTTP_200_OK)

def update_post(posts : PostsSchema , user : user_dependency, db : db_dependency):
    user = db.query(User).filter(User.id == user["id"]).first()
    if user is None:
        raise HTTPException(status_code=404, detail= "User not found.")
    existing_post = db.query(PostsModel).filter()