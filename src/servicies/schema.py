from dataclasses import Field

from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class UserProfileModel(BaseModel):
    user_id: int  # Telegram user_id (BIGINT)
    gender: str  # 'male', 'female', 'other'
    name: str
    age: int  # CHECK (age > 0 AND age < 150)
    about: Optional[str] = None
    meta: Optional[dict] = None  # JSONB

    class Config:
        from_attributes = True

class UserProfileCreate(BaseModel):
    user_id: int
    gender: str
    name: str
    age: int
    about: Optional[str] = None
    meta: Optional[Dict] = None

    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    gender: Optional[str] = None
    name: Optional[str] = None
    age: Optional[int] = None
    about: Optional[str] = None
    meta: Optional[Dict] = None

    class Config:
        from_attributes = True

class UserProfileResponse(BaseModel):
    user_id: int
    gender: str
    name: str
    age: int
    about: Optional[str] = None
    meta: Optional[Dict] = None

    class Config:
        from_attributes = True