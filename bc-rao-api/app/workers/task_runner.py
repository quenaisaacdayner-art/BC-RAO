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

        update_task_state(task_id, "SUCCESS", {
            "status": result.status,
            "scraped": result.scraped,
            "filtered": result.filtered,
            "classified": result.classified,
            "errors": result.errors
        })
    except Exception as e:
        update_task_state(task_id, "FAILURE", {
            "error": str(e),
            "type": type(e).__name__
        })
