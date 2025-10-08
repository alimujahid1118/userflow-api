from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, registry, relationship

engine = create_engine(
    "postgresql+psycopg2://postgres:root@localhost:5432/test", echo= True
)

Sessionlocal = sessionmaker(autocommit= False, autoflush= False, bind= engine)

mapper_registry = registry()

Base = mapper_registry.generate_base()

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key= True)
    username = Column(String, unique= True)
    hashed_password = Column(String)
    profile = relationship("Profile")

class Profile(Base):
    __tablename__ = "profile"

    id = Column(Integer, primary_key= True)
    name = Column(String)
    bio = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship("User", uselist= False)
    posts = relationship("Posts", back_populates= "profile")

class Posts(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key= True)
    content = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))
    profile_id = Column(Integer, ForeignKey('profile.id'))
    profile = relationship("Profile", back_populates= "posts")

Base.metadata.create_all(engine)