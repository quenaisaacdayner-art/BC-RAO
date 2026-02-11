"""
Analysis API endpoints for triggering, monitoring, and querying analysis results.

Endpoints:
- POST /campaigns/{campaign_id}/analyze: Trigger async analysis (manual or force-refresh)
- GET /analysis/{task_id}/progress: Stream real-time progress via SSE
- GET /campaigns/{campaign_id}/community-profile: Get single community profile
- GET /campaigns/{campaign_id}/community-profiles: Get all profiles for comparison
- GET /campaigns/{campaign_id}/scoring-breakdown: Get detailed post scoring
- GET /campaigns/{campaign_id}/analyzed-posts: Get posts with scores and filtering
- GET /campaigns/{campaign_id}/forbidden-patterns: Get blacklist patterns
- POST /campaigns/{campaign_id}/forbidden-patterns: Add custom pattern
"""
import asyncio
import json
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.workers.task_runner import generate_task_id, run_analysis_background_task, get_task_state
from app.services.analysis_service import AnalysisService
from app.models.analysis import (
    CommunityProfileResponse,
    CommunityProfileListResponse,
    PostScoreBreakdown,
    BlacklistResponse,
)
from app.dependencies import get_current_user
from app.integrations.supabase_client import get_supabase_client
from app.utils.errors import AppError, ErrorCode


# Analysis endpoints under /analysis prefix for SSE, rest under /campaigns for REST
router = APIRouter(prefix="/analysis", tags=["analysis"])


class TriggerAnalysisRequest(BaseModel):
    """Request body for triggering analysis."""
    force_refresh: bool = False


class TriggerAnalysisResponse(BaseModel):
    """Response for analysis trigger."""
    task_id: str
    status: str


class AddPatternRequest(BaseModel):
    """Request body for adding custom forbidden pattern."""
    category: str
    pattern: str
    subreddit: Optional[str] = None


@router.post("/campaigns/{campaign_id}/analyze", status_code=status.HTTP_202_ACCEPTED)
async def trigger_analysis(
    campaign_id: UUID,
    request: TriggerAnalysisRequest = Body(default=TriggerAnalysisRequest()),
    user: Dict[str, Any] = Depends(get_current_user)
) -> TriggerAnalysisResponse:
    """
    Trigger asynchronous analysis pipeline for a campaign.

    This is the MANUAL trigger endpoint. Auto-trigger happens via collection completion.
    Use this for force-refresh or manual re-analysis.

    Validates campaign exists and belongs to user, then launches background task.
    Returns task_id for progress monitoring via SSE endpoint.

    Args:
        campaign_id: Campaign UUID
        request: Request body with force_refresh flag
        user: Current authenticated user from JWT

    Returns:
        202 Accepted with task_id and status="started"

    Raises:
        404: Campaign not found or not owned by user
    """
    user_id = user["sub"]

    # Validate campaign exists and belongs to user
    supabase = get_supabase_client()
    response = supabase.table("campaigns").select("id, user_id").eq("id", str(campaign_id)).eq("user_id", user_id).execute()
    campaign = response.data[0] if response.data else None

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.RESOURCE_NOT_FOUND,
                "message": "Campaign not found or access denied",
                "details": {"campaign_id": str(campaign_id)}
            }
        )

    # Run analysis as background task
    task_id = generate_task_id()
    asyncio.create_task(
        run_analysis_background_task(task_id, str(campaign_id), request.force_refresh)
    )

    return TriggerAnalysisResponse(
        task_id=task_id,
        status="started"
    )


@router.get("/{task_id}/progress")
async def stream_progress(task_id: str):
    """
    Stream real-time analysis progress via Server-Sent Events (SSE).

    Polls task state from Redis every 500ms and yields SSE events with progress data.
    No authentication required - task_id acts as bearer token (unguessable UUID).

    SSE format:
    - event: progress | started | pending | success | error | done
    - data: JSON payload with state details

    Args:
        task_id: Task UUID from trigger_analysis response

    Returns:
        StreamingResponse with text/event-stream media type
    """

    async def progress_stream():
        """Generator function for SSE stream. Reads task state from Redis."""
        last_state = None
        last_meta = None
        heartbeat_counter = 0

        while True:
            task = get_task_state(task_id)
            state = task["state"]
            meta = task["meta"]

            state_changed = (state != last_state or meta != last_meta)
            last_state = state
            last_meta = meta

            if state == "SUCCESS":
                yield f"event: success\ndata: {json.dumps(meta)}\n\n"
                yield f"event: done\ndata: {{}}\n\n"
                break
            elif state == "FAILURE":
                yield f"event: error\ndata: {json.dumps(meta)}\n\n"
                yield f"event: done\ndata: {{}}\n\n"
                break
            elif state_changed:
                if state == "PROGRESS":
                    yield f"event: progress\ndata: {json.dumps(meta)}\n\n"
                elif state == "STARTED":
                    yield f"event: started\ndata: {json.dumps({'state': 'started'})}\n\n"
                elif state == "PENDING":
                    yield f"event: pending\ndata: {json.dumps({'state': 'pending'})}\n\n"
                heartbeat_counter = 0
            else:
                heartbeat_counter += 1
                if heartbeat_counter >= 10:
                    yield f": keepalive\n\n"
                    heartbeat_counter = 0

            await asyncio.sleep(1.5)

    return StreamingResponse(
        progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable NGINX buffering for real-time streaming
        }
    )


@router.get("/campaigns/{campaign_id}/community-profile")
async def get_community_profile(
    campaign_id: UUID,
    subreddit: str = Query(..., description="Subreddit name"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get single community profile by subreddit.

    Returns ISC score, behavioral patterns, dominant tone, formality level,
    top success hooks, forbidden patterns, and archetype distribution.

    Args:
        campaign_id: Campaign UUID
        subreddit: Subreddit name (required)
        user: Current authenticated user from JWT

    Returns:
        200 OK with CommunityProfileResponse

    Raises:
        404: Profile not found for subreddit
    """
    user_id = user["sub"]

    # Validate campaign ownership
    supabase = get_supabase_client()
    campaign_response = supabase.table("campaigns").select("id").eq("id", str(campaign_id)).eq("user_id", user_id).execute()

    if not campaign_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.RESOURCE_NOT_FOUND,
                "message": "Campaign not found or access denied",
                "details": {"campaign_id": str(campaign_id)}
            }
        )

    service = AnalysisService()
    try:
        profile = await service.get_community_profile(str(campaign_id), subreddit)
        return profile
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details
            }
        )


@router.get("/campaigns/{campaign_id}/community-profiles")
async def get_community_profiles(
    campaign_id: UUID,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all community profiles for a campaign.

    Used for comparison table showing ISC scores, tones, formality across subreddits.

    Args:
        campaign_id: Campaign UUID
        user: Current authenticated user from JWT

    Returns:
        200 OK with CommunityProfileListResponse
    """
    user_id = user["sub"]

    # Validate campaign ownership
    supabase = get_supabase_client()
    campaign_response = supabase.table("campaigns").select("id").eq("id", str(campaign_id)).eq("user_id", user_id).execute()

    if not campaign_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.RESOURCE_NOT_FOUND,
                "message": "Campaign not found or access denied",
                "details": {"campaign_id": str(campaign_id)}
            }
        )

    service = AnalysisService()
    profiles = await service.get_community_profiles(str(campaign_id))

    return {"profiles": profiles}


@router.get("/campaigns/{campaign_id}/scoring-breakdown")
async def get_scoring_breakdown(
    campaign_id: UUID,
    post_id: str = Query(..., description="Post UUID"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get detailed scoring breakdown for a post.

    Returns vulnerability weight, rhythm adherence, formality match, penalties,
    total score, and penalty phrases for inline highlighting.

    Args:
        campaign_id: Campaign UUID (for context)
        post_id: Post UUID (required)
        user: Current authenticated user from JWT

    Returns:
        200 OK with PostScoreBreakdown

    Raises:
        404: Post not found
    """
    user_id = user["sub"]

    # Validate campaign ownership
    supabase = get_supabase_client()
    campaign_response = supabase.table("campaigns").select("id").eq("id", str(campaign_id)).eq("user_id", user_id).execute()

    if not campaign_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.RESOURCE_NOT_FOUND,
                "message": "Campaign not found or access denied",
                "details": {"campaign_id": str(campaign_id)}
            }
        )

    service = AnalysisService()
    try:
        breakdown = await service.get_scoring_breakdown(post_id)
        return breakdown
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details
            }
        )


@router.get("/campaigns/{campaign_id}/analyzed-posts")
async def get_analyzed_posts(
    campaign_id: UUID,
    subreddit: Optional[str] = Query(None, description="Filter by subreddit"),
    sort_by: str = Query("total_score", description="Sort field"),
    sort_dir: str = Query("desc", description="Sort direction (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get paginated list of analyzed posts with filtering and sorting.

    Supports filtering by subreddit and sorting by various scoring metrics.
    Results include NLP metadata and scoring breakdowns.

    Args:
        campaign_id: Campaign UUID
        subreddit: Optional subreddit filter
        sort_by: Sort field (total_score, vulnerability_weight, rhythm_adherence, etc.)
        sort_dir: Sort direction (asc or desc)
        page: Page number (1-indexed)
        per_page: Items per page (max 100)
        user: Current authenticated user from JWT

    Returns:
        200 OK with posts, total, page, per_page
    """
    user_id = user["sub"]

    # Validate campaign ownership
    supabase = get_supabase_client()
    campaign_response = supabase.table("campaigns").select("id").eq("id", str(campaign_id)).eq("user_id", user_id).execute()

    if not campaign_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.RESOURCE_NOT_FOUND,
                "message": "Campaign not found or access denied",
                "details": {"campaign_id": str(campaign_id)}
            }
        )

    service = AnalysisService()
    result = await service.get_analyzed_posts(
        campaign_id=str(campaign_id),
        subreddit=subreddit,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        per_page=per_page
    )

    return result


@router.get("/campaigns/{campaign_id}/forbidden-patterns")
async def get_forbidden_patterns(
    campaign_id: UUID,
    subreddit: Optional[str] = Query(None, description="Filter by subreddit"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get forbidden patterns aggregated by category.

    Returns both system-detected patterns from analysis and user-added custom patterns.
    Grouped by category with counts and severity levels.

    Args:
        campaign_id: Campaign UUID
        subreddit: Optional subreddit filter
        user: Current authenticated user from JWT

    Returns:
        200 OK with BlacklistResponse (patterns, total, categories)
    """
    user_id = user["sub"]

    # Validate campaign ownership
    supabase = get_supabase_client()
    campaign_response = supabase.table("campaigns").select("id").eq("id", str(campaign_id)).eq("user_id", user_id).execute()

    if not campaign_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.RESOURCE_NOT_FOUND,
                "message": "Campaign not found or access denied",
                "details": {"campaign_id": str(campaign_id)}
            }
        )

    service = AnalysisService()
    result = await service.get_forbidden_patterns(
        campaign_id=str(campaign_id),
        subreddit=subreddit
    )

    return result


@router.post("/campaigns/{campaign_id}/forbidden-patterns", status_code=status.HTTP_201_CREATED)
async def add_custom_pattern(
    campaign_id: UUID,
    request: AddPatternRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Add custom forbidden pattern.

    Users can add custom patterns to supplement system-detected patterns.
    Custom patterns have is_system=False and can be edited/deleted later.

    System-detected patterns cannot be removed (is_system=True).

    Args:
        campaign_id: Campaign UUID
        request: AddPatternRequest with category, pattern, optional subreddit
        user: Current authenticated user from JWT

    Returns:
        201 Created with pattern entry

    Raises:
        404: Campaign not found or access denied
    """
    user_id = user["sub"]

    service = AnalysisService()
    try:
        pattern = await service.add_custom_pattern(
            campaign_id=str(campaign_id),
            user_id=user_id,
            category=request.category,
            pattern=request.pattern,
            subreddit=request.subreddit
        )
        return pattern
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details
            }
        )
