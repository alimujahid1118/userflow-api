from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from services.database import Base

class Profile(Base):
    __tablename__ = "profile"

    id = Column(Integer, primary_key= True)
    name = Column(String)
    bio = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship("User", uselist= False)
    posts = relationship("Posts", back_populates= "profile")