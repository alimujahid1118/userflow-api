from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from services.database import Base

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from services.database import Base  # or wherever your SQLAlchemy Base is defined

class Message(Base):
    __tablename__ = "messages"  # ✅ This must match the error’s table name

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    delivered = Column(Boolean, default=False)

    sender = relationship("User", foreign_keys=[sender_id])
    recipient = relationship("User", foreign_keys=[recipient_id])