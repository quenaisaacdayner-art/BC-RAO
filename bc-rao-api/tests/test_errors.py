"""
Tests for error handling utilities and exception classes.

Tests error codes, AppError behavior, and error response format
to ensure consistent error handling across the API.
"""
import pytest
from fastapi import status
from app.utils.errors import ErrorCode, AppError


class TestErrorCodes:
    """Test that all error codes are defined."""

    def test_auth_required_exists(self):
        """AUTH_REQUIRED error code should exist."""
        assert hasattr(ErrorCode, "AUTH_REQUIRED")
        assert ErrorCode.AUTH_REQUIRED == "AUTH_REQUIRED"

    def test_auth_invalid_exists(self):
        """AUTH_INVALID error code should exist."""
        assert hasattr(ErrorCode, "AUTH_INVALID")
        assert ErrorCode.AUTH_INVALID == "AUTH_INVALID"

    def test_plan_limit_reached_exists(self):
        """PLAN_LIMIT_REACHED error code should exist."""
        assert hasattr(ErrorCode, "PLAN_LIMIT_REACHED")
        assert ErrorCode.PLAN_LIMIT_REACHED == "PLAN_LIMIT_REACHED"

    def test_resource_not_found_exists(self):
        """RESOURCE_NOT_FOUND error code should exist."""
        assert hasattr(ErrorCode, "RESOURCE_NOT_FOUND")
        assert ErrorCode.RESOURCE_NOT_FOUND == "RESOURCE_NOT_FOUND"

    def test_duplicate_resource_exists(self):
        """DUPLICATE_RESOURCE error code should exist (BUG-A18 related)."""
        assert hasattr(ErrorCode, "DUPLICATE_RESOURCE")
        assert ErrorCode.DUPLICATE_RESOURCE == "DUPLICATE_RESOURCE"

    def test_validation_error_exists(self):
        """VALIDATION_ERROR error code should exist."""
        assert hasattr(ErrorCode, "VALIDATION_ERROR")
        assert ErrorCode.VALIDATION_ERROR == "VALIDATION_ERROR"

    def test_collection_in_progress_exists(self):
        """COLLECTION_IN_PROGRESS error code should exist."""
        assert hasattr(ErrorCode, "COLLECTION_IN_PROGRESS")
        assert ErrorCode.COLLECTION_IN_PROGRESS == "COLLECTION_IN_PROGRESS"

    def test_inference_failed_exists(self):
        """INFERENCE_FAILED error code should exist."""
        assert hasattr(ErrorCode, "INFERENCE_FAILED")
        assert ErrorCode.INFERENCE_FAILED == "INFERENCE_FAILED"

    def test_apify_error_exists(self):
        """APIFY_ERROR error code should exist."""
        assert hasattr(ErrorCode, "APIFY_ERROR")
        assert ErrorCode.APIFY_ERROR == "APIFY_ERROR"

    def test_internal_error_exists(self):
        """INTERNAL_ERROR error code should exist."""
        assert hasattr(ErrorCode, "INTERNAL_ERROR")
        assert ErrorCode.INTERNAL_ERROR == "INTERNAL_ERROR"


class TestAppErrorBasics:
    """Test AppError exception basics."""

    def test_app_error_creation(self):
        """AppError should be creatable with code and message."""
        error = AppError(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message="Campaign not found"
        )

        assert error.code == ErrorCode.RESOURCE_NOT_FOUND
        assert error.message == "Campaign not found"
        assert error.details == {}
        assert error.status_code == status.HTTP_400_BAD_REQUEST  # Default

    def test_app_error_with_details(self):
        """AppError should support details dict."""
        error = AppError(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message="Campaign not found",
            details={"campaign_id": "123"}
        )

        assert error.details == {"campaign_id": "123"}

    def test_app_error_with_custom_status(self):
        """AppError should support custom HTTP status code."""
        error = AppError(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message="Campaign not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

        assert error.status_code == 404

    def test_app_error_is_exception(self):
        """AppError should be an Exception subclass."""
        error = AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="Something went wrong"
        )

        assert isinstance(error, Exception)

    def test_app_error_can_be_raised(self):
        """AppError should be raiseable."""
        with pytest.raises(AppError) as exc_info:
            raise AppError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Invalid input"
            )

        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR
        assert exc_info.value.message == "Invalid input"


class TestAppErrorAttributes:
    """Test AppError attribute access and modification."""

    def test_error_code_accessible(self):
        """Error code should be accessible as attribute."""
        error = AppError(
            code=ErrorCode.AUTH_REQUIRED,
            message="Authentication required"
        )

        assert error.code == "AUTH_REQUIRED"

    def test_error_message_accessible(self):
        """Error message should be accessible as attribute."""
        error = AppError(
            code=ErrorCode.PLAN_LIMIT_REACHED,
            message="Budget exceeded"
        )

        assert error.message == "Budget exceeded"

    def test_error_details_accessible(self):
        """Error details should be accessible as attribute."""
        details = {"remaining": 0.0, "limit": 1.0}
        error = AppError(
            code=ErrorCode.PLAN_LIMIT_REACHED,
            message="Budget exceeded",
            details=details
        )

        assert error.details == details
        assert error.details["remaining"] == 0.0

    def test_error_status_code_accessible(self):
        """Error status code should be accessible as attribute."""
        error = AppError(
            code=ErrorCode.AUTH_INVALID,
            message="Invalid token",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

        assert error.status_code == 401


class TestCommonErrorScenarios:
    """Test common error scenarios from actual usage."""

    def test_not_found_error(self):
        """Test RESOURCE_NOT_FOUND error pattern."""
        error = AppError(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message="Campaign not found",
            details={"campaign_id": "abc123"},
            status_code=404
        )

        assert error.code == "RESOURCE_NOT_FOUND"
        assert error.status_code == 404
        assert "campaign_id" in error.details

    def test_validation_error(self):
        """Test VALIDATION_ERROR pattern."""
        error = AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Invalid subreddit name",
            details={"field": "subreddit", "value": "r/python"},
            status_code=400
        )

        assert error.code == "VALIDATION_ERROR"
        assert error.status_code == 400
        assert error.details["field"] == "subreddit"

    def test_budget_error(self):
        """Test PLAN_LIMIT_REACHED pattern."""
        error = AppError(
            code=ErrorCode.PLAN_LIMIT_REACHED,
            message="Monthly budget exceeded",
            details={"spent": 1.50, "limit": 1.00},
            status_code=402
        )

        assert error.code == "PLAN_LIMIT_REACHED"
        assert error.details["spent"] == 1.50
        assert error.details["limit"] == 1.00

    def test_duplicate_resource_error(self):
        """Test DUPLICATE_RESOURCE pattern (BUG-A18 related)."""
        error = AppError(
            code=ErrorCode.DUPLICATE_RESOURCE,
            message="Post already registered",
            details={"post_url": "https://reddit.com/r/python/comments/abc123/test/"},
            status_code=409
        )

        assert error.code == "DUPLICATE_RESOURCE"
        assert error.status_code == 409
        assert "post_url" in error.details

    def test_collection_in_progress_error(self):
        """Test COLLECTION_IN_PROGRESS pattern."""
        error = AppError(
            code=ErrorCode.COLLECTION_IN_PROGRESS,
            message="Collection already running for this campaign",
            details={"campaign_id": "camp123"},
            status_code=409
        )

        assert error.code == "COLLECTION_IN_PROGRESS"
        assert error.status_code == 409


class TestErrorDefaults:
    """Test default values for error attributes."""

    def test_default_details_empty_dict(self):
        """Details should default to empty dict if not provided."""
        error = AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="Something went wrong"
        )

        assert error.details == {}
        assert isinstance(error.details, dict)

    def test_default_status_code_400(self):
        """Status code should default to 400 if not provided."""
        error = AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Invalid input"
        )

        assert error.status_code == status.HTTP_400_BAD_REQUEST

    def test_none_details_becomes_empty_dict(self):
        """None details should be converted to empty dict."""
        error = AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="Error",
            details=None
        )

        assert error.details == {}


class TestErrorStringRepresentation:
    """Test string representation of errors."""

    def test_error_str_contains_message(self):
        """str(error) should contain the message."""
        error = AppError(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message="Campaign not found"
        )

        error_str = str(error)
        assert "Campaign not found" in error_str

    def test_error_repr_useful(self):
        """repr(error) should be useful for debugging."""
        error = AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Invalid input"
        )

        # Just verify it doesn't crash
        repr_str = repr(error)
        assert isinstance(repr_str, str)


@pytest.mark.parametrize("code,expected_value", [
    ("AUTH_REQUIRED", "AUTH_REQUIRED"),
    ("RESOURCE_NOT_FOUND", "RESOURCE_NOT_FOUND"),
    ("VALIDATION_ERROR", "VALIDATION_ERROR"),
    ("DUPLICATE_RESOURCE", "DUPLICATE_RESOURCE"),
    ("PLAN_LIMIT_REACHED", "PLAN_LIMIT_REACHED"),
])
def test_error_code_values(code, expected_value):
    """All error codes should have expected string values."""
    assert getattr(ErrorCode, code) == expected_value


@pytest.mark.parametrize("status_code", [400, 401, 402, 403, 404, 409, 422, 500])
def test_app_error_with_various_status_codes(status_code):
    """AppError should accept various HTTP status codes."""
    error = AppError(
        code=ErrorCode.INTERNAL_ERROR,
        message="Test error",
        status_code=status_code
    )

    assert error.status_code == status_code
