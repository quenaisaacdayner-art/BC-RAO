"""
Main v1 API router.
Aggregates all v1 endpoint routers.
"""
from fastapi import APIRouter
from app.api.v1 import auth, campaigns, collection, analysis, drafts

# Create main v1 router
router = APIRouter()

# Include auth router (Phase 1, Plan 3)
router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Include campaigns router (Phase 1, Plan 5)
router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])

# Include collection router (Phase 2, Plan 2)
router.include_router(collection.router, tags=["collection"])

# Include analysis router (Phase 3, Plan 2)
router.include_router(analysis.router, tags=["analysis"])

# Include drafts router (Phase 4, Plan 2)
router.include_router(drafts.router, tags=["drafts"])

# Placeholder for future sub-routers:
# - monitor.py (Phase 5)
# - billing.py (Phase 6)
