"""
Security utilities for JWT verification and authentication.
Supports both HS256 (legacy) and ES256 (new Supabase signing keys).
"""
from typing import Dict, Any, Optional, List
import httpx
from jose import jwt, JWTError
from app.config import settings
from app.utils.errors import AppError, ErrorCode

# Cache JWKS keys to avoid fetching on every request
_jwks_cache: Optional[List[Dict]] = None


def _get_jwks_keys() -> List[Dict]:
    """Fetch and cache JWKS public keys from Supabase."""
    global _jwks_cache
    if _jwks_cache is None:
        url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks"
        response = httpx.get(url, headers={"apikey": settings.SUPABASE_ANON_KEY}, timeout=10)
        response.raise_for_status()
        _jwks_cache = response.json().get("keys", [])
    return _jwks_cache


def _find_jwk_key(kid: str) -> Optional[Dict]:
    """Find a JWK key by key ID."""
    keys = _get_jwks_keys()
    for key in keys:
        if key.get("kid") == kid:
            return key
    return None


def verify_jwt(token: str) -> Dict[str, Any]:
    """
    Verify and decode a Supabase JWT token.
    Automatically detects HS256 (legacy) vs ES256 (new) signing.

    Args:
        token: JWT token string from Authorization header

    Returns:
        Decoded token payload containing user information

    Raises:
        AppError: If token is invalid or expired
    """
    try:
        # Read token header to determine algorithm
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")
        kid = header.get("kid")

        if alg == "HS256":
            # Legacy: verify with shared secret
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
        else:
            # ES256/RS256: verify with JWKS public key
            if not kid:
                raise JWTError("Token missing 'kid' header for asymmetric verification")

            jwk_key = _find_jwk_key(kid)
            if not jwk_key:
                # Clear cache and retry (key might have rotated)
                global _jwks_cache
                _jwks_cache = None
                jwk_key = _find_jwk_key(kid)

            if not jwk_key:
                raise JWTError(f"No matching JWK key found for kid: {kid}")

            payload = jwt.decode(
                token,
                jwk_key,
                algorithms=[alg],
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
