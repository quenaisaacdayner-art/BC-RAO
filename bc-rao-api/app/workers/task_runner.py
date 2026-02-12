"""
Lightweight in-process task runner using Redis for state tracking.
Replaces Celery for Railway deployment where memory is limited.

Tasks run as asyncio background tasks within the FastAPI process.
Progress is stored in Redis and polled by the SSE endpoint.
"""
import asyncio
import json
import uuid
from typing import Optional

import redis

from app.config import settings

_redis_client = None


def get_redis():
    """Get or create Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


def generate_task_id() -> str:
    """Generate a unique task ID."""
    return str(uuid.uuid4())


def update_task_state(task_id: str, state: str, meta: dict):
    """Write task state to Redis with 1-hour TTL."""
    r = get_redis()
    r.setex(
        f"task:{task_id}",
        3600,
        json.dumps({"state": state, "meta": meta})
    )


def get_task_state(task_id: str) -> dict:
    """Read task state from Redis."""
    r = get_redis()
    data = r.get(f"task:{task_id}")
    if data:
        return json.loads(data)
    return {"state": "PENDING", "meta": {}}


async def run_collection_background(task_id: str, campaign_id: str, user_id: str, plan: str):
    """
    Run collection pipeline as an asyncio background task.
    Stores progress in Redis for SSE streaming.

    After successful collection, auto-triggers analysis pipeline (LOCKED user decision).
    """
    from app.services.collection_service import CollectionService
    from app.models.raw_posts import CollectionProgress

    def progress_callback(progress: CollectionProgress):
        update_task_state(task_id, "PROGRESS", {
            "state": progress.state,
            "scraped": progress.scraped,
            "filtered": progress.filtered,
            "classified": progress.classified,
            "current_step": progress.current_step,
            "total_steps": progress.total_steps,
            "current_subreddit": progress.current_subreddit,
            "errors": progress.errors
        })

    try:
        update_task_state(task_id, "STARTED", {"state": "started"})

        service = CollectionService()
        result = await service.run_collection(
            campaign_id=campaign_id,
            user_id=user_id,
            plan=plan,
            progress_callback=progress_callback
        )

        # Auto-trigger analysis after successful collection (LOCKED user decision)
        analysis_task_id = generate_task_id()

        update_task_state(task_id, "SUCCESS", {
            "status": result.status,
            "scraped": result.scraped,
            "filtered": result.filtered,
            "classified": result.classified,
            "errors": result.errors,
            "analysis_task_id": analysis_task_id  # Frontend can track analysis progress
        })

        # Launch analysis as background task (pass user_id/plan for style guide)
        asyncio.create_task(
            run_analysis_background_task(
                analysis_task_id, campaign_id,
                user_id=user_id, plan=plan,
            )
        )

    except Exception as e:
        update_task_state(task_id, "FAILURE", {
            "error": str(e),
            "type": type(e).__name__
        })


async def run_analysis_background_task(
    task_id: str,
    campaign_id: str,
    force_refresh: bool = False,
    user_id: Optional[str] = None,
    plan: Optional[str] = None,
):
    """
    Run analysis pipeline as an asyncio background task.
    Stores progress in Redis for SSE streaming.

    Args:
        task_id: Task UUID for Redis state tracking
        campaign_id: Campaign UUID
        force_refresh: If True, re-analyze even if profiles exist
        user_id: User UUID for LLM style guide cost tracking
        plan: User plan for budget enforcement
    """
    from app.workers.analysis_worker import run_analysis_background

    await run_analysis_background(task_id, campaign_id, force_refresh, user_id=user_id, plan=plan)


async def run_monitoring_check_background_task(task_id: str, shadow_id: str):
    """
    Run monitoring check as an asyncio background task.
    Stores progress in Redis for SSE streaming.

    Args:
        task_id: Task UUID for Redis state tracking
        shadow_id: Shadow entry UUID
    """
    from app.workers.monitoring_worker import run_monitoring_check

    await run_monitoring_check(task_id, shadow_id)


async def run_audit_background_task(task_id: str, shadow_id: str):
    """
    Run 7-day post audit as an asyncio background task.
    Stores progress in Redis for SSE streaming.

    Args:
        task_id: Task UUID for Redis state tracking
        shadow_id: Shadow entry UUID
    """
    from app.workers.monitoring_worker import run_post_audit

    await run_post_audit(task_id, shadow_id)


async def schedule_periodic_monitoring():
    """
    Schedule periodic monitoring checks every 15 minutes.

    Creates a recurring asyncio task that dispatches pending checks.
    Runs indefinitely in the background.
    """
    from app.workers.monitoring_worker import dispatch_pending_checks
    import logging

    logger = logging.getLogger(__name__)
    logger.info("Starting periodic monitoring scheduler (15-min interval)")

    while True:
        try:
            await dispatch_pending_checks()
        except Exception as e:
            logger.error(f"Periodic monitoring dispatch error: {e}")

        # Sleep for 15 minutes
        await asyncio.sleep(900)
