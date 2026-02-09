"""
FastAPI dependencies for authentication and authorization.
Used across protected endpoints via Depends().
"""
from typing import Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.security import verify_jwt
from app.utils.errors import AppError, ErrorCode


# HTTPBearer scheme for JWT tokens in Authorization header
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency to extract and validate current user from JWT token.

    Usage:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            user_id = user["sub"]
            ...

    Args:
        credentials: HTTP Authorization credentials with Bearer token

    Returns:
        Decoded JWT payload containing user information (includes "sub" as user_id)

    Raises:
        HTTPException: 401 if token is missing or invalid
    """
    try:
        token = credentials.credentials
        payload = verify_jwt(token)
        return payload
    except AppError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details
            }
        )
