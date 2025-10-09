from pydantic import BaseModel

class PostsSchema(BaseModel):

    content : str