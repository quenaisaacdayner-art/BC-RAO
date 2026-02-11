---
phase: 05-monitoring-feedback-loop
plan: 01
subsystem: api, monitoring, integrations
tags: [reddit-api, resend, httpx, email, shadowban-detection, pydantic, supabase]

# Dependency graph
requires:
  - phase: 01-foundation-core-setup
    provides: Supabase client singleton, config pattern, Pydantic model patterns
  - phase: 04-draft-generation
    provides: generated_drafts table for draft-post linking

provides:
  - Monitoring domain Pydantic models (RegisterPostRequest, ShadowEntry, MonitoringDashboardStats)
  - MonitoringService for post registration, status tracking, audit classification
  - RedditDualCheckClient for shadowban detection via OAuth + anonymous checks
  - Email service for shadowban/success/adjustment alerts via Resend
  - parse_reddit_url validator for Reddit URL format validation

affects: [05-02-monitoring-api, 05-03-background-workers, dashboard-monitoring]

# Tech tracking
tech-stack:
  added: [resend>=2.0.0]
  patterns:
    - Reddit dual-check pattern (authenticated + anonymous verification)
    - Email rate limiting (max 1 emergency alert per 24h)
    - URL parsing with regex validation in Pydantic

key-files:
  created:
    - bc-rao-api/app/models/monitoring.py
    - bc-rao-api/app/services/monitoring_service.py
    - bc-rao-api/app/integrations/reddit_client.py
    - bc-rao-api/app/services/email_service.py
  modified:
    - bc-rao-api/app/config.py
    - bc-rao-api/requirements.txt

key-decisions:
  - "Use httpx for Reddit API (not PRAW) for lightweight HTTP-only approach"
  - "OAuth token caching for 3500 seconds to avoid repeated token requests"
  - "Graceful email fallback in development (skip sends if RESEND_API_KEY empty)"
  - "Rate limit shadowban alerts to max 1 per 24h per user"
  - "Dual-check shadowban detection: auth sees post but anon doesn't = shadowbanned"
  - "Infer draft_id from most recent approved/posted draft in same subreddit within 24h"
  - "Use subscription.plan as proxy for account_status until proper account_status tracking added"

patterns-established:
  - "Reddit URL validation regex: ^https?://(?:www\\.)?(?:old\\.)?reddit\\.com/r/([a-zA-Z0-9_]{3,21})/comments/([a-z0-9]{5,9})(?:/[^/]+)?/?$"
  - "Email service error handling: log but never crash monitoring pipeline"
  - "Rate limiting via email_alerts table query (last 24h check)"
  - "Async HTTP client lazy initialization pattern in RedditDualCheckClient"

# Metrics
duration: 6min
completed: 2026-02-11
---

# Phase 5 Plan 01: Monitoring Foundation Summary

**Reddit dual-check shadowban detection via OAuth + anonymous verification, Resend-based alert emails with rate limiting, and MonitoringService for shadow_table lifecycle management**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-11T04:11:12Z
- **Completed:** 2026-02-11T04:16:46Z
- **Tasks:** 2
- **Files created:** 4
- **Files modified:** 2

## Accomplishments

- Monitoring domain models with Reddit URL validation and shadow_table schema mapping
- MonitoringService handles post registration with draft inference, ISC snapshot, and 7-day audit classification
- RedditDualCheckClient detects shadowbans via dual-check pattern (auth + anon) using httpx
- Email service sends formatted HTML alerts (shadowban/success/adjustment) via Resend with 24h rate limiting

## Task Commits

Each task was committed atomically:

1. **Task 1: Pydantic models + monitoring service + Reddit URL validator** - `7dbde83` (feat)
2. **Task 2: Reddit dual-check client + email service** - `1c41474` (feat)

## Files Created/Modified

**Created:**
- `bc-rao-api/app/models/monitoring.py` - RegisterPostRequest with URL validation, ShadowEntry, MonitoringDashboardStats, CheckResult, PostAuditResult models, parse_reddit_url helper
- `bc-rao-api/app/services/monitoring_service.py` - MonitoringService with register_post, get_monitored_posts, get_dashboard_stats, update_post_status, run_post_audit
- `bc-rao-api/app/integrations/reddit_client.py` - RedditDualCheckClient with OAuth token caching, dual_check_post, fetch_post_metrics async methods
- `bc-rao-api/app/services/email_service.py` - send_shadowban_alert, send_success_alert, send_adjustment_alert, record_alert, can_send_shadowban_alert

**Modified:**
- `bc-rao-api/app/config.py` - Added REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET settings
- `bc-rao-api/requirements.txt` - Added resend>=2.0.0 dependency

## Decisions Made

**Reddit API approach:** Used httpx for lightweight Reddit JSON endpoint requests instead of PRAW. PRAW is a heavy dependency with full OOP wrapper we don't need. Appending `.json` to Reddit URLs gives us public data, OAuth client_credentials flow for authenticated checks.

**OAuth token caching:** Cache Reddit access tokens for 3500 seconds (100s buffer before 3600s expiry) to avoid repeated token requests on every dual-check. Stored in instance variable with expiry timestamp.

**Graceful email fallback:** Email service checks `settings.RESEND_API_KEY` and skips sends if empty (development mode). Logs warning but returns `{"status": "skipped"}` instead of crashing. Production MUST set RESEND_API_KEY.

**Rate limiting strategy:** Query `email_alerts` table for most recent emergency alert within 24h. If found, block additional shadowban alerts. Prevents alert fatigue if user has multiple posts shadowbanned in quick succession.

**Dual-check detection logic:**
- Both auth and anon see post → "active"
- Auth sees post, anon doesn't → "shadowbanned" (key detection pattern)
- Auth doesn't see post → "removed"
- Both fail → "removed"

**Draft inference:** When registering a post, query `generated_drafts` for most recent approved/posted draft matching subreddit + user + campaign within 24h. Sets `draft_id` for linking post outcome back to draft that was used.

**Account status proxy:** Subscription.plan used as proxy for determining check_interval (trial=1h, else 4h). Proper account_status tracking (New/WarmingUp/Established) deferred to future phase. Also checks most recent shadow_table entry for existing account_status.

**Audit classification:** 7-day audit classifies outcomes: Shadowbanned/Removido → "Rejection", Ativo + (10+ upvotes OR 3+ comments) → "SocialSuccess", else → "Inertia".

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added resend package to requirements.txt**
- **Found during:** Task 2 (email service creation)
- **Issue:** Import resend failed - package not in requirements.txt
- **Fix:** Added `resend>=2.0.0` to requirements.txt and ran `pip install resend`
- **Files modified:** bc-rao-api/requirements.txt
- **Verification:** Import succeeded after installation
- **Committed in:** 1c41474 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking issue)
**Impact on plan:** Auto-fix necessary to unblock email service implementation. No scope creep.

## Issues Encountered

None - all planned work executed successfully.

## User Setup Required

**External services require manual configuration.** See [USER-SETUP.md](./USER-SETUP.md) for:

- **Resend:** API key from dashboard, sender domain verification (or use onboarding domain for dev)
- **Reddit:** Create "script" app at reddit.com/prefs/apps to get client_id and client_secret
- Environment variables: RESEND_API_KEY, EMAIL_FROM, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET
- Verification commands to confirm setup

Both services must be configured before monitoring functionality works in production.

## Next Phase Readiness

**Ready for Phase 5 Plan 02 (Monitoring API Endpoints):**
- MonitoringService ready to consume via FastAPI routes
- RedditDualCheckClient ready for background worker dual-checks
- Email service ready to send alerts from worker tasks
- All models type-safe and validated

**Ready for Phase 5 Plan 03 (Background Workers):**
- dual_check_post and fetch_post_metrics methods ready for periodic tasks
- update_post_status and run_post_audit ready for worker pipeline
- record_alert ready for tracking sent emails

**No blockers.** All foundation services implemented and verified.

**Concerns:**
- Account status tracking is using subscription.plan as proxy - proper account_status field should be added to profiles table in future iteration
- Email alert metadata (check_result dict) currently logged but not persisted to database - consider adding JSONB metadata column to shadow_table for full audit trail

---
*Phase: 05-monitoring-feedback-loop*
*Completed: 2026-02-11*

## Self-Check: PASSED

All created files verified:
- ✓ bc-rao-api/app/models/monitoring.py
- ✓ bc-rao-api/app/services/monitoring_service.py
- ✓ bc-rao-api/app/integrations/reddit_client.py
- ✓ bc-rao-api/app/services/email_service.py

All commits verified:
- ✓ 7dbde83 (Task 1: monitoring models and service)
- ✓ 1c41474 (Task 2: Reddit dual-check client and email service)
