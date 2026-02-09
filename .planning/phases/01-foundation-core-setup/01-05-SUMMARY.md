---
phase: 01-foundation-core-setup
plan: 05
subsystem: api-and-ui
tags: [fastapi, pydantic, nextjs, shadcn-ui, campaigns, dashboard, sidebar, dark-mode]
requires:
  - phase: 01-01
    provides: JWT auth middleware, error handling, Supabase client, campaigns table
  - phase: 01-02
    provides: Next.js structure, Shadcn UI components, theme provider
  - phase: 01-03
    provides: Auth system with server-side auth checking
affects:
  - 01-06 (campaign form will use these API endpoints)
  - phase-02 (collector will reference campaigns)
  - phase-03 (analyzer will work with campaign data)
  - phase-04 (generator will create drafts for campaigns)
tech-stack:
  added: []
  patterns:
    - pydantic validation with min/max constraints for campaign fields
    - supabase crud service pattern with error handling
    - collapsible sidebar with icon-only mode
    - conditional empty state rendering
    - server-side auth check with redirect pattern
key-files:
  created:
    - bc-rao-api/app/models/campaign.py
    - bc-rao-api/app/services/campaign_service.py
    - bc-rao-api/app/api/v1/campaigns.py
    - bc-rao-frontend/app/(dashboard)/layout.tsx
    - bc-rao-frontend/app/(dashboard)/page.tsx
    - bc-rao-frontend/components/sidebar/app-sidebar.tsx
    - bc-rao-frontend/components/sidebar/nav-items.ts
  modified:
    - bc-rao-api/app/api/v1/router.py
key-decisions:
  - decision: Campaign stats use placeholder zeros until collection phases
    rationale: Collector (Phase 2) and analyzer (Phase 3) will populate real data
    impact: Stats display but show zeros until future phases
  - decision: Overview page conditionally shows empty state vs stats
    rationale: Better UX for new users, professional onboarding experience
    impact: Zero-campaign state prompts user to create first campaign
  - decision: Sidebar uses collapsible icon mode per user requirements
    rationale: Balances screen space with navigation clarity
    impact: Users can toggle between full and icon-only sidebar
patterns-established:
  - "Campaign service pattern: Service class with create/list/get/update/delete using Supabase client"
  - "Auth-protected endpoints: All campaign endpoints require get_current_user dependency"
  - "Empty state handling: Conditional rendering based on data presence"
  - "Dashboard layout: SidebarProvider wrapping AppSidebar + main content"
duration: 5 minutes
completed: 2026-02-09
---

# Phase 01 Plan 05: Campaign API and Dashboard Shell Summary

**One-liner:** Complete campaign CRUD API with validation (5-15 keywords, min 1 subreddit) and professional dashboard shell with collapsible sidebar, dark/light mode toggle, user menu with logout, and overview page with empty state handling.

## Performance

**Execution time:** 5 minutes (327 seconds)
**Tasks completed:** 2/2 (100%)
**Commits:** 2 atomic commits (1 per task)

## Accomplishments

### Task 1: Campaign CRUD API — models, service, endpoints
- Created campaign models with Pydantic validation:
  - CampaignCreate: name (1-100 chars), product_context (min 10), keywords (5-15 items), target_subreddits (min 1)
  - CampaignUpdate: all fields optional with same validation when provided
  - CampaignResponse: full campaign data with timestamps
  - CampaignWithStats: extends response with stats dict (posts_collected, drafts_generated, active_monitors)
  - CampaignListResponse: campaigns array with total count
- Implemented CampaignService with full CRUD operations:
  - create: inserts with user_id, defaults status to "active"
  - list_for_user: returns user's campaigns ordered by created_at desc
  - get_by_id: fetches single campaign with stats (placeholder zeros)
  - update: validates ownership, applies partial updates
  - delete: validates ownership before deletion
- Built campaigns API endpoints at `/v1/campaigns`:
  - POST / → 201 (create)
  - GET / → 200 (list)
  - GET /{id} → 200 (get with stats)
  - PATCH /{id} → 200 (update)
  - DELETE /{id} → 204 (delete)
- All endpoints require JWT authentication via get_current_user dependency
- Proper AppError handling for not found, validation errors, and server errors
- Registered campaigns router in v1 router

### Task 2: Dashboard shell — sidebar, layout, overview page
- Created navigation structure:
  - nav-items.ts: Overview (LayoutDashboard icon) and Campaigns (Target icon) with future phase items commented
- Built collapsible AppSidebar component:
  - Header with "BC-RAO" branding
  - Navigation menu with active state via usePathname()
  - Footer with dark/light mode toggle (Sun/Moon icons)
  - User menu dropdown with logout functionality (calls supabase.auth.signOut, redirects to /login)
  - Full icon-only collapse mode using Shadcn Sidebar `collapsible="icon"`
- Implemented dashboard layout:
  - Server-side auth check with redirect to /login if unauthenticated
  - SidebarProvider wrapping AppSidebar + SidebarInset
  - Header with SidebarTrigger and "Dashboard" title
  - Main content area with padding and gap
- Created overview page with conditional rendering:
  - Zero campaigns: centered card with "Welcome to BC-RAO" title, "Create a campaign to start collecting community data" message, "Create Campaign" CTA button linking to /dashboard/campaigns/new
  - With campaigns: grid of summary cards (Total Campaigns, Recent Activity, Quick Actions)
- Professional Vercel dashboard aesthetic with balanced info density
- No emojis, direct tone per user requirements

## Task Commits

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 1 | Campaign CRUD API with models, service, and endpoints | d0a7bb1 | bc-rao-api/app/models/campaign.py, bc-rao-api/app/services/campaign_service.py, bc-rao-api/app/api/v1/campaigns.py, bc-rao-api/app/api/v1/router.py |
| 2 | Dashboard shell with collapsible sidebar and overview page | 4973068 | bc-rao-frontend/app/(dashboard)/layout.tsx, bc-rao-frontend/app/(dashboard)/page.tsx, bc-rao-frontend/components/sidebar/app-sidebar.tsx, bc-rao-frontend/components/sidebar/nav-items.ts |

## Files Created

**Backend API:**
- bc-rao-api/app/models/campaign.py (63 lines) - Pydantic models for campaign CRUD
- bc-rao-api/app/services/campaign_service.py (203 lines) - CampaignService with Supabase operations
- bc-rao-api/app/api/v1/campaigns.py (131 lines) - Campaign REST endpoints

**Frontend Dashboard:**
- bc-rao-frontend/app/(dashboard)/layout.tsx (35 lines) - Auth-protected dashboard layout
- bc-rao-frontend/app/(dashboard)/page.tsx (75 lines) - Overview page with empty state
- bc-rao-frontend/components/sidebar/app-sidebar.tsx (107 lines) - Collapsible sidebar with theme toggle and logout
- bc-rao-frontend/components/sidebar/nav-items.ts (22 lines) - Navigation items definition

## Files Modified

- bc-rao-api/app/api/v1/router.py - Added campaigns router import and registration

## Decisions Made

1. **Campaign stats use placeholder zeros until collection phases**
   - **Context:** CampaignWithStats includes posts_collected, drafts_generated, active_monitors
   - **Decision:** Return zeros for all stats fields in get_by_id endpoint
   - **Rationale:** Collector (Phase 2), analyzer (Phase 3), and monitor (Phase 5) will populate real data - no point in fake data
   - **Impact:** Stats display correctly but show zeros until future phases implement collection/analysis
   - **Alternatives considered:** Removing stats field entirely (decided against - better to show placeholder than change API contract later)

2. **Overview page conditionally shows empty state vs stats**
   - **Context:** New users with zero campaigns should see clear next steps
   - **Decision:** Render centered welcome card with CTA when campaignCount === 0, otherwise show stats grid
   - **Rationale:** Better UX for new users, professional onboarding experience, reduces friction
   - **Impact:** Zero-campaign state prompts user to create first campaign with clear action button
   - **Alternatives considered:** Always showing stats grid with zeros (confusing for new users)

3. **Sidebar uses collapsible icon mode per user requirements**
   - **Context:** User locked decision: "Collapsible left sidebar with icons + labels (collapses to icon-only)"
   - **Decision:** Implemented with Shadcn Sidebar `collapsible="icon"` prop
   - **Rationale:** Balances screen space with navigation clarity, matches Vercel dashboard style
   - **Impact:** Users can toggle between full sidebar (icon + label) and compact (icon only)
   - **Alternatives considered:** Always-expanded or offcanvas pattern (user already decided)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. All tasks completed successfully with no blocking issues.

## User Setup Required

None - no external service configuration required for this plan.

## Next Phase Readiness

### Ready for next plans

**01-06 (Campaign form + API integration):**
- Campaign API endpoints ready: POST /v1/campaigns for creation
- Campaign models with validation ready for form integration
- Dashboard layout established for /dashboard/campaigns/new route
- Empty state on overview page links to /dashboard/campaigns/new

**Phase 02 (Data collection):**
- Campaigns table schema ready with target_subreddits, keywords fields
- Campaign service pattern established for worker integration
- Campaign stats placeholders ready to receive real data

**Phase 03 (Analysis):**
- Campaign stats structure established (posts_collected field ready)
- Campaign detail endpoint returns stats for analysis dashboard

**Phase 04 (Generation):**
- Campaign context (product_context, keywords) accessible via API
- Campaign stats include drafts_generated field for tracking

### Blockers

None. All dependencies resolved.

### Technical notes

1. **Campaign validation enforces 5-15 keywords**
   - Current: Pydantic Field with min_length=5, max_length=15
   - Rationale: Per system spec, prevents too narrow or too broad targeting
   - Impact: Form in 01-06 must enforce same constraint client-side

2. **Dashboard route groups use (dashboard) pattern**
   - Current: app/(dashboard)/ for all dashboard routes
   - Rationale: Next.js convention for route grouping without affecting URL structure
   - Impact: All future dashboard routes should use this pattern

3. **Logout uses client-side Supabase SDK**
   - Current: AppSidebar calls createClient().auth.signOut()
   - Rationale: Simpler than backend proxy, works with SSR token refresh via middleware
   - Impact: Middleware handles token cleanup automatically

## Self-Check: PASSED

All created files exist:
- bc-rao-api/app/models/campaign.py ✓
- bc-rao-api/app/services/campaign_service.py ✓
- bc-rao-api/app/api/v1/campaigns.py ✓
- bc-rao-frontend/app/(dashboard)/layout.tsx ✓
- bc-rao-frontend/app/(dashboard)/page.tsx ✓
- bc-rao-frontend/components/sidebar/app-sidebar.tsx ✓
- bc-rao-frontend/components/sidebar/nav-items.ts ✓

All commits exist:
- d0a7bb1 ✓
- 4973068 ✓
