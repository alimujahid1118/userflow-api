from fastapi import HTTPException, APIRouter
from .schemas import ProfileSchema
from .models import Profile as ProfileModel
from starlette import status
from services.common import user_dependency, db_dependency

router = APIRouter(
    prefix="/auth",
    tags=["profile"]
)

#Create a new Profile
@router.post("/create-profile", status_code=status.HTTP_201_CREATED)

def create_profile(profile : ProfileSchema, user : user_dependency, db : db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail= "Unauthorized request.")
    existing_profile = db.query(ProfileModel).filter(ProfileModel.user_id == user["id"]).first()
    if existing_profile:
        raise HTTPException(status_code=404, detail="Profile already created!")
    if existing_profile is None:
        new_profile = ProfileModel(
            name = profile.name,
            bio = profile.bio,
            user_id = user["id"]
        )
        db.add(new_profile)
        db.commit()
        return {"Message" : "Profile has been created successfully."}

#Get Profile
@router.get("/get-profile", status_code=status.HTTP_200_OK)

def get_profile(user : user_dependency, db : db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail= "Unauthorized request.")
    profile = db.query(ProfileModel).filter(ProfileModel.user_id == user["id"]).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="Unable to fetch Profile.")
    return profile

#Update Profile
@router.put("/update-profile", status_code=status.HTTP_201_CREATED)

def update_profile(profile : ProfileSchema, user : user_dependency, db : db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail= "Unauthorized request.")
    existing_profile= db.query(ProfileModel).filter(ProfileModel.user_id == user["id"]).first()
    if existing_profile is None:
        raise HTTPException(status_code=404 , detail= "Unable to find a Profile")
    
    existing_profile.name = profile.name
    existing_profile.bio = profile.bio

    db.commit()
    db.refresh(existing_profile)
    return {"Message" : "Profile has been updated successfully."}

#Delete Profile
@router.delete("/delete-profile", status_code=status.HTTP_200_OK)

def delete_profile(user : user_dependency, db : db_dependency):
    profile = db.query(ProfileModel).filter(ProfileModel.user_id == user["id"]).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile doesn't exist")
    db.delete(profile)
    db.commit()
    return {"Message" : "Profile has been deleted successfully."}