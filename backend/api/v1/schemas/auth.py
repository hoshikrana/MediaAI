from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional
from datetime import datetime

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=100)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)

class GoogleCallbackRequest(BaseModel):
    code: str
    state: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    profile_picture_url: Optional[str] = None
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class AuthResponse(BaseModel):
    token: TokenResponse
    user: UserResponse

class MessageResponse(BaseModel):
    message: str
