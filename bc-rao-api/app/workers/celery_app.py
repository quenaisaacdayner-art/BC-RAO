"""
Celery application configuration for BC-RAO background tasks.
Supports 4 task queues: scraping, analysis, generation, monitoring.
"""
from celery import Celery
from app.config import settings

# Create Celery app instance
celery_app = Celery(
    "bc-rao",
    broker=settings.celery_broker,
    backend=settings.celery_backend
)

# Configure Celery
celery_app.conf.update(
    # Serialization (security: use JSON, not pickle)
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task tracking
    task_track_started=True,
    task_acks_late=True,  # Re-queue tasks on worker crash

    # Task routing: map task names to queues
    task_routes={
        "app.workers.tasks.scraping.*": {"queue": "scraping"},
        "app.workers.tasks.analysis.*": {"queue": "analysis"},
        "app.workers.tasks.generation.*": {"queue": "generation"},
        "app.workers.tasks.monitoring.*": {"queue": "monitoring"},
    },

    # Default queue
    task_default_queue="scraping",
)


@celery_app.task(name="ping")
def ping() -> str:
    """Test task to verify Celery is working."""
    return "pong"
