"""
Main v1 API router.
Aggregates all v1 endpoint routers.
"""
from fastapi import APIRouter
from app.api.v1 import auth

# Create main v1 router
router = APIRouter()

# Include auth router (Phase 1, Plan 3)
router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Placeholder for future sub-routers:
# - campaigns.py (Phase 1, Plan 5)
# - collector.py (Phase 2)
# - analyzer.py (Phase 3)
# - generator.py (Phase 4)
# - monitor.py (Phase 5)
# - billing.py (Phase 6)
