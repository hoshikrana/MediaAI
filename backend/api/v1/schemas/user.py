from pydantic import BaseModel, Field, HttpUrl, model_validator
from typing import List, Optional
from datetime import datetime

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    profile_picture_url: Optional[HttpUrl] = None

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

class SessionListItem(BaseModel):
    id: str
    patient_id: Optional[str] = None
    status: str
    risk_level: Optional[str] = None
    created_at: datetime
    image_filename: str

class SessionListResponse(BaseModel):
    sessions: List[SessionListItem]
    total: int
    page: int
    limit: int
