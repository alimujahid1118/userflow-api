from fastapi import FastAPI
from auth.views import router as auth_router
from profile.views import router as profile_router
from posts.views import router as posts_router
from services.database import Base, engine
from chat.views import router as chat_router
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(posts_router)
app.include_router(chat_router)
