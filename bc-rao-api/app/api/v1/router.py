"""
Main v1 API router.
Aggregates all v1 endpoint routers.
"""
from fastapi import APIRouter
from app.api.v1 import auth, campaigns, collection

# Create main v1 router
router = APIRouter()

# Include auth router (Phase 1, Plan 3)
router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Include campaigns router (Phase 1, Plan 5)
router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])

# Include collection router (Phase 2, Plan 2)
router.include_router(collection.router, tags=["collection"])

# Placeholder for future sub-routers:
# - analyzer.py (Phase 3)
# - generator.py (Phase 4)
# - monitor.py (Phase 5)
# - billing.py (Phase 6)
