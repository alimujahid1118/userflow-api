from fastapi import HTTPException, APIRouter
from .schemas import PostsSchema
from .models import Posts as PostsModel
from profile.models import Profile as ProfileModel
from auth.models import User
from starlette import status
from services.common import user_dependency, db_dependency

router = APIRouter(
    prefix="/auth",
    tags=["posts"]
)

@router.post("/create-post", status_code=status.HTTP_201_CREATED)

def create_post(user : user_dependency, posts : PostsSchema, db : db_dependency):
    user = db.query(User).filter(User.id == user["id"]).first()
    if user is None:
        raise HTTPException(status_code=404, detail= "User not found.")
    profile = db.query(ProfileModel.id).filter(ProfileModel.user_id == user.id).first()
    if profile is None:
        raise HTTPException(status_code=404, detail= "Profile not found.")
    if profile:
        new_post = PostsModel(
            content = posts.content,
            user_id = user.id,
            profile_id = profile.id
        )
        db.add(new_post)
        db.commit()
        return {"Message" : "Post has been created successfully."}

@router.get("/get-all-posts", status_code=200)
def get_all_posts(db: db_dependency):
    all_posts = db.query(PostsModel).all()
    if not all_posts:
        raise HTTPException(status_code=404, detail="No posts found.")
    return [{"content": post.content} for post in all_posts]

@router.get("/get-post/{post_id}", status_code= status.HTTP_200_OK)

def get_post(post_id : int , user : user_dependency, db : db_dependency):
    user = db.query(User).filter(User.id == user["id"]).first()
    if user is None:
        raise HTTPException(status_code=404, detail= "User not found.")
    if post_id is None:
        raise HTTPException(status_code=401, detail="Post is either unauthorized or Not available")
    post = db.query(PostsModel).filter(PostsModel.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail= "Post(s) not found.")
    if post.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this post.")
    if post:
        return {"content" : post}

@router.put("/update-post/{post_id}", status_code=status.HTTP_200_OK)

def update_post(post_id : int, posts : PostsSchema , user : user_dependency, db : db_dependency):
    user = db.query(User).filter(User.id == user["id"]).first()
    if user is None:
        raise HTTPException(status_code=404, detail= "User not found.")
    existing_post = db.query(PostsModel).filter(PostsModel.id == post_id).first()
    if existing_post is None:
        raise HTTPException(status_code=404, detail= "Unable to fetch post.")
    elif existing_post.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to update this post.")
    elif existing_post.user_id == user.id:
        existing_post.content = posts.content
        db.commit()
        db.refresh(existing_post)
        return {"Message" : "Post has been updated successfully."}

@router.delete("/delete-post/{post_id}", status_code=status.HTTP_200_OK)

def delete_post(post_id : int, user : user_dependency, db : db_dependency):
    user = db.query(User).filter(User.id == user["id"]).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized request.")
    existing_post = db.query(PostsModel).filter(PostsModel.id == post_id).first()
    if existing_post is None:
        raise HTTPException(status_code=404, detail="Unable to fetch post.")
    elif existing_post.user_id != user.id:
        raise HTTPException(status_code=401, detail="Unauthorized request.")
    db.delete(existing_post)
    db.commit()
    return {"Message" : "Post has been deleted successfully."}