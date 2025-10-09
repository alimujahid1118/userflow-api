from pydantic import BaseModel

class ProfileSchema(BaseModel):

    name : str
    bio : str