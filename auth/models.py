from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from services.database import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key= True)
    username = Column(String, unique= True)
    hashed_password = Column(String)
    profile = relationship("Profile")