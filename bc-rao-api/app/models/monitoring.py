"""
Pydantic models for monitoring domain.

Models for post registration, monitoring status tracking, and dashboard stats.
"""

import re
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RegisterPostRequest(BaseModel):
    """Request to register a post for monitoring."""
    post_url: str = Field(..., min_length=1)
    campaign_id: UUID

    @field_validator('post_url')
    @classmethod
    def validate_reddit_url(cls, v: str) -> str:
        """Validate Reddit URL format."""
        pattern = r'^https?://(?:www\.)?(?:old\.)?reddit\.com/r/([a-zA-Z0-9_]{3,21})/comments/([a-z0-9]{5,9})(?:/[^/]+)?/?$'
        if not re.match(pattern, v):
            raise ValueError('Invalid Reddit URL format. Expected format: https://reddit.com/r/subreddit/comments/post_id/title')
        return v


class RegisterPostResponse(BaseModel):
    """Response after registering a post for monitoring."""
    id: UUID
    post_url: str
    subreddit: str
    reddit_post_id: str
    status: str
    isc_at_post: float
    check_interval_hours: int
    next_check_at: datetime
    created_at: datetime


class ShadowEntry(BaseModel):
    """Full shadow_table row model."""
    id: UUID
    draft_id: Optional[UUID] = None
    campaign_id: UUID
    user_id: UUID
    post_url: str
    subreddit: str
    status_vida: Literal["Ativo", "Removido", "404", "Shadowbanned", "Auditado"]
    conversational_depth: int
    isc_at_post: float
    account_status: str
    check_interval_hours: int
    total_checks: int
    last_check_status: Optional[int] = None
    last_check_at: datetime
    audit_result: Optional[Literal["SocialSuccess", "Rejection", "Inertia"]] = None
    audit_completed_at: Optional[datetime] = None
    submitted_at: datetime
    audit_due_at: datetime
    created_at: datetime


class MonitoringDashboardStats(BaseModel):
    """Dashboard statistics for monitoring overview."""
    active_count: int
    removed_count: int
    shadowbanned_count: int
    total_count: int
    success_rate: float
    recent_alerts: list[dict]


class CheckResult(BaseModel):
    """Result from a Reddit dual-check operation."""
    timestamp: datetime
    auth_status: str  # "ok" or "fail"
    anon_status: str  # "ok" or "fail"
    detected_status: str  # "active", "removed", or "shadowbanned"


class PostAuditResult(BaseModel):
    """Result from post audit classification."""
    shadow_id: UUID
    outcome: Literal["SocialSuccess", "Rejection", "Inertia"]
    audited_at: datetime


def parse_reddit_url(url: str) -> dict | None:
    """
    Parse Reddit URL and extract subreddit and post_id.

    Args:
        url: Reddit post URL

    Returns:
        Dict with 'subreddit' and 'post_id' keys, or None if invalid
    """
    pattern = r'^https?://(?:www\.)?(?:old\.)?reddit\.com/r/([a-zA-Z0-9_]{3,21})/comments/([a-z0-9]{5,9})(?:/[^/]+)?/?$'
    match = re.match(pattern, url)

    if not match:
        return None

    return {
        "subreddit": match.group(1),
        "post_id": match.group(2)
    }
