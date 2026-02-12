"""
Error handling utilities and exception classes.
Provides standardized error responses across the API.
"""
from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


class ErrorCode:
    """Standard error codes used throughout the API."""
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_INVALID = "AUTH_INVALID"
    PLAN_LIMIT_REACHED = "PLAN_LIMIT_REACHED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    COLLECTION_IN_PROGRESS = "COLLECTION_IN_PROGRESS"
    INFERENCE_FAILED = "INFERENCE_FAILED"
    APIFY_ERROR = "APIFY_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AppError(Exception):
    """
    Base application exception with standardized error shape.
    All custom exceptions should inherit from this class.
    """
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """
    Handler for AppError exceptions.
    Returns standardized error shape: {"error": {"code", "message", "details"}}
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handler for Pydantic validation errors.
    Converts FastAPI validation errors to standardized error shape.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": ErrorCode.VALIDATION_ERROR,
                "message": "Invalid request data",
                "details": {"validation_errors": exc.errors()}
            }
        }
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for unexpected exceptions.
    Logs the real error and returns details in non-production environments.
    """
    import logging
    logging.error(f"Unhandled error on {request.method} {request.url.path}: {type(exc).__name__}: {exc}")

    from app.config import settings
    error_message = "An unexpected error occurred"
    details = {}
    if settings.APP_ENV != "production":
        error_message = f"[{type(exc).__name__}] {exc}"
        details = {"type": type(exc).__name__, "message": str(exc)}

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": ErrorCode.INTERNAL_ERROR,
                "message": error_message,
                "details": details
            }
        }
    )
