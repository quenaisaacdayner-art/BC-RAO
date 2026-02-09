"""
Security utilities for JWT verification and authentication.
Extracted for testability and reusability.
"""
from typing import Dict, Any
from jose import jwt, JWTError
from app.config import settings
from app.utils.errors import AppError, ErrorCode


def verify_jwt(token: str) -> Dict[str, Any]:
    """
    Verify and decode a Supabase JWT token.

    Args:
        token: JWT token string from Authorization header

    Returns:
        Decoded token payload containing user information

    Raises:
        AppError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
        return payload
    except JWTError as e:
        raise AppError(
            code=ErrorCode.AUTH_INVALID,
            message="Invalid or expired authentication token",
            details={"error": str(e)},
            status_code=401
        )
