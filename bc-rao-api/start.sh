#!/bin/bash

# Start Celery worker in background
celery -A app.workers.celery_app worker --loglevel=info -Q scraping,analysis,generation,monitoring &

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
