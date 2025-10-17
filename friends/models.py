from sqlalchemy import Column, Enum, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from services.database import Base
from auth.models import User
import enum

class FriendshipStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

class Friendship(Base):
    __tablename__ = "friendship"

    id = Column(Integer, primary_key=True)
    receiver_id = Column(Integer, ForeignKey('user.id', ondelete="Cascade"), nullable=False)
    requester_id = Column(Integer, ForeignKey('user.id', ondelete="Cascade"), nullable=False)
    status = Column(Enum(FriendshipStatus), default= FriendshipStatus.pending, nullable= False)

    receiver = relationship("User", foreign_keys=[receiver_id])
    requester = relationship("User", foreign_keys=[requester_id])

    __table_args__ = (
        UniqueConstraint(receiver_id, requester_id, name="unique_friend_request"),
    )