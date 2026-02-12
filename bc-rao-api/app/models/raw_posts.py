"""
Pydantic models for raw_posts table.
Handles CRUD operations and API responses for collected Reddit posts.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class RawPostCreate(BaseModel):
    """Model for creating a new raw post."""
    campaign_id: UUID
    subreddit: str
    reddit_post_id: str
    reddit_url: Optional[str] = None
    author: Optional[str] = None
    author_karma: Optional[int] = None
    title: str
    raw_text: str
    comment_count: int = 0
    upvote_ratio: Optional[float] = None
    archetype: str = "Unclassified"
    success_score: Optional[float] = None
    reddit_created_at: Optional[datetime] = None


class RawPostResponse(RawPostCreate):
    """Model for raw post API response."""
    id: UUID
    user_id: UUID
    is_ai_processed: bool
    collected_at: datetime

    class Config:
        from_attributes = True


class RawPostListResponse(BaseModel):
    """Paginated list response for raw posts."""
    posts: list[RawPostResponse]
    total: int
    page: int
    per_page: int


class CollectionProgress(BaseModel):
    """Real-time collection progress for SSE/polling."""
    state: str = Field(
        ...,
        description="Current state: scraping, filtering, classifying, storing, complete, error"
    )
    scraped: int = Field(default=0, description="Total posts scraped so far")
    filtered: int = Field(default=0, description="Posts passing quality filter")
    classified: int = Field(default=0, description="Posts classified by LLM")
    current_step: int = Field(default=1, description="Current step number")
    total_steps: int = Field(default=1, description="Total steps in pipeline")
    current_subreddit: Optional[str] = Field(default=None, description="Currently processing subreddit")
    errors: list[str] = Field(default_factory=list, description="Error messages")


class CollectionResult(BaseModel):
    """Final result after collection pipeline completes."""
    status: str = Field(
        ...,
        description="complete | partial (if some subreddits failed)"
    )
    scraped: int = Field(description="Total posts scraped")
    filtered: int = Field(description="Total posts after quality filter")
    classified: int = Field(description="Total posts classified")
    errors: list[str] = Field(default_factory=list, description="Error messages if any")
