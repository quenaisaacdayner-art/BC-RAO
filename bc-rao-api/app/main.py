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


@app.get("/debug/test-collect/{campaign_id}")
async def debug_collect(campaign_id: str, authorization: str = ""):
    """Temporary: test collect flow step by step. Pass ?authorization=Bearer+xxx"""
    steps = {}

    # Step 1: JWT
    from app.utils.security import verify_jwt
    if not authorization.startswith("Bearer "):
        return {"error": "Pass ?authorization=Bearer+YOUR_TOKEN"}
    token = authorization[7:]
    try:
        payload = verify_jwt(token)
        user_id = payload.get("sub")
        steps["jwt"] = {"ok": True, "user_id": user_id}
    except Exception as e:
        return {"steps": steps, "failed_at": "jwt", "error": str(e), "type": type(e).__name__}

    # Step 2: Supabase client
    try:
        from app.integrations.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        steps["supabase_client"] = {"ok": True}
    except Exception as e:
        return {"steps": steps, "failed_at": "supabase_client", "error": str(e), "type": type(e).__name__}

    # Step 3: Campaign query
    try:
        response = supabase.table("campaigns").select("id, user_id").eq("id", campaign_id).eq("user_id", user_id).execute()
        campaign = response.data[0] if response.data else None
        steps["campaign_query"] = {"ok": True, "found": bool(campaign), "data": campaign}
    except Exception as e:
        return {"steps": steps, "failed_at": "campaign_query", "error": str(e), "type": type(e).__name__}

    # Step 4: Profile query (plan column doesn't exist yet — Phase 6)
    steps["profile_query"] = {"ok": True, "note": "skipped — plan defaults to trial until Phase 6"}

    # Step 5: Redis
    try:
        from app.workers.task_runner import get_redis, generate_task_id
        r = get_redis()
        r.ping()
        task_id = generate_task_id()
        steps["redis"] = {"ok": True, "task_id": task_id}
    except Exception as e:
        return {"steps": steps, "failed_at": "redis", "error": str(e), "type": type(e).__name__}

    return {"steps": steps, "all_ok": True}
