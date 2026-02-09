"""
Campaign request/response models.
Used for campaign CRUD operations and validation.
"""
from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class CampaignCreate(BaseModel):
    """Request body for creating a campaign."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    product_context: str = Field(..., min_length=10)
    product_url: Optional[HttpUrl] = None
    keywords: list[str] = Field(..., min_length=5, max_length=15)
    target_subreddits: list[str] = Field(..., min_length=1)


class CampaignUpdate(BaseModel):
    """Request body for updating a campaign."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    product_context: Optional[str] = Field(None, min_length=10)
    product_url: Optional[HttpUrl] = None
    keywords: Optional[list[str]] = Field(None, min_length=5, max_length=15)
    target_subreddits: Optional[list[str]] = Field(None, min_length=1)
    status: Optional[Literal["active", "paused", "archived"]] = None


class CampaignResponse(BaseModel):
    """Response model for a single campaign."""
    id: str
    name: str
    description: Optional[str] = None
    product_context: str
    product_url: Optional[str] = None
    keywords: list[str]
    target_subreddits: list[str]
    status: str
    created_at: datetime
    updated_at: datetime


class CampaignWithStats(CampaignResponse):
    """Campaign response with aggregated statistics."""
    stats: dict = Field(
        default_factory=lambda: {
            "posts_collected": 0,
            "drafts_generated": 0,
            "active_monitors": 0
        }
    )


class CampaignListResponse(BaseModel):
    """Response model for campaign list."""
    campaigns: list[CampaignResponse]
    total: int
