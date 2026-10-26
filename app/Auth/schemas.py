from pydantic import BaseModel, Field, EmailStr


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    useremail: EmailStr = Field(..., max_length=255)
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    username: str
    useremail: EmailStr
