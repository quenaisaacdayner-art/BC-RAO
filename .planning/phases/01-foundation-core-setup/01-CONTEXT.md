# Phase 1: Foundation & Core Setup - Context

**Gathered:** 2026-02-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can sign up with email/password, create campaigns with product context, keywords, and target subreddits, and navigate a dashboard shell. All infrastructure dependencies (FastAPI, Celery, Redis, Supabase with RLS) are ready for module development in Phase 2+. Auth, campaign CRUD, and the dashboard scaffold are the deliverables. No module pipelines (collection, analysis, generation, monitoring) are built here.

</domain>

<decisions>
## Implementation Decisions

### Dashboard shell & navigation
- Collapsible left sidebar with icons + labels (collapses to icon-only)
- Main landing page is an overview page with summary stats (campaign count, recent activity, quick actions)
- Campaigns live on a separate page accessible from sidebar
- Balanced information density — cards with enough info to be useful, not overwhelming (Vercel dashboard style)
- Dark/light mode toggle supported from the start

### Campaign creation flow
- Single page form with all fields visible: name, product context, product URL, keywords, target subreddits
- Subreddit input uses search + autocomplete that queries Reddit for matching subreddits as user types
- Keyword input is a textarea with comma-separated values; system splits and validates count (5-15 required)
- Post-creation redirect: Claude's discretion (campaign detail page or list with toast)

### Empty states & first-run experience
- Zero campaigns state: quick-start card that explains what campaigns are + CTA to create first one
- Overview page hides stats sections entirely until real data exists (no skeleton/placeholder metrics)
- Tone is professional and direct — "Create a campaign to start collecting community data." No fluff, no emoji
- Campaign list cards show stats inline with zeros (Posts: 0 | Drafts: 0 | Monitors: 0) to preview what modules will deliver

### Claude's Discretion
- Post-campaign-creation redirect behavior
- Sidebar section grouping and icon choices
- Loading skeleton design and transition animations
- Exact form layout and field ordering within the single-page campaign form
- Error state styling (toast vs inline vs modal)
- Overview page layout and widget arrangement

</decisions>

<specifics>
## Specific Ideas

- Dashboard should feel like Vercel's dashboard — balanced, modern, not cluttered
- Sidebar pattern similar to Linear or Notion (collapsible, icon-only mode)
- Campaign stats showing zeros is intentional — sets user expectation for the full pipeline (Collect > Analyze > Generate > Monitor)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation-core-setup*
*Context gathered: 2026-02-07*
