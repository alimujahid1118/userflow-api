from pydantic import BaseModel
from enum import Enum

class FriendshipStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

class FriendBase(BaseModel):

    receiver_id : int

class FriendshipResponse(BaseModel):

    id : int
    receiver_id : int
    requester_id : int
    status : FriendshipStatus

    class config:
        orm_mode = True

class FriendResponse(BaseModel):

    id: int
    username : str

    class config:
        from_attributes = True