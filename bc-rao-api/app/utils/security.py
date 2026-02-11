"""
Security utilities for JWT verification and authentication.
Uses Supabase Auth API for reliable token verification.
"""
from typing import Dict, Any
import httpx
from app.config import settings
from app.utils.errors import AppError, ErrorCode


def verify_jwt(token: str) -> Dict[str, Any]:
    """
    Verify a Supabase JWT token by calling Supabase Auth API.

    Instead of local JWT decoding (which requires matching the signing
    algorithm and keys), this delegates verification to Supabase itself
    via the /auth/v1/user endpoint — the same approach the JS SDK uses.

    Args:
        token: JWT token string from Authorization header

    Returns:
        Dict with at least {"sub": user_id} matching JWT payload format

    Raises:
        AppError: If token is invalid or expired
    """
    try:
        url = f"{settings.SUPABASE_URL}/auth/v1/user"
        response = httpx.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": settings.SUPABASE_ANON_KEY,
            },
            timeout=10,
        )

        if response.status_code == 401:
            raise AppError(
                code=ErrorCode.AUTH_INVALID,
                message="Invalid or expired authentication token",
                details={"status": 401},
                status_code=401,
            )

        if response.status_code != 200:
            raise AppError(
                code=ErrorCode.AUTH_INVALID,
                message="Authentication verification failed",
                details={"status": response.status_code, "body": response.text[:200]},
                status_code=401,
            )

        user_data = response.json()
        user_id = user_data.get("id", "")

        # Return payload matching JWT claims format (sub = user id)
        return {
            "sub": user_id,
            "email": user_data.get("email", ""),
            "role": user_data.get("role", "authenticated"),
        }

    except AppError:
        raise
    except Exception as e:
        raise AppError(
            code=ErrorCode.AUTH_INVALID,
            message="Authentication verification failed",
            details={"error": str(e), "type": type(e).__name__},
            status_code=401,
        )
