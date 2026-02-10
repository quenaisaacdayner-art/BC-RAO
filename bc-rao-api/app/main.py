"""
BC-RAO FastAPI Application Entry Point.
Configures middleware, error handlers, and routes.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.api.v1.router import router as v1_router
from app.utils.errors import (
    AppError,
    app_error_handler,
    validation_error_handler,
    generic_error_handler
)


# Create FastAPI application
app = FastAPI(
    title="BC-RAO API",
    version="1.0.0",
    description="Social intelligence platform for Reddit marketing",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

# Include v1 API router
app.include_router(v1_router, prefix="/v1")


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns 200 OK if service is running.
    """
    return {"status": "healthy"}


@app.get("/debug/config")
async def debug_config():
    """Temporary diagnostic endpoint. Remove after debugging."""
    return {
        "supabase_url_set": bool(settings.SUPABASE_URL),
        "supabase_url_prefix": settings.SUPABASE_URL[:20] + "..." if settings.SUPABASE_URL else "",
        "jwt_secret_set": bool(settings.SUPABASE_JWT_SECRET),
        "jwt_secret_length": len(settings.SUPABASE_JWT_SECRET),
        "anon_key_set": bool(settings.SUPABASE_ANON_KEY),
        "service_role_key_set": bool(settings.SUPABASE_SERVICE_ROLE_KEY),
        "redis_url_set": bool(settings.REDIS_URL),
        "cors_origins": settings.CORS_ORIGINS,
        "app_env": settings.APP_ENV,
    }


@app.get("/debug/test-jwt")
async def debug_jwt(authorization: str = ""):
    """Temporary: test JWT validation. Pass ?authorization=Bearer+xxx"""
    from app.utils.security import verify_jwt
    if not authorization.startswith("Bearer "):
        return {"error": "Pass ?authorization=Bearer+YOUR_TOKEN"}
    token = authorization[7:]
    try:
        payload = verify_jwt(token)
        return {"success": True, "sub": payload.get("sub"), "exp": payload.get("exp")}
    except Exception as e:
        return {"success": False, "error": str(e), "type": type(e).__name__}
