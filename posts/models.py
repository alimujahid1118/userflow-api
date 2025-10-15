from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from services.database import Base

class Posts(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key= True)
    content = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))
    profile_id = Column(Integer, ForeignKey('profile.id'))
    profile = relationship("Profile", back_populates= "posts")