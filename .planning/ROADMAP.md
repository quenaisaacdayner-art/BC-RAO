# Roadmap: BC-RAO

## Overview

BC-RAO delivers social intelligence for Reddit marketing through a systematic 6-phase build: foundation infrastructure with auth and campaigns, followed by the core 4-module pipeline (Collect → Analyze → Generate → Monitor), and completed with billing integration. Each phase delivers a complete, verifiable capability that enables the next, progressing from basic campaign management to full behavioral mimicry with negative reinforcement learning.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation & Core Setup** - Auth, dashboard scaffold, campaign management, infrastructure
- [ ] **Phase 2: Collection Pipeline** - Module 1 with Apify scraping, regex filtering, archetype classification
- [x] **Phase 3: Pattern Engine** - Module 2 with SpaCy rhythm analysis, ISC scoring, community profiling
- [x] **Phase 4: Draft Generation** - Module 3 with conditioned generation, blacklist enforcement, ISC gating
- [ ] **Phase 5: Monitoring & Feedback Loop** - Module 4 with dual-check shadowban detection, negative reinforcement
- [ ] **Phase 6: Billing & Production Polish** - Stripe integration, usage enforcement, trial lifecycle

## Phase Details

### Phase 1: Foundation & Core Setup
**Goal**: Users can sign up, create campaigns, and navigate the dashboard with all infrastructure dependencies ready for module development.

**Depends on**: Nothing (first phase)

**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, CAMP-01, CAMP-02, CAMP-03, CAMP-04, INFR-01, INFR-02, INFR-03, INFR-04, INFR-05, INFR-06

**Success Criteria** (what must be TRUE):
  1. User can sign up with email/password and receive JWT that persists across browser refresh
  2. User can create campaigns with product context, keywords (5-15), and target subreddits
  3. User can view, edit, and delete campaigns from dashboard
  4. FastAPI backend accepts authenticated requests with Pydantic validation and returns standardized errors
  5. Celery workers and Redis broker are running and accepting tasks

**Plans**: 6 plans

Plans:
- [x] 01-01-PLAN.md — Backend foundation: DB schema + RLS, FastAPI scaffold, error handling, JWT dependency (completed 2026-02-09)
- [x] 01-02-PLAN.md — Frontend foundation: Next.js + Tailwind + Shadcn/UI, Supabase middleware, theme provider (completed 2026-02-09)
- [x] 01-03-PLAN.md — Auth system: Backend auth endpoints + frontend login/signup pages (completed 2026-02-09)
- [x] 01-04-PLAN.md — Worker infrastructure: Celery + Redis, InferenceClient, cost tracking (completed 2026-02-09)
- [ ] 01-05-PLAN.md — Campaign API + dashboard shell: CRUD endpoints, sidebar, overview page
- [ ] 01-06-PLAN.md — Campaign UI: Create form with subreddit autocomplete, list, edit, delete

---

### Phase 2: Collection Pipeline
**Goal**: System scrapes Reddit via Apify, filters posts with regex, classifies archetypes with LLM, and stores behavioral data in raw_posts table.

**Depends on**: Phase 1 (campaigns, infrastructure)

**Requirements**: COLL-01, COLL-02, COLL-03, COLL-04, COLL-05, COLL-06, COLL-07

**Success Criteria** (what must be TRUE):
  1. User can trigger data collection for a campaign and see progress tracking (total found, regex filtered, AI processed)
  2. System scrapes target subreddits via Apify with 80% local regex pre-filter before AI processing
  3. Top 10% of filtered posts are classified into archetypes (Journey/ProblemSolution/Feedback) and stored with success scores
  4. User can view collected posts filtered by archetype, subreddit, and success score
  5. Collection runs as async Celery task without blocking dashboard

**Plans**: 4 plans

Plans:
- [ ] 02-01-PLAN.md — Backend pipeline core: Apify client, regex pre-filter, collection service, raw_posts models
- [ ] 02-02-PLAN.md — Celery collection worker with progress tracking + FastAPI collection endpoints (trigger, SSE, posts query)
- [ ] 02-03-PLAN.md — Frontend collection trigger page with live SSE progress tracking
- [ ] 02-04-PLAN.md — Frontend post browsing: card grid, filters, detail modal, funnel stats + human verification

---

### Phase 3: Pattern Engine
**Goal**: System analyzes post syntax with SpaCy, calculates ISC scores per subreddit, and builds community profiles with rhythm patterns and forbidden patterns.

**Depends on**: Phase 2 (raw_posts data)

**Requirements**: PATN-01, PATN-02, PATN-03, PATN-04, PATN-05, PATN-06

**Success Criteria** (what must be TRUE):
  1. System performs local SpaCy NLP analysis on collected posts for sentence length, formality, tone, and vocabulary complexity
  2. Each subreddit has a community profile with ISC score, dominant tone, archetype distribution, and forbidden patterns
  3. User can view community profile for each target subreddit showing sensitivity level and success patterns
  4. User can view scoring breakdown for individual posts showing how vulnerability, rhythm, and penalties contributed to success score
  5. Pattern analysis runs locally via SpaCy with zero external API cost

**Plans**: 4 plans

Plans:
- [x] 03-01-PLAN.md — SpaCy NLP pipeline with custom components, post scoring algorithms, forbidden pattern extraction (completed 2026-02-11)
- [x] 03-02-PLAN.md — Analysis service, background worker with auto-trigger from collection, API endpoints for profiles/scoring/blacklist (completed 2026-02-11)
- [x] 03-03-PLAN.md — Frontend community profiles: comparison table, tabbed detail with ISC gauge and archetype chart, SSE progress (completed 2026-02-11)
- [x] 03-04-PLAN.md — Frontend analysis page with scoring breakdowns and inline penalty highlighting, blacklist management page (completed 2026-02-11)

---

### Phase 4: Draft Generation
**Goal**: Users generate conditioned drafts that match community behavioral DNA, respect blacklist constraints, and adapt to ISC sensitivity levels.

**Depends on**: Phase 3 (community_profiles, syntax_blacklist)

**Requirements**: GENR-01, GENR-02, GENR-03, GENR-04, GENR-05, GENR-06, GENR-07, GENR-08, GENR-09, DASH-01, DASH-02, DASH-03, DASH-04

**Success Criteria** (what must be TRUE):
  1. User can generate conditioned drafts by selecting subreddit, archetype, and providing optional context
  2. Generation pipeline loads community profile and syntax blacklist before building LLM prompt
  3. ISC gating blocks risky archetypes when ISC > 7.5 and forces Feedback archetype with zero links
  4. User can view, edit, approve, or discard drafts in draft editor with vulnerability and rhythm match scores displayed
  5. User can regenerate drafts with optional feedback to refine output
  6. Dashboard guides user through Project Briefing → Strategic Selection → Community Intelligence → Alchemical Transmutation stages

**Plans**: 5 plans

Plans:
- [x] 04-01-PLAN.md — Backend generation core: prompt builder, ISC gating, blacklist validator, generation service, draft models (completed 2026-02-11)
- [x] 04-02-PLAN.md — Backend API endpoints: draft generate/list/update/regenerate/delete, Celery worker, SSE streaming (completed 2026-02-11)
- [x] 04-03-PLAN.md — Frontend generation form with ISC gating UX, SSE streaming, draft list page (completed 2026-02-11)
- [x] 04-04-PLAN.md — Frontend draft editor with score sidebar, draft actions (approve/discard/regenerate/copy) (completed 2026-02-11)
- [x] 04-05-PLAN.md — Campaign stage indicator, linear progression enforcement, Stage 4 content on campaign page (completed 2026-02-11)

---

### Phase 5: Monitoring & Feedback Loop
**Goal**: System monitors posted content with dual-check shadowban detection, alerts users on removals, and feeds removal data back into blacklist for continuous learning.

**Depends on**: Phase 4 (generated_drafts)

**Requirements**: ORCH-01, ORCH-02, ORCH-03, ORCH-04, ORCH-05, ORCH-06, ORCH-07, EMAL-01, EMAL-02, EMAL-03, DASH-05, DASH-06, DASH-07

**Success Criteria** (what must be TRUE):
  1. User can register a posted draft by pasting Reddit URL and system starts monitoring with ISC snapshot
  2. System performs dual-check monitoring (authenticated + anonymous request) on schedule (4h for established, 1h for new accounts)
  3. Shadowban detected when auth returns 200 but public returns not_found for 2 consecutive checks
  4. User receives emergency email alert immediately on shadowban detection with instruction to pause 48h
  5. When post is removed, system extracts forbidden patterns and injects into syntax_blacklist per subreddit
  6. Post audit runs at 7-day mark classifying outcome as SocialSuccess, Rejection, or Inertia
  7. User can view monitoring dashboard showing active/removed/shadowbanned counts, success rate, and recent alerts
  8. Dashboard guides user through Deployment & Sentinel → Post-Audit & Loop stages

**Plans**: 4 plans

Plans:
- [ ] 05-01-PLAN.md — Backend monitoring foundation: models, service, Reddit dual-check client, email service
- [ ] 05-02-PLAN.md — Backend API endpoints, monitoring worker, scheduler, audit task, feedback loop
- [ ] 05-03-PLAN.md — Frontend monitoring dashboard: stats, post cards, filters, shadowban alert, URL registration
- [ ] 05-04-PLAN.md — Stage 5 campaign journey integration, "I posted this" button on draft editor

---

### Phase 6: Billing & Production Polish
**Goal**: Users can upgrade from trial to paid plans via Stripe, system enforces plan limits in real-time, and trial lifecycle manages conversion flow.

**Depends on**: Phase 5 (complete feature set)

**Requirements**: AUTH-05, CAMP-05, BILL-01, BILL-02, BILL-03, BILL-04, BILL-05, BILL-06, BILL-07, EMAL-04, EMAL-05, DASH-08

**Success Criteria** (what must be TRUE):
  1. User receives guided 4-step onboarding on first signup (product context → subreddits → keywords → first collection)
  2. Trial lifecycle works end-to-end: 7-day access → day-5 reminder email → day-7 expiry to read-only
  3. User can upgrade to Starter ($49/mo) or Growth ($99/mo) via Stripe checkout
  4. System enforces plan limits (subreddits, drafts/month, campaigns, monitors) with 403 errors and upgrade prompts
  5. Stripe webhooks handle subscription events (checkout completed, invoice paid/failed, subscription updated/deleted)
  6. User can view usage stats and manage subscription via Stripe customer portal
  7. Monthly usage resets on billing cycle and cost caps enforced per plan tier (80% threshold triggers warning)
  8. Dashboard displays usage stats, plan limits, and upgrade prompts

**Plans**: TBD (estimate 3-4 plans)

Plans:
- [ ] 06-01: TBD during planning
- [ ] 06-02: TBD during planning
- [ ] 06-03: TBD during planning

---

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Core Setup | 6/6 | Complete | 2026-02-09 |
| 2. Collection Pipeline | 4/4 | Complete | 2026-02-10 |
| 3. Pattern Engine | 4/4 | Complete | 2026-02-11 |
| 4. Draft Generation | 5/5 | Complete | 2026-02-11 |
| 5. Monitoring & Feedback Loop | 0/4 | Not started | - |
| 6. Billing & Production Polish | 0/TBD | Not started | - |

---
*Roadmap created: 2026-02-07*
*Last updated: 2026-02-11 (Phase 5 planned: 4 plans in 3 waves)*
