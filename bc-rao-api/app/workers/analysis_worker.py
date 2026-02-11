"""
Background worker for asynchronous analysis pipeline execution.

Runs NLP analysis, scoring, profiling, and pattern extraction with real-time progress tracking.
"""

from app.services.analysis_service import AnalysisService
from app.models.analysis import AnalysisProgress


async def run_analysis_background(task_id: str, campaign_id: str, force_refresh: bool = False):
    """
    Run analysis pipeline as background task with progress tracking.

    This function is called by run_analysis_background_task in task_runner.py.
    It wraps AnalysisService and provides progress updates via Redis state tracking.

    Args:
        task_id: Task UUID for Redis state tracking
        campaign_id: Campaign UUID
        force_refresh: If True, re-analyze even if profiles exist
    """
    from app.workers.task_runner import update_task_state

    def progress_callback(progress: AnalysisProgress) -> None:
        """
        Callback to emit analysis progress updates for SSE streaming.

        Stores progress in Redis for the SSE endpoint to poll.
        """
        update_task_state(task_id, "PROGRESS", {
            "state": progress.state,
            "current": progress.current,
            "total": progress.total,
            "status": progress.status,
            "current_step": progress.current_step,
        })

    try:
        # Instantiate analysis service
        service = AnalysisService()

        # Run async analysis with progress callback
        result = await service.run_analysis(
            campaign_id=campaign_id,
            force_refresh=force_refresh,
            progress_callback=progress_callback
        )

        # Update task state to SUCCESS with result data
        update_task_state(task_id, "SUCCESS", {
            "status": result.status,
            "posts_analyzed": result.posts_analyzed,
            "profiles_created": result.profiles_created,
            "errors": result.errors,
        })

    except Exception as e:
        # Update task state to FAILURE with error details
        update_task_state(task_id, "FAILURE", {
            "error": str(e),
            "type": type(e).__name__
        })
