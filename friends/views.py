from fastapi import APIRouter, status
from starlette import status
from services.common import db_dependency, user_dependency
from services import common

router = APIRouter(
    prefix="/friends",
    tags=["Friends"]
)

@router.post("/send-request/{username}", status_code=status.HTTP_201_CREATED)

def send_request(db : db_dependency, user : user_dependency, username : str):
    return common.send_friend_request(db, user, username)

@router.post("/accept-request/{username}", status_code=status.HTTP_201_CREATED)

def accept_request(db : db_dependency, user : user_dependency, username : str):
    return common.accept_friend_request(db, user, username)

@router.post("/reject-request/{username}", status_code=status.HTTP_200_OK)

def reject_request(db : db_dependency, user : user_dependency, username : str):
    return common.reject_friend_request(db, user, username)

@router.get("/get-friends", status_code=status.HTTP_200_OK)

def get_friends(db : db_dependency, user : user_dependency):
    return common.get_all_friends(db, user)

@router.get("/pending-requests", status_code=status.HTTP_200_OK)

def pending_request(db : db_dependency, user : user_dependency):
    return common.pending_requests(db , user)

@router.delete("/delete-friend", status_code=status.HTTP_200_OK)

def delete_friend(db : db_dependency, user : user_dependency, username : str):
    return common.delete_friend(db, user, username)
