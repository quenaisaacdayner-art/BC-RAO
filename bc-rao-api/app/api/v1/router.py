"""
Main v1 API router.
Aggregates all v1 endpoint routers.
"""
from fastapi import APIRouter
from app.api.v1 import auth, campaigns, collection, analysis, drafts, monitoring

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

# Include monitoring router (Phase 5, Plan 2)
router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])

# Placeholder for future sub-routers:
# - billing.py (Phase 6)
