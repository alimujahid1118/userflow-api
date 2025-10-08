from pydantic import BaseModel

class CreateUserRequest(BaseModel):

    username : str
    password : str

class Token(BaseModel):

    access_token : str
    token_type : str

class ProfileSchema(BaseModel):

    name : str
    bio : str

class PostsSchema(BaseModel):

    content : str