"""
Common Pydantic models used across the API.
Primarily for standardized error responses in OpenAPI documentation.
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """
    Standardized error detail structure.
    Used in error responses across all endpoints.
    """
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context-specific details"
    )


class ErrorResponse(BaseModel):
    """
    Standardized error response wrapper.
    All error responses follow this shape.
    """
    error: ErrorDetail = Field(..., description="Error information")
