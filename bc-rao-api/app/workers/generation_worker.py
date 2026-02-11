"""
Celery worker for asynchronous draft generation with progress tracking.

This module is NOT used in Railway deployment (which uses lightweight task_runner).
Keeping for reference in case Celery is needed for horizontal scaling.

For Railway: See app/workers/task_runner.py which handles generation tasks
via asyncio background tasks with Redis state tracking.
"""
import asyncio
from typing import Optional

from app.workers.celery_app import celery_app
from app.generation.generation_service import GenerationService
from app.models.draft import GenerateDraftRequest


@celery_app.task(bind=True, name="app.workers.tasks.generation.generate_draft_task", max_retries=0)
def generate_draft_task(
    self,
    campaign_id: str,
    user_id: str,
    plan: str,
    subreddit: str,
    archetype: str,
    context: Optional[str],
    account_status: Optional[str]
) -> dict:
    """
    Celery task to run draft generation pipeline with progress tracking.

    This task bridges sync Celery with async GenerationService by using asyncio.run().
    Emits PROGRESS state updates via self.update_state() for SSE streaming.

    Task routing: Matched by "app.workers.tasks.generation.*" pattern -> generation queue.

    Args:
        campaign_id: Campaign UUID
        user_id: User UUID
        plan: User plan tier (trial, starter, growth)
        subreddit: Target subreddit
        archetype: Draft archetype (Journey, ProblemSolution, Feedback)
        context: Optional user context/product description
        account_status: Account status (New, WarmingUp, Established)

    Returns:
        Dict with draft data (DraftResponse serialized)

    Raises:
        Re-raises exceptions after updating task state to FAILURE
    """

    def emit_progress(message: str) -> None:
        """
        Emit Celery task progress updates for SSE streaming.

        Guard with called_directly check to allow direct testing without Celery.
        """
        if not self.request.called_directly:
            self.update_state(
                state='PROGRESS',
                meta={
                    'type': 'status',
                    'message': message
                }
            )

    try:
        # Build GenerateDraftRequest
        request = GenerateDraftRequest(
            subreddit=subreddit,
            archetype=archetype,
            context=context,
            account_status=account_status or "Established"
        )

        # Instantiate generation service
        service = GenerationService()

        # Emit progress events
        emit_progress("Loading community profile...")
        emit_progress("Checking ISC gating...")
        emit_progress("Building prompt...")
        emit_progress("Generating draft via LLM...")

        # Run async generation method using asyncio.run()
        # This bridges sync Celery task with async service layer
        draft = asyncio.run(
            service.generate_draft(
                campaign_id=campaign_id,
                user_id=user_id,
                plan=plan,
                request=request
            )
        )

        emit_progress("Validating against blacklist...")
        emit_progress("Scoring draft...")
        emit_progress("Saving draft...")

        # Convert DraftResponse to dict for JSON serialization
        draft_dict = {
            "id": str(draft.id),
            "campaign_id": str(draft.campaign_id),
            "subreddit": draft.subreddit,
            "archetype": draft.archetype,
            "title": draft.title,
            "body": draft.body,
            "vulnerability_score": draft.vulnerability_score,
            "rhythm_match_score": draft.rhythm_match_score,
            "blacklist_violations": draft.blacklist_violations,
            "model_used": draft.model_used,
            "token_count": draft.token_count,
            "token_cost_usd": draft.token_cost_usd,
            "generation_params": draft.generation_params,
            "status": draft.status,
            "user_edits": draft.user_edits,
            "created_at": draft.created_at.isoformat(),
            "updated_at": draft.updated_at.isoformat(),
        }

        # Return final result
        return {
            "type": "complete",
            "draft": draft_dict
        }

    except Exception as e:
        # Update task state to FAILURE with error details
        if not self.request.called_directly:
            self.update_state(
                state='FAILURE',
                meta={
                    'type': 'error',
                    'message': str(e),
                    'error_type': type(e).__name__
                }
            )
        # Re-raise for Celery to mark task as failed
        raise


@celery_app.task(bind=True, name="app.workers.tasks.generation.regenerate_draft_task", max_retries=0)
def regenerate_draft_task(
    self,
    draft_id: str,
    user_id: str,
    plan: str,
    feedback: Optional[str]
) -> dict:
    """
    Celery task to regenerate a draft with optional user feedback.

    Same queue and progress pattern as generate_draft_task.

    Args:
        draft_id: Original draft UUID
        user_id: User UUID
        plan: User plan tier
        feedback: Optional user feedback to incorporate

    Returns:
        Dict with regenerated draft data (DraftResponse serialized)

    Raises:
        Re-raises exceptions after updating task state to FAILURE
    """

    def emit_progress(message: str) -> None:
        """Emit Celery task progress updates for SSE streaming."""
        if not self.request.called_directly:
            self.update_state(
                state='PROGRESS',
                meta={
                    'type': 'status',
                    'message': message
                }
            )

    try:
        # Instantiate generation service
        service = GenerationService()

        # Emit progress events
        emit_progress("Loading original draft...")
        emit_progress("Incorporating feedback...")
        emit_progress("Regenerating draft...")

        # Run async regeneration method using asyncio.run()
        draft = asyncio.run(
            service.regenerate_draft(
                draft_id=draft_id,
                user_id=user_id,
                plan=plan,
                feedback=feedback
            )
        )

        emit_progress("Validating regenerated draft...")
        emit_progress("Saving draft...")

        # Convert DraftResponse to dict for JSON serialization
        draft_dict = {
            "id": str(draft.id),
            "campaign_id": str(draft.campaign_id),
            "subreddit": draft.subreddit,
            "archetype": draft.archetype,
            "title": draft.title,
            "body": draft.body,
            "vulnerability_score": draft.vulnerability_score,
            "rhythm_match_score": draft.rhythm_match_score,
            "blacklist_violations": draft.blacklist_violations,
            "model_used": draft.model_used,
            "token_count": draft.token_count,
            "token_cost_usd": draft.token_cost_usd,
            "generation_params": draft.generation_params,
            "status": draft.status,
            "user_edits": draft.user_edits,
            "created_at": draft.created_at.isoformat(),
            "updated_at": draft.updated_at.isoformat(),
        }

        # Return final result
        return {
            "type": "complete",
            "draft": draft_dict
        }

    except Exception as e:
        # Update task state to FAILURE with error details
        if not self.request.called_directly:
            self.update_state(
                state='FAILURE',
                meta={
                    'type': 'error',
                    'message': str(e),
                    'error_type': type(e).__name__
                }
            )
        # Re-raise for Celery to mark task as failed
        raise
