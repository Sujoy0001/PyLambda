from pydantic import BaseModel, Field, EmailStr


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    useremail: EmailStr = Field(..., max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginCredentials(BaseModel):
    useremail: EmailStr = Field(..., max_length=255)
    password: str = Field(min_length=8, max_length=128)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    useremail: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=32, max_length=256)
    new_password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    username: str
    useremail: EmailStr


class PhoneVerificationRequest(BaseModel):
    phone_number: int = Field(...)