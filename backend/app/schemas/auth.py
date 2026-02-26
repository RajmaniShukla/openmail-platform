"""
OpenMail Platform - Authentication Schemas
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """Schema for login request."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Schema for login response."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserResponse


class RefreshRequest(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str


class RefreshResponse(BaseModel):
    """Schema for token refresh response."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""
    sub: UUID
    email: str
    role: str
    exp: datetime
    iat: datetime
    jti: str


class VerifyEmailRequest(BaseModel):
    """Schema for email verification."""
    token: str


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    success: bool = True
