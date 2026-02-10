"""
Celery worker for asynchronous collection pipeline execution.
Runs scraping, filtering, classification, and storage with real-time progress tracking.
"""
import asyncio
from typing import Optional

from app.workers.celery_app import celery_app
from app.services.collection_service import CollectionService
from app.models.raw_posts import CollectionProgress


@celery_app.task(bind=True, name="app.workers.tasks.scraping.collect_campaign_data", max_retries=0)
def collect_campaign_data(self, campaign_id: str, user_id: str, plan: str) -> dict:
    """
    Celery task to run collection pipeline for a campaign with progress tracking.

    This task bridges sync Celery with async CollectionService by using asyncio.run().
    Emits PROGRESS state updates via self.update_state() for SSE streaming.

    Task routing: Matched by "app.workers.tasks.scraping.*" pattern -> scraping queue.

    Args:
        campaign_id: Campaign UUID
        user_id: User UUID (for ownership verification)
        plan: User plan tier (trial, starter, growth)

    Returns:
        Dict with status, scraped, filtered, classified counts, and errors list

    Raises:
        Re-raises exceptions after updating task state to FAILURE
    """

    def progress_callback(progress: CollectionProgress) -> None:
        """
        Callback to emit Celery task progress updates for SSE streaming.

        Guard with called_directly check to allow direct testing without Celery.
        """
        # Only update state if running as Celery task (not direct call)
        if not self.request.called_directly:
            self.update_state(
                state='PROGRESS',
                meta={
                    'state': progress.state,
                    'scraped': progress.scraped,
                    'filtered': progress.filtered,
                    'classified': progress.classified,
                    'current_step': progress.current_step,
                    'total_steps': progress.total_steps,
                    'current_subreddit': progress.current_subreddit,
                    'errors': progress.errors
                }
            )

    try:
        # Instantiate collection service
        service = CollectionService()

        # Run async collection method using asyncio.run()
        # This bridges sync Celery task with async service layer
        result = asyncio.run(
            service.run_collection(
                campaign_id=campaign_id,
                user_id=user_id,
                plan=plan,
                progress_callback=progress_callback
            )
        )

        # Return final result
        return {
            "status": result.status,
            "scraped": result.scraped,
            "filtered": result.filtered,
            "classified": result.classified,
            "errors": result.errors
        }

    except Exception as e:
        # Update task state to FAILURE with error details
        if not self.request.called_directly:
            self.update_state(
                state='FAILURE',
                meta={
                    'error': str(e),
                    'type': type(e).__name__
                }
            )
        # Re-raise for Celery to mark task as failed
        raise
