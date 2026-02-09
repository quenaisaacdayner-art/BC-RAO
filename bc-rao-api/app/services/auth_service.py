"""
Authentication service for handling Supabase Auth operations.
Manages signup, login, token refresh, and user profile retrieval.
"""
from typing import Tuple, Dict, Any
from supabase import Client
from app.integrations.supabase_client import get_supabase_client
from app.utils.errors import AppError, ErrorCode


class AuthService:
    """Service for authentication operations using Supabase Auth."""

    def __init__(self, supabase: Client = None):
        """
        Initialize auth service with Supabase client.

        Args:
            supabase: Optional Supabase client instance (for testing)
        """
        self.supabase = supabase or get_supabase_client()

    def signup(self, email: str, password: str, full_name: str) -> Tuple[str, str, str]:
        """
        Register a new user with Supabase Auth.
        The DB trigger automatically creates profile and trial subscription.

        Args:
            email: User's email address
            password: User's password (min 6 characters)
            full_name: User's full name (stored in user metadata)

        Returns:
            Tuple of (user_id, access_token, refresh_token)

        Raises:
            AppError: If signup fails (e.g., email already exists)
        """
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name
                    }
                }
            })

            if not response.user:
                raise AppError(
                    code=ErrorCode.AUTH_INVALID,
                    message="Failed to create user account",
                    status_code=400
                )

            return (
                response.user.id,
                response.session.access_token,
                response.session.refresh_token
            )
        except Exception as e:
            # Handle Supabase-specific errors
            error_message = str(e)
            if "already registered" in error_message.lower() or "duplicate" in error_message.lower():
                raise AppError(
                    code=ErrorCode.AUTH_INVALID,
                    message="Email address is already registered",
                    details={"email": email},
                    status_code=400
                )
            raise AppError(
                code=ErrorCode.AUTH_INVALID,
                message="Signup failed",
                details={"error": error_message},
                status_code=400
            )

    def login(self, email: str, password: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Authenticate user with email and password.

        Args:
            email: User's email address
            password: User's password

        Returns:
            Tuple of (access_token, refresh_token, user_info)

        Raises:
            AppError: If login fails (invalid credentials)
        """
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if not response.user or not response.session:
                raise AppError(
                    code=ErrorCode.AUTH_INVALID,
                    message="Invalid email or password",
                    status_code=401
                )

            user_info = {
                "id": response.user.id,
                "email": response.user.email,
                "full_name": response.user.user_metadata.get("full_name")
            }

            return (
                response.session.access_token,
                response.session.refresh_token,
                user_info
            )
        except AppError:
            raise
        except Exception as e:
            raise AppError(
                code=ErrorCode.AUTH_INVALID,
                message="Invalid email or password",
                status_code=401
            )

    def refresh(self, refresh_token: str) -> Tuple[str, str]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Tuple of (new_access_token, new_refresh_token)

        Raises:
            AppError: If refresh fails (invalid or expired token)
        """
        try:
            response = self.supabase.auth.refresh_session(refresh_token)

            if not response.session:
                raise AppError(
                    code=ErrorCode.AUTH_INVALID,
                    message="Invalid or expired refresh token",
                    status_code=401
                )

            return (
                response.session.access_token,
                response.session.refresh_token
            )
        except AppError:
            raise
        except Exception as e:
            raise AppError(
                code=ErrorCode.AUTH_INVALID,
                message="Token refresh failed",
                details={"error": str(e)},
                status_code=401
            )

    def get_me(self, user_id: str) -> Dict[str, Any]:
        """
        Get current user's profile with subscription information.

        Args:
            user_id: User's UUID from JWT token

        Returns:
            User profile dictionary with plan and trial info

        Raises:
            AppError: If profile not found or query fails
        """
        try:
            # Query user profile
            profile_response = self.supabase.table("profiles").select("*").eq("id", user_id).single().execute()

            if not profile_response.data:
                raise AppError(
                    code=ErrorCode.RESOURCE_NOT_FOUND,
                    message="User profile not found",
                    status_code=404
                )

            profile = profile_response.data

            # Query active subscription
            subscription_response = self.supabase.table("subscriptions").select("*").eq("user_id", user_id).eq("status", "active").single().execute()

            subscription = subscription_response.data if subscription_response.data else None

            return {
                "id": profile["id"],
                "full_name": profile.get("full_name"),
                "email": profile["email"],
                "plan": subscription["plan"] if subscription else "trial",
                "trial_ends_at": subscription.get("trial_ends_at") if subscription else None,
                "onboarding_completed": profile.get("onboarding_completed", False)
            }
        except AppError:
            raise
        except Exception as e:
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="Failed to retrieve user profile",
                details={"error": str(e)},
                status_code=500
            )
