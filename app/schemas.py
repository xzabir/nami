from datetime import datetime
from typing import Optional, Dict

from pydantic import BaseModel, EmailStr, Field


# --- Auth ---

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Captioning ---

STYLES = ["formal", "sarcastic", "humorous_tech", "humorous_non_tech"]


class CaptionRequest(BaseModel):
    video_url: str


class CaptionsOut(BaseModel):
    formal: str
    sarcastic: str
    humorous_tech: str
    humorous_non_tech: str


class JobOut(BaseModel):
    id: str
    video_url: str
    status: str
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    captions: Optional[Dict[str, str]] = None

    class Config:
        from_attributes = True
