from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from typing import List, Optional
from datetime import datetime


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    profile_picture_url: Optional[HttpUrl] = None


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    profile_picture_url: Optional[str] = None

    model_config = {"from_attributes": True}


class CreateAPIKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    permissions: List[str]
    rate_limit_per_hour: int = Field(default=100, ge=1, le=1000)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyCreatedResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    plain_key: str
    permissions: List[str]
    created_at: datetime


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    permissions: List[str]
    rate_limit_per_hour: int
    is_active: bool
    last_used_at: Optional[datetime] = None
    usage_count: int
    created_at: datetime
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SessionSummary(BaseModel):
    id: str
    patient_id: Optional[str] = None
    status: str
    risk_level: Optional[str] = None
    created_at: datetime


class SessionListResponse(BaseModel):
    sessions: List[SessionSummary]
    total: int
