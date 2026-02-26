"""
OpenMail Platform - Authentication Endpoints
"""
from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_verification_token
)
from app.db.database import get_db
from app.models.user import User, Session, VerificationToken
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    VerifyEmailRequest,
    MessageResponse
)
from app.schemas.user import UserCreate, UserResponse, ForgotPassword, PasswordReset

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Get user from database
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user account."""
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email.lower())
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        email=user_data.email.lower(),
        password_hash=hash_password(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        is_verified=False,
        is_active=True
    )
    db.add(user)
    await db.flush()
    
    # Create verification token
    token = VerificationToken(
        user_id=user.id,
        token=generate_verification_token(),
        token_type="email_verify",
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(token)
    
    await db.commit()
    
    # TODO: Send verification email
    
    return MessageResponse(
        message="Registration successful. Please check your email to verify your account.",
        success=True
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return tokens."""
    # Find user
    result = await db.execute(
        select(User).where(User.email == form_data.username.lower())
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        # Track failed login attempts
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=settings.LOCKOUT_DURATION_MINUTES
                )
            await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if account is locked
    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is temporarily locked. Please try again later."
        )
    
    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Reset failed login attempts on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.utcnow()
    
    # Create tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Store session
    session = Session(
        user_id=user.id,
        token_hash=hash_password(access_token[-32:]),  # Hash last 32 chars
        refresh_token_hash=hash_password(refresh_token[-32:]),
        device_info=request.headers.get("User-Agent", "Unknown")[:500],
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
        expires_at=datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        refresh_expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(session)
    await db.commit()
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token."""
    payload = decode_token(request.refresh_token)
    
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value
    }
    access_token = create_access_token(token_data)
    
    return RefreshResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Logout current user (invalidate session)."""
    # In a real implementation, you'd invalidate the specific session
    # For now, we just return success
    return MessageResponse(
        message="Successfully logged out",
        success=True
    )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    request: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db)
):
    """Verify email address using token."""
    result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.token == request.token,
            VerificationToken.token_type == "email_verify"
        )
    )
    token = result.scalar_one_or_none()
    
    if not token or not token.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Mark token as used
    token.used_at = datetime.utcnow()
    
    # Verify user
    result = await db.execute(
        select(User).where(User.id == token.user_id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        user.is_verified = True
    
    await db.commit()
    
    return MessageResponse(
        message="Email verified successfully",
        success=True
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPassword,
    db: AsyncSession = Depends(get_db)
):
    """Request password reset email."""
    result = await db.execute(
        select(User).where(User.email == request.email.lower())
    )
    user = result.scalar_one_or_none()
    
    if user:
        # Create reset token
        token = VerificationToken(
            user_id=user.id,
            token=generate_verification_token(),
            token_type="password_reset",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.add(token)
        await db.commit()
        
        # TODO: Send reset email
    
    # Always return success to prevent email enumeration
    return MessageResponse(
        message="If an account exists with that email, a password reset link has been sent.",
        success=True
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: PasswordReset,
    db: AsyncSession = Depends(get_db)
):
    """Reset password using token."""
    result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.token == request.token,
            VerificationToken.token_type == "password_reset"
        )
    )
    token = result.scalar_one_or_none()
    
    if not token or not token.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Mark token as used
    token.used_at = datetime.utcnow()
    
    # Update user password
    result = await db.execute(
        select(User).where(User.id == token.user_id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        user.password_hash = hash_password(request.password)
        user.failed_login_attempts = 0
        user.locked_until = None
    
    await db.commit()
    
    return MessageResponse(
        message="Password reset successfully",
        success=True
    )
