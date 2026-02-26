"""
OpenMail Platform - User Schemas
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Base schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for user profile update."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    """Schema for user response."""
    id: UUID
    role: str
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    timezone: str
    language: str
    settings: Dict[str, Any]
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserBrief(BaseModel):
    """Brief user info for listings."""
    id: UUID
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# Password schemas
class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordReset(BaseModel):
    """Schema for password reset."""
    token: str
    password: str = Field(..., min_length=8, max_length=100)


class ForgotPassword(BaseModel):
    """Schema for forgot password request."""
    email: EmailStr


# Settings schema
class UserSettings(BaseModel):
    """Schema for user settings."""
    signature: Optional[str] = None
    notifications: bool = True
    theme: str = "light"
    default_mailbox_id: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)
