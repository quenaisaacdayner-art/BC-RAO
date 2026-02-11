"""
Monitoring API endpoints for post registration and shadowban tracking.

Endpoints:
- POST /register: Register a post for monitoring
- GET /posts: List monitored posts for a campaign
- GET /dashboard: Aggregate monitoring stats
- GET /{shadow_id}: Single monitored post detail
- GET /stream/{task_id}: Stream monitoring check progress via SSE
"""
import asyncio
import json
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.workers.task_runner import generate_task_id, get_task_state, update_task_state
from app.services.monitoring_service import MonitoringService
from app.models.monitoring import (
    RegisterPostRequest,
    RegisterPostResponse,
    ShadowEntry,
    MonitoringDashboardStats,
)
from app.dependencies import get_current_user
from app.utils.errors import ErrorCode


router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=RegisterPostResponse)
async def register_post_for_monitoring(
    request: RegisterPostRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Register a posted draft for monitoring.

    Creates shadow_table entry, schedules first monitoring check,
    and schedules 7-day audit.

    Args:
        request: RegisterPostRequest with post_url and campaign_id
        user: Current authenticated user from JWT

    Returns:
        201 Created with RegisterPostResponse

    Raises:
        400: Invalid URL format
        409: Post already registered for this user
    """
    user_id = user["sub"]

    try:
        service = MonitoringService()
        result = service.register_post(
            user_id=user_id,
            campaign_id=str(request.campaign_id),
            post_url=request.post_url
        )

        # Schedule first monitoring check as background task
        shadow_id = str(result.id)
        check_task_id = generate_task_id()

        asyncio.create_task(
            run_monitoring_check_background(check_task_id, shadow_id)
        )

        # Schedule 7-day audit as background task with ETA
        # NOTE: For production, use a proper job queue like Celery beat or APScheduler
        # For now, the dispatch_pending_checks scheduler will catch audit_due_at posts
        # This is a simplified approach for Railway deployment

        return result

    except ValueError as e:
        # URL validation errors or duplicate post
        if "already registered" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": ErrorCode.DUPLICATE_RESOURCE,
                    "message": str(e),
                    "details": {"post_url": request.post_url}
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": ErrorCode.VALIDATION_ERROR,
                    "message": str(e),
                    "details": {"post_url": request.post_url}
                }
            )


@router.get("/posts")
async def get_monitored_posts(
    campaign_id: UUID = Query(..., description="Campaign UUID"),
    status_filter: Optional[str] = Query(None, description="Filter by status", alias="status"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List monitored posts for a campaign.

    Supports optional status filter (Ativo, Removido, Shadowbanned, etc.).

    Args:
        campaign_id: Campaign UUID (required)
        status_filter: Optional status_vida filter
        user: Current authenticated user from JWT

    Returns:
        200 OK with {"posts": list[ShadowEntry], "total": int}
    """
    user_id = user["sub"]

    try:
        service = MonitoringService()
        posts = service.get_monitored_posts(
            user_id=user_id,
            campaign_id=str(campaign_id),
            status=status_filter
        )

        return {
            "posts": [post.model_dump(mode="json") for post in posts],
            "total": len(posts)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": ErrorCode.INTERNAL_ERROR,
                "message": f"Failed to fetch monitored posts: {str(e)}"
            }
        )


@router.get("/dashboard", response_model=MonitoringDashboardStats)
async def get_monitoring_dashboard(
    campaign_id: UUID = Query(..., description="Campaign UUID"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get monitoring dashboard statistics.

    Returns aggregate counts, success rate, and recent alerts.

    Args:
        campaign_id: Campaign UUID (required)
        user: Current authenticated user from JWT

    Returns:
        200 OK with MonitoringDashboardStats
    """
    user_id = user["sub"]

    try:
        service = MonitoringService()
        stats = service.get_dashboard_stats(
            user_id=user_id,
            campaign_id=str(campaign_id)
        )

        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": ErrorCode.INTERNAL_ERROR,
                "message": f"Failed to fetch dashboard stats: {str(e)}"
            }
        )


@router.get("/{shadow_id}", response_model=ShadowEntry)
async def get_shadow_entry_detail(
    shadow_id: UUID,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get single monitored post detail.

    Includes full shadow entry with check history from metadata.

    Args:
        shadow_id: Shadow entry UUID
        user: Current authenticated user from JWT

    Returns:
        200 OK with ShadowEntry

    Raises:
        404: Entry not found or access denied
    """
    user_id = user["sub"]

    try:
        service = MonitoringService()
        entry = service.get_shadow_entry(
            shadow_id=str(shadow_id),
            user_id=user_id
        )

        return entry

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.RESOURCE_NOT_FOUND,
                "message": str(e),
                "details": {"shadow_id": str(shadow_id)}
            }
        )


@router.get("/stream/{task_id}")
async def stream_monitoring_progress(
    task_id: str
):
    """
    Stream monitoring check progress via Server-Sent Events (SSE).

    Polls task state every 500ms and yields SSE events with progress data.
    No authentication required - task_id acts as bearer token (unguessable UUID).

    SSE events:
    - started: {"state": "started"}
    - progress: {"type": "status", "message": "Checking post..."}
    - success: {"type": "complete", "result": {...}}
    - error: {"type": "error", "message": "..."}
    - done: Final event signaling stream close

    Args:
        task_id: Task UUID from registration response

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


async def run_monitoring_check_background(task_id: str, shadow_id: str):
    """
    Run monitoring check pipeline as an asyncio background task.

    Imports the actual worker function to avoid circular dependencies.

    Args:
        task_id: Task UUID for Redis state tracking
        shadow_id: Shadow entry UUID
    """
    from app.workers.task_runner import run_monitoring_check_background_task
    await run_monitoring_check_background_task(task_id, shadow_id)
