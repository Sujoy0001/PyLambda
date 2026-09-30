from pydantic import BaseModel


class Auth0User(BaseModel):
    username: str
    email: str
    password: str 
    isAdmin: bool
    active: bool
    verified: bool
