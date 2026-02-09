"""
Main v1 API router.
Aggregates all v1 endpoint routers.
"""
from fastapi import APIRouter

# Create main v1 router
router = APIRouter()

# Placeholder for future sub-routers
# These will be added in subsequent plans:
# - auth.py (Phase 1, Plan 3)
# - campaigns.py (Phase 1, Plan 5)
# - collector.py (Phase 2)
# - analyzer.py (Phase 3)
# - generator.py (Phase 4)
# - monitor.py (Phase 5)
# - billing.py (Phase 6)

# Example of how sub-routers will be included:
# from app.api.v1 import auth, campaigns
# router.include_router(auth.router, prefix="/auth", tags=["auth"])
# router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
