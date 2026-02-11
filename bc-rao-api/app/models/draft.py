"""
Pydantic models for draft generation requests and responses.

Models for draft creation, editing, regeneration, and blacklist validation.
"""

from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class GenerateDraftRequest(BaseModel):
    """Request to generate a new draft."""
    subreddit: str = Field(..., min_length=1, max_length=100)
    archetype: Literal["Journey", "ProblemSolution", "Feedback"]
    context: Optional[str] = Field(None, max_length=2000)
    account_status: Optional[Literal["New", "WarmingUp", "Established"]] = "Established"


class DraftResponse(BaseModel):
    """Generated draft with metadata and scores."""
    id: UUID
    campaign_id: UUID
    subreddit: str
    archetype: str
    title: Optional[str] = None
    body: str
    vulnerability_score: float
    rhythm_match_score: float
    blacklist_violations: int
    model_used: str
    token_count: int
    token_cost_usd: float
    generation_params: dict
    status: Literal["generated", "edited", "approved", "posted", "discarded"]
    user_edits: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DraftListResponse(BaseModel):
    """List of drafts with pagination."""
    drafts: list[DraftResponse]
    total: int


class UpdateDraftRequest(BaseModel):
    """Update draft status or edits."""
    status: Optional[Literal["generated", "edited", "approved", "posted", "discarded"]] = None
    user_edits: Optional[str] = None


class RegenerateDraftRequest(BaseModel):
    """Request to regenerate draft with optional feedback."""
    feedback: Optional[str] = Field(None, max_length=1000)


class BlacklistViolation(BaseModel):
    """Single blacklist violation detail."""
    pattern: str
    category: str
    matched_text: str


class BlacklistCheckResult(BaseModel):
    """Result of blacklist validation check."""
    passed: bool
    violations: list[BlacklistViolation]
