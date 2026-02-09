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
