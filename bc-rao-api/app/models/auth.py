"""
Authentication request/response models.
Used for signup, login, token refresh, and user profile endpoints.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    """Request body for user signup."""
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str


class LoginRequest(BaseModel):
    """Request body for user login."""
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Request body for token refresh."""
    refresh_token: str


class AuthResponse(BaseModel):
    """Response for signup and refresh endpoints."""
    user_id: str
    access_token: str
    refresh_token: str


class LoginResponse(BaseModel):
    """Response for login endpoint with user info."""
    access_token: str
    refresh_token: str
    user: dict


class UserProfile(BaseModel):
    """User profile with subscription info."""
    id: str
    full_name: Optional[str] = None
    email: str
    plan: str
    trial_ends_at: Optional[str] = None
    onboarding_completed: bool
