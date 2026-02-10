#!/bin/bash

# Start FastAPI server (collection tasks run in-process via asyncio)
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
