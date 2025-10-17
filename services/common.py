from typing import Annotated
from .database import Sessionlocal
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from auth.models import User
from datetime import datetime, timedelta, timezone
from friends.models import Friendship
from friends.schemas import FriendshipStatus

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

def send_friend_request(db : db_dependency, user : user_dependency, username : str):
    requested_user = db.query(User).filter(User.username == username).first()

    if requested_user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    
    requested_user_id = requested_user.id

    current_user = db.query(User).filter(User.id == user["id"]).first()
    current_user_id = current_user.id

    if current_user.username == username:
        raise HTTPException(status_code=400, detail="Cannot send request to yourself.")
    
    existing = db.query(Friendship).filter(
    ((Friendship.receiver_id == requested_user_id) & (Friendship.requester_id == current_user_id)) |
    ((Friendship.receiver_id == current_user_id) & (Friendship.requester_id == requested_user_id))
    ).first()

    if existing:
        if existing.status == FriendshipStatus.pending:
            raise HTTPException(status_code=400, detail="Friend request already sent.")
        
        elif existing.status == FriendshipStatus.accepted:
            raise HTTPException(status_code=400, detail="Your both are friends already.")
        
        elif existing.status == FriendshipStatus.rejected:
                existing.status = FriendshipStatus.pending
                db.commit()
                db.refresh(existing)
                return {"Message" : "Request sent successfully."}
    
    if existing is None:
    
        friendship_request = Friendship(
            receiver_id = requested_user_id,
            requester_id = current_user_id
        )

        db.add(friendship_request)
        db.commit()
        db.refresh(friendship_request)
        return {"Message" : "Request sent successfully."}

def accept_friend_request(db : db_dependency, user : user_dependency, username : str):
    
    requested_user = db.query(User).filter(User.username == username).first()

    if requested_user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    
    requested_user_id = requested_user.id
    
    check = db.query(Friendship).filter((Friendship.receiver_id == user["id"]) & (Friendship.requester_id == requested_user_id)).first()

    if not check:
        raise HTTPException(status_code=401, detail="Such friend request does not exist.")
    
    if check.status == FriendshipStatus.accepted:
        raise HTTPException(status_code=400, detail="You are already friends.")
    
    if  check.status == FriendshipStatus.pending:
        check.status = FriendshipStatus.accepted
        db.commit()
        db.refresh(check)
        return (f"{requested_user.username}'s request has been accepted.")
    
def reject_friend_request(db : db_dependency, user : user_dependency, username : str):
    requested_user = db.query(User).filter(User.username == username).first()
    
    if requested_user is None:
        raise HTTPException(status_code=400, detail="User not found.")
    
    requested_user_id = requested_user.id
    
    current_user = db.query(User).filter(User.id == user["id"]).first()
    current_user_id = current_user.id

    check = db.query(Friendship).filter((Friendship.receiver_id == current_user_id) & (Friendship.requester_id == requested_user_id)).first()
    if check is None:
        raise HTTPException(status_code=404, detail="Such friend request does not exist.")
    
    if check.status == FriendshipStatus.rejected:
        raise HTTPException(status_code=401, detail="Request already rejected.")
    
    if check.status == FriendshipStatus.accepted:
        raise HTTPException(status_code=401, detail="Request already accepted.")
    
    if check.status == FriendshipStatus.pending:
        check.status = FriendshipStatus.rejected
        db.commit()
        db.refresh(check)

        return {"Message" : "Request Rejected successfully."}
    
def get_all_friends(db : db_dependency, user : user_dependency):
    current_user_id = user["id"]
    all_friends = db.query(Friendship).filter(((Friendship.receiver_id == current_user_id) | (Friendship.requester_id == current_user_id)) & (Friendship.status == FriendshipStatus.accepted)).all()
    if not all_friends:
        return {"Message" : "You have no friends"}
    all_friends_id = []

    for friends in all_friends:
        if friends.receiver_id == current_user_id:
            all_friends_id.append(friends.requester_id)
        else:
            all_friends_id.append(friends.receiver_id)

    all_users = db.query(User).filter(User.id.in_(all_friends_id)).all()
    usernames = [f.username for f in all_users]
    return {"Friends" : usernames}

def pending_requests(db: db_dependency, user: user_dependency):
    current_user_id = user["id"]

    # Incoming requests (received by current user)
    pending_requests = db.query(Friendship).filter(
        (Friendship.receiver_id == current_user_id) &
        (Friendship.status == FriendshipStatus.pending)
    ).all()

    pending_request_ids = [req.requester_id for req in pending_requests]

    pending_request_users = db.query(User).filter(User.id.in_(pending_request_ids)).all()
    pending_request_usernames = [u.username for u in pending_request_users]

    # Outgoing requests (sent by current user)
    sent_requests = db.query(Friendship).filter(
        (Friendship.requester_id == current_user_id) &
        (Friendship.status == FriendshipStatus.pending)
    ).all()

    sent_request_ids = [req.receiver_id for req in sent_requests]

    sent_request_users = db.query(User).filter(User.id.in_(sent_request_ids)).all()
    sent_request_usernames = [u.username for u in sent_request_users]

    # Return a proper response
    return {
        "Pending requests (received)": pending_request_usernames or ["None"],
        "Pending requests (sent)": sent_request_usernames or ["None"]
    }

def delete_friend(db : db_dependency, user : user_dependency, username : str):
    current_user_id = user["id"]

    requested_user = db.query(User).filter(User.username == username).first()
    requested_user_id = requested_user.id

    check = db.query(Friendship).filter((((Friendship.requester_id == requested_user_id) & (Friendship.receiver_id == current_user_id)) | ((Friendship.requester_id == current_user_id) & (Friendship.receiver_id == requested_user_id))) & (Friendship.status == FriendshipStatus.accepted)).first()
    if not check:
        raise HTTPException(status_code=400, detail="No such friend found.")
    
    if check:
        db.delete(check)
        db.commit()

        return {"Message" : "Friend has been deleted from friends list."}