"""
Collection API endpoints for triggering, monitoring, and querying Reddit post collection.

Endpoints:
- POST /campaigns/{campaign_id}/collect: Trigger async collection
- GET /collection/{task_id}/progress: Stream real-time progress via SSE
- GET /campaigns/{campaign_id}/posts: Fetch posts with filters and pagination
- GET /campaigns/{campaign_id}/posts/{post_id}: Get post detail for modal
- GET /campaigns/{campaign_id}/collection-stats: Get aggregated statistics
"""
import asyncio
import json
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.workers.task_runner import generate_task_id, run_collection_background, get_task_state
from app.services.collection_service import CollectionService
from app.models.raw_posts import RawPostListResponse, RawPostResponse
from app.dependencies import get_current_user
from app.integrations.supabase_client import get_supabase_client
from app.utils.errors import AppError, ErrorCode


# All collection endpoints under /collection prefix
router = APIRouter(prefix="/collection", tags=["collection"])


@router.post("/campaigns/{campaign_id}/collect", status_code=status.HTTP_202_ACCEPTED)
async def trigger_collection(
    campaign_id: UUID,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Trigger asynchronous collection pipeline for a campaign.

    Validates campaign exists and belongs to user, then queues Celery task.
    Returns task_id for progress monitoring via SSE endpoint.

    Billing limits NOT enforced here (deferred to Phase 6).

    Args:
        campaign_id: Campaign UUID
        user: Current authenticated user from JWT

    Returns:
        202 Accepted with task_id and status="queued"

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

    # User plan — defaults to "trial" until billing (Phase 6) is implemented
    plan = "trial"

    # Run collection as background task
    task_id = generate_task_id()
    asyncio.create_task(
        run_collection_background(task_id, str(campaign_id), user_id, plan)
    )

    return {
        "task_id": task_id,
        "status": "queued"
    }


@router.get("/{task_id}/progress")
async def stream_progress(task_id: str):
    """
    Stream real-time collection progress via Server-Sent Events (SSE).

    Polls Celery task state every 500ms and yields SSE events with progress data.
    No authentication required - task_id acts as bearer token (unguessable UUID).

    SSE format:
    - event: progress | started | pending | success | error | done
    - data: JSON payload with state details

    Args:
        task_id: Celery task UUID from trigger_collection response

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

            # Only send events when state or data changes, or as heartbeat
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
                # Send SSE keepalive comment every ~15s to prevent proxy timeouts
                heartbeat_counter += 1
                if heartbeat_counter >= 10:  # 10 * 1.5s = 15s
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


@router.get("/campaigns/{campaign_id}/posts", response_model=RawPostListResponse)
async def get_posts(
    campaign_id: UUID,
    archetype: Optional[str] = Query(None, description="Filter by archetype"),
    subreddit: Optional[str] = Query(None, description="Filter by subreddit"),
    min_score: Optional[float] = Query(None, description="Minimum success_score"),
    max_score: Optional[float] = Query(None, description="Maximum success_score"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get paginated list of collected posts with optional filters.

    Supports filtering by archetype, subreddit, and success score range.
    Results ordered by success_score DESC, then collected_at DESC.

    Args:
        campaign_id: Campaign UUID
        archetype: Filter by archetype (Journey, ProblemSolution, Feedback, Unclassified)
        subreddit: Filter by subreddit name
        min_score: Minimum success_score (inclusive)
        max_score: Maximum success_score (inclusive)
        page: Page number (1-indexed)
        per_page: Items per page (max 100)
        user: Current authenticated user from JWT

    Returns:
        RawPostListResponse with posts, total, page, per_page
    """
    user_id = user["sub"]

    service = CollectionService()
    result = await service.get_posts(
        campaign_id=str(campaign_id),
        user_id=user_id,
        archetype=archetype,
        subreddit=subreddit,
        min_score=min_score,
        max_score=max_score,
        page=page,
        per_page=per_page
    )

    return result


@router.get("/campaigns/{campaign_id}/posts/{post_id}", response_model=RawPostResponse)
async def get_post_detail(
    campaign_id: UUID,
    post_id: UUID,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get detailed information for a single post (for modal display).

    Args:
        campaign_id: Campaign UUID (for context, not used in query)
        post_id: Post UUID
        user: Current authenticated user from JWT

    Returns:
        RawPostResponse with full post details

    Raises:
        404: Post not found or not owned by user
    """
    user_id = user["sub"]

    service = CollectionService()
    try:
        result = await service.get_post_detail(
            post_id=str(post_id),
            user_id=user_id
        )
        return result
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details
            }
        )


@router.get("/campaigns/{campaign_id}/stats")
async def get_collection_stats(
    campaign_id: UUID,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get aggregated collection statistics for a campaign.

    Returns counts by archetype and subreddit, plus average success score.

    Args:
        campaign_id: Campaign UUID
        user: Current authenticated user from JWT

    Returns:
        Dict with:
        - total: Total post count
        - by_archetype: {archetype: count}
        - by_subreddit: {subreddit: count}
        - avg_success_score: Average success score
    """
    user_id = user["sub"]

    service = CollectionService()
    stats = await service.get_collection_stats(
        campaign_id=str(campaign_id),
        user_id=user_id
    )

    return stats
