"""
Pydantic models for Pattern Engine analysis responses.

Models for NLP results, post scoring, community profiles, and forbidden patterns.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class NLPResult(BaseModel):
    """NLP analysis result for a single post."""
    formality_score: Optional[float] = None
    tone: Optional[str] = None
    tone_compound: Optional[float] = None
    avg_sentence_length: Optional[float] = None
    sentence_length_std: Optional[float] = None
    vocabulary_complexity: Optional[float] = None
    num_sentences: Optional[int] = None


class PostScoreBreakdown(BaseModel):
    """Detailed scoring breakdown for a post."""
    post_id: UUID
    vulnerability_weight: float
    rhythm_adherence: float
    formality_match: float
    marketing_jargon_penalty: float
    link_density_penalty: float
    total_score: float
    penalty_phrases: list[dict]  # {phrase, severity, category}


class CommunityProfileResponse(BaseModel):
    """Community profile with ISC score and behavioral patterns."""
    id: UUID
    campaign_id: UUID
    subreddit: str
    isc_score: float
    isc_tier: str
    avg_sentence_length: Optional[float] = None
    dominant_tone: Optional[str] = None
    formality_level: Optional[float] = None
    top_success_hooks: list
    forbidden_patterns: list
    archetype_distribution: dict
    sample_size: int
    last_analyzed_at: datetime


class CommunityProfileListResponse(BaseModel):
    """List of community profiles."""
    profiles: list[CommunityProfileResponse]


class AnalysisProgress(BaseModel):
    """Real-time analysis progress tracking."""
    state: str
    current: int
    total: int
    status: str
    current_step: str  # "nlp_analysis", "scoring", "profiling"


class AnalysisResult(BaseModel):
    """Analysis job completion result."""
    status: str
    posts_analyzed: int
    profiles_created: int
    errors: list[str]


class ForbiddenPatternEntry(BaseModel):
    """Single forbidden pattern entry."""
    id: UUID
    category: str
    pattern: str
    subreddit: Optional[str] = None  # None = global pattern
    is_system: bool  # True = auto-detected, False = user-added
    count: int


class BlacklistResponse(BaseModel):
    """Blacklist patterns grouped by category."""
    patterns: list[ForbiddenPatternEntry]
    total: int
    categories: dict[str, int]  # category -> count


def isc_to_tier(score: float) -> str:
    """
    Convert ISC score to human-readable tier.

    Args:
        score: ISC score (1.0 to 10.0)

    Returns:
        Tier description string
    """
    if score < 3:
        return "Low Sensitivity"
    elif score < 5:
        return "Moderate Sensitivity"
    elif score < 7:
        return "High Sensitivity"
    else:
        return "Very High Sensitivity"
