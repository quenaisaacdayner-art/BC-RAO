"""
Authentication endpoints for signup, login, token refresh, and user profile.
Integrates with Supabase Auth for secure user management.
"""
from fastapi import APIRouter, Depends, status
from app.models.auth import (
    SignupRequest,
    LoginRequest,
    RefreshRequest,
    AuthResponse,
    LoginResponse,
    UserProfile
)
from app.services.auth_service import AuthService
from app.dependencies import get_current_user


router = APIRouter()


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest):
    """
    Register a new user account.

    Creates user in Supabase Auth and triggers DB function to create:
    - User profile in profiles table
    - Trial subscription in subscriptions table

    Args:
        request: Signup credentials (email, password, full_name)

    Returns:
        AuthResponse with user_id and JWT tokens

    Raises:
        AppError: If email already exists or signup fails
    """
    auth_service = AuthService()
    user_id, access_token, refresh_token = auth_service.signup(
        email=request.email,
        password=request.password,
        full_name=request.full_name
    )

    return AuthResponse(
        user_id=user_id,
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user with email and password.

    Args:
        request: Login credentials (email, password)

    Returns:
        LoginResponse with JWT tokens and user info

    Raises:
        AppError: If credentials are invalid
    """
    auth_service = AuthService()
    access_token, refresh_token, user = auth_service.login(
        email=request.email,
        password=request.password
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh(request: RefreshRequest):
    """
    Refresh access token using refresh token.

    Args:
        request: Refresh token

    Returns:
        AuthResponse with new token pair

    Raises:
        AppError: If refresh token is invalid or expired
    """
    auth_service = AuthService()
    access_token, refresh_token = auth_service.refresh(
        refresh_token=request.refresh_token
    )

    # Extract user_id from new access token
    from app.utils.security import verify_jwt
    payload = verify_jwt(access_token)
    user_id = payload.get("sub")

    return AuthResponse(
        user_id=user_id,
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current user's profile and subscription information.

    Requires valid JWT token in Authorization header.

    Args:
        current_user: Decoded JWT payload from get_current_user dependency

    Returns:
        UserProfile with plan and trial info

    Raises:
        AppError: If user not found or unauthorized
    """
    auth_service = AuthService()
    user_id = current_user.get("sub")
    profile = auth_service.get_me(user_id=user_id)

    return UserProfile(**profile)
