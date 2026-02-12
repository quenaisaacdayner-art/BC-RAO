"""
Draft API endpoints for generation, listing, updating, regenerating, and deleting drafts.

Endpoints:
- POST /campaigns/{campaign_id}/drafts/generate: Trigger async draft generation
- GET /campaigns/{campaign_id}/drafts/generate/stream/{task_id}: Stream generation progress via SSE
- GET /campaigns/{campaign_id}/drafts: List drafts with filters
- PATCH /drafts/{draft_id}: Update draft status/edits
- POST /drafts/{draft_id}/regenerate: Regenerate draft with feedback
- DELETE /drafts/{draft_id}: Delete draft
"""
import asyncio
import json
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.workers.task_runner import generate_task_id, get_task_state
from app.generation.generation_service import GenerationService
from app.models.draft import (
    GenerateDraftRequest,
    DraftResponse,
    DraftListResponse,
    UpdateDraftRequest,
    RegenerateDraftRequest,
)
from app.dependencies import get_current_user
from app.integrations.supabase_client import get_supabase_client
from app.utils.errors import AppError, ErrorCode


# Draft endpoints under /drafts prefix (except generate which is under /campaigns)
router = APIRouter()


# Plan limits for draft generation (from system spec)
PLAN_LIMITS = {
    "trial":   {"drafts_month": 10},
    "starter": {"drafts_month": 50},
    "growth":  {"drafts_month": -1},  # -1 = unlimited
}


async def check_monthly_draft_limit(user_id: str, plan: str) -> None:
    """
    Check if user has exceeded monthly draft generation limit.

    Args:
        user_id: User UUID
        plan: User plan tier (trial, starter, growth)

    Raises:
        HTTPException: 403 if monthly limit exceeded
    """
    # Growth plan has unlimited drafts
    limit = PLAN_LIMITS[plan]["drafts_month"]
    if limit == -1:
        return

    # Count drafts generated this month
    supabase = get_supabase_client()
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    count_response = supabase.table("generated_drafts").select(
        "id", count="exact"
    ).eq("user_id", user_id).gte("created_at", month_start.isoformat()).execute()

    current_count = count_response.count or 0

    if current_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": ErrorCode.PLAN_LIMIT_REACHED,
                "message": f"Monthly draft limit reached ({limit} drafts/month for {plan} plan)",
                "details": {
                    "current": current_count,
                    "limit": limit,
                    "plan": plan
                }
            }
        )


@router.post("/campaigns/{campaign_id}/drafts/generate", status_code=status.HTTP_202_ACCEPTED)
async def trigger_generation(
    campaign_id: UUID,
    request: GenerateDraftRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Trigger asynchronous draft generation for a campaign.

    Validates campaign ownership, checks monthly limits, then queues background task.
    Returns task_id for progress monitoring via SSE endpoint.

    Args:
        campaign_id: Campaign UUID
        request: GenerateDraftRequest with subreddit, archetype, context, account_status
        user: Current authenticated user from JWT

    Returns:
        202 Accepted with task_id and status="queued"

    Raises:
        403: Monthly draft limit exceeded
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

    # Check monthly draft limit
    await check_monthly_draft_limit(user_id, plan)

    # Run generation as background task
    task_id = generate_task_id()
    asyncio.create_task(
        run_generation_background(
            task_id=task_id,
            campaign_id=str(campaign_id),
            user_id=user_id,
            plan=plan,
            request=request
        )
    )

    return {
        "task_id": task_id,
        "status": "queued"
    }


async def run_generation_background(
    task_id: str,
    campaign_id: str,
    user_id: str,
    plan: str,
    request: GenerateDraftRequest
):
    """
    Run draft generation pipeline as an asyncio background task.
    Stores progress in Redis for SSE streaming.

    Args:
        task_id: Task UUID for Redis state tracking
        campaign_id: Campaign UUID
        user_id: User UUID
        plan: User plan tier
        request: GenerateDraftRequest with generation parameters
    """
    from app.workers.task_runner import update_task_state

    def emit_progress(message: str):
        """Helper to emit progress status events."""
        update_task_state(task_id, "PROGRESS", {
            "type": "status",
            "message": message
        })

    try:
        update_task_state(task_id, "STARTED", {"state": "started"})

        service = GenerationService()

        # Emit progress events during generation
        emit_progress("Loading community profile...")
        await asyncio.sleep(0.1)  # Allow progress to be captured

        emit_progress("Checking ISC gating...")
        await asyncio.sleep(0.1)

        emit_progress("Building prompt...")
        await asyncio.sleep(0.1)

        emit_progress("Generating draft via LLM...")

        # Call generation service
        draft = await service.generate_draft(
            campaign_id=campaign_id,
            user_id=user_id,
            plan=plan,
            request=request
        )

        emit_progress("Validating against blacklist...")
        await asyncio.sleep(0.1)

        emit_progress("Scoring draft...")
        await asyncio.sleep(0.1)

        emit_progress("Saving draft...")
        await asyncio.sleep(0.1)

        # Convert DraftResponse to dict for JSON serialization
        draft_dict = draft.model_dump(mode="json")

        update_task_state(task_id, "SUCCESS", {
            "type": "complete",
            "draft": draft_dict
        })

    except AppError as e:
        # User-facing errors (ISC gating blocks, plan limits, etc.)
        update_task_state(task_id, "FAILURE", {
            "type": "error",
            "message": e.message,
            "code": e.code,
            "details": e.details
        })
    except Exception as e:
        # System errors
        update_task_state(task_id, "FAILURE", {
            "type": "error",
            "message": f"Generation failed: {str(e)}",
            "code": ErrorCode.INTERNAL_ERROR
        })


@router.get("/campaigns/{campaign_id}/drafts/generate/stream/{task_id}")
async def stream_generation_progress(
    campaign_id: UUID,
    task_id: str
):
    """
    Stream real-time generation progress via Server-Sent Events (SSE).

    Polls task state every 500ms and yields SSE events with progress data.
    No authentication required - task_id acts as bearer token (unguessable UUID).

    SSE events:
    - status: {"type": "status", "message": "Loading community profile..."}
    - chunk: {"type": "chunk", "content": "..."} (for future streaming)
    - complete: {"type": "complete", "draft": DraftResponse}
    - error: {"type": "error", "message": "..."}
    - done: Final event signaling stream close

    Args:
        campaign_id: Campaign UUID (context only, not validated)
        task_id: Task UUID from trigger_generation response

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


@router.get("/campaigns/{campaign_id}/drafts", response_model=DraftListResponse)
async def get_drafts(
    campaign_id: UUID,
    status: Optional[str] = Query(None, description="Filter by status"),
    subreddit: Optional[str] = Query(None, description="Filter by subreddit"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get paginated list of drafts for a campaign with optional filters.

    Supports filtering by status and subreddit.
    Results ordered by created_at DESC.

    Args:
        campaign_id: Campaign UUID
        status: Filter by status (generated, edited, approved, posted, discarded)
        subreddit: Filter by subreddit name
        limit: Max results to return (max 100)
        offset: Pagination offset
        user: Current authenticated user from JWT

    Returns:
        DraftListResponse with drafts and total count
    """
    user_id = user["sub"]

    service = GenerationService()
    result = await service.get_drafts(
        campaign_id=str(campaign_id),
        user_id=user_id,
        status=status,
        subreddit=subreddit,
        limit=limit,
        offset=offset
    )

    return result


@router.get("/drafts/{draft_id}", response_model=DraftResponse)
async def get_draft(
    draft_id: UUID,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a single draft by ID.

    Args:
        draft_id: Draft UUID
        user: Current authenticated user from JWT

    Returns:
        DraftResponse

    Raises:
        404: Draft not found or access denied
    """
    user_id = user["sub"]

    supabase = get_supabase_client()
    response = supabase.table("generated_drafts").select("*").eq(
        "id", str(draft_id)
    ).eq("user_id", user_id).execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.RESOURCE_NOT_FOUND,
                "message": "Draft not found or access denied",
                "details": {"draft_id": str(draft_id)}
            }
        )

    draft = response.data[0]
    return DraftResponse(
        id=draft["id"],
        campaign_id=draft["campaign_id"],
        subreddit=draft["subreddit"],
        archetype=draft["archetype"],
        title=draft.get("title"),
        body=draft["body"],
        vulnerability_score=draft["vulnerability_score"],
        rhythm_match_score=draft["rhythm_match_score"],
        blacklist_violations=draft["blacklist_violations"],
        model_used=draft["model_used"],
        token_count=draft["token_count"],
        token_cost_usd=draft["token_cost_usd"],
        generation_params=draft.get("generation_params", {}),
        status=draft["status"],
        user_edits=draft.get("user_edits"),
        created_at=draft["created_at"],
        updated_at=draft["updated_at"],
    )


@router.patch("/drafts/{draft_id}", response_model=DraftResponse)
async def update_draft(
    draft_id: UUID,
    update: UpdateDraftRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update draft status or user edits.

    Allows users to approve, discard, or edit drafts.

    Args:
        draft_id: Draft UUID
        update: UpdateDraftRequest with status and/or user_edits
        user: Current authenticated user from JWT

    Returns:
        Updated DraftResponse

    Raises:
        404: Draft not found or access denied
    """
    user_id = user["sub"]

    service = GenerationService()
    try:
        result = await service.update_draft(
            draft_id=str(draft_id),
            user_id=user_id,
            update=update
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


@router.post("/drafts/{draft_id}/regenerate", status_code=status.HTTP_202_ACCEPTED)
async def regenerate_draft(
    draft_id: UUID,
    request: RegenerateDraftRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Regenerate a draft with optional user feedback.

    Checks monthly draft limit, then queues regeneration task.
    Preserves original draft parameters and appends feedback to context.

    Args:
        draft_id: Original draft UUID
        request: RegenerateDraftRequest with optional feedback
        user: Current authenticated user from JWT

    Returns:
        202 Accepted with task_id and status="queued"

    Raises:
        403: Monthly draft limit exceeded
        404: Original draft not found
    """
    user_id = user["sub"]

    # User plan — defaults to "trial" until billing (Phase 6) is implemented
    plan = "trial"

    # Check monthly draft limit (regeneration counts toward limit)
    await check_monthly_draft_limit(user_id, plan)

    # Run regeneration as background task
    task_id = generate_task_id()
    asyncio.create_task(
        run_regeneration_background(
            task_id=task_id,
            draft_id=str(draft_id),
            user_id=user_id,
            plan=plan,
            feedback=request.feedback
        )
    )

    return {
        "task_id": task_id,
        "status": "queued"
    }


async def run_regeneration_background(
    task_id: str,
    draft_id: str,
    user_id: str,
    plan: str,
    feedback: Optional[str]
):
    """
    Run draft regeneration pipeline as an asyncio background task.
    Stores progress in Redis for SSE streaming.

    Args:
        task_id: Task UUID for Redis state tracking
        draft_id: Original draft UUID
        user_id: User UUID
        plan: User plan tier
        feedback: Optional user feedback to incorporate
    """
    from app.workers.task_runner import update_task_state

    def emit_progress(message: str):
        """Helper to emit progress status events."""
        update_task_state(task_id, "PROGRESS", {
            "type": "status",
            "message": message
        })

    try:
        update_task_state(task_id, "STARTED", {"state": "started"})

        service = GenerationService()

        # Emit progress events during regeneration
        emit_progress("Loading original draft...")
        await asyncio.sleep(0.1)

        emit_progress("Incorporating feedback...")
        await asyncio.sleep(0.1)

        emit_progress("Regenerating draft...")

        # Call regeneration service
        draft = await service.regenerate_draft(
            draft_id=draft_id,
            user_id=user_id,
            plan=plan,
            feedback=feedback
        )

        emit_progress("Validating regenerated draft...")
        await asyncio.sleep(0.1)

        emit_progress("Saving draft...")
        await asyncio.sleep(0.1)

        # Convert DraftResponse to dict for JSON serialization
        draft_dict = draft.model_dump(mode="json")

        update_task_state(task_id, "SUCCESS", {
            "type": "complete",
            "draft": draft_dict
        })

    except AppError as e:
        # User-facing errors
        update_task_state(task_id, "FAILURE", {
            "type": "error",
            "message": e.message,
            "code": e.code,
            "details": e.details
        })
    except Exception as e:
        # System errors
        update_task_state(task_id, "FAILURE", {
            "type": "error",
            "message": f"Regeneration failed: {str(e)}",
            "code": ErrorCode.INTERNAL_ERROR
        })


@router.delete("/drafts/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_draft(
    draft_id: UUID,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a draft.

    Args:
        draft_id: Draft UUID
        user: Current authenticated user from JWT

    Returns:
        204 No Content

    Raises:
        404: Draft not found or access denied
    """
    user_id = user["sub"]

    service = GenerationService()
    try:
        await service.delete_draft(
            draft_id=str(draft_id),
            user_id=user_id
        )
        return None
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details
            }
        )
