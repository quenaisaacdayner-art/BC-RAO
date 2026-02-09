"""
Worker package for background task processing.
Re-exports celery_app for convenience.
"""
from app.workers.celery_app import celery_app, ping

__all__ = ["celery_app", "ping"]
