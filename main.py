from fastapi import FastAPI
from auth.views import router as auth_router
from profile.views import router as profile_router
from posts.views import router as posts_router
from services.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(posts_router)