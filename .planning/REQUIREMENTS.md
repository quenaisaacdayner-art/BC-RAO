# Requirements: BC-RAO

**Defined:** 2026-02-07
**Core Value:** Founders can generate Reddit posts that survive moderation and earn genuine engagement by mimicking native community behavior patterns.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Authentication & Onboarding

- [ ] **AUTH-01**: User can sign up with email and password via Supabase Auth
- [ ] **AUTH-02**: User can log in and receive JWT that persists across browser refresh
- [ ] **AUTH-03**: User can log out from any page
- [ ] **AUTH-04**: Profile is created automatically on signup with onboarding state tracking
- [ ] **AUTH-05**: Guided onboarding (4 steps): product context, subreddit selection, keywords, first collection trigger

### Campaigns

- [ ] **CAMP-01**: User can create campaign with name, product context, product URL, keywords (5-15), and target subreddits
- [ ] **CAMP-02**: User can view list of their campaigns with stats (posts collected, drafts generated, active monitors)
- [ ] **CAMP-03**: User can edit campaign keywords, subreddits, and status (active/paused/archived)
- [ ] **CAMP-04**: User can delete a campaign (cascades to related data)
- [ ] **CAMP-05**: Campaign creation enforces plan tier limits (max campaigns per plan)

### Module 1 — Data Collector

- [ ] **COLL-01**: User can trigger data collection for a campaign (fresh/historical/hybrid mode)
- [ ] **COLL-02**: System scrapes target subreddits via Apify SDK with managed actors
- [ ] **COLL-03**: Regex pre-filter (Camada B) removes ~80% of low-quality posts locally before AI processing
- [ ] **COLL-04**: Top 10% of filtered posts are classified into archetypes (Journey/ProblemSolution/Feedback) via OpenRouter LLM
- [ ] **COLL-05**: Raw posts stored with immutable raw_text, archetype, rhythm_metadata, and success_score
- [ ] **COLL-06**: Collection runs as async Celery task with progress tracking (total found, regex filtered, AI processed)
- [ ] **COLL-07**: User can view collected posts with filtering by archetype, subreddit, and success score

### Module 2 — Pattern Engine

- [x] **PATN-01**: System performs SpaCy local NLP analysis on collected posts (sentence length, formality, tone, vocabulary complexity)
- [x] **PATN-02**: System classifies post archetypes and stores rhythm_metadata in raw_posts
- [x] **PATN-03**: System aggregates per-subreddit community profiles with ISC score, dominant tone, archetype distribution, forbidden patterns, and success hooks
- [x] **PATN-04**: System calculates post success scores using vulnerability weight, thread depth, rhythm adherence, marketing jargon penalty, and link density penalty
- [x] **PATN-05**: User can view community profile for each target subreddit (ISC, rhythm patterns, archetypes, forbidden patterns)
- [x] **PATN-06**: User can view scoring breakdown for individual posts

### Module 3 — Conditioning Generator

- [ ] **GENR-01**: User can generate conditioned drafts by selecting subreddit, archetype, and optional user context
- [ ] **GENR-02**: Generation pipeline loads community profile + syntax blacklist before building dynamic LLM prompt
- [ ] **GENR-03**: ISC gating blocks risky archetypes when ISC > 7.5 (forces Feedback with max vulnerability, zero links)
- [ ] **GENR-04**: Account status decision tree enforced (New = warm-up mode, comments only; Established = full generation)
- [ ] **GENR-05**: Post-processing validates drafts against regex blacklist, link density, sentence length, and jargon scan
- [ ] **GENR-06**: Each draft stored with archetype, vulnerability_score, rhythm_match_score, model_used, token_cost
- [ ] **GENR-07**: User can view, edit, approve, or discard generated drafts in draft editor
- [ ] **GENR-08**: User can regenerate a draft with optional feedback
- [ ] **GENR-09**: Draft generation enforces monthly plan limits (drafts/month per tier)

### Module 4 — Orchestrator

- [ ] **ORCH-01**: User can register a posted draft by pasting the Reddit URL (creates shadow table entry with ISC snapshot)
- [ ] **ORCH-02**: System performs dual-check monitoring: authenticated request (author view) + anonymous request (public view)
- [ ] **ORCH-03**: Monitoring runs on Celery Beat schedule (4h for established accounts, 1h for new accounts' first 3 posts)
- [ ] **ORCH-04**: Shadowban detected when auth=200 but public=not_found for 2 consecutive checks
- [ ] **ORCH-05**: When post is removed, system extracts forbidden patterns and injects into syntax_blacklist per subreddit
- [ ] **ORCH-06**: Post audit runs at 7-day mark classifying outcome as SocialSuccess, Rejection, or Inertia
- [ ] **ORCH-07**: Monitor slot registration enforces plan limits (monitors per tier)

### Email Alerts

- [ ] **EMAL-01**: Emergency alert sent immediately on shadowban detection with instruction to pause posting 48h
- [ ] **EMAL-02**: Success alert sent when post audit result is SocialSuccess
- [ ] **EMAL-03**: Adjustment alert sent when post audit suggests strategy pivot
- [ ] **EMAL-04**: Trial reminder email sent at day 5 with usage stats
- [ ] **EMAL-05**: Trial expiry notification at day 7 with upgrade prompt

### Billing & Usage

- [ ] **BILL-01**: Stripe checkout for Starter ($49/mo) and Growth ($99/mo) plans
- [ ] **BILL-02**: Stripe customer portal for subscription management
- [ ] **BILL-03**: Stripe webhook handling (checkout.completed, invoice.paid, invoice.failed, subscription.updated, subscription.deleted)
- [ ] **BILL-04**: Trial lifecycle: 7-day trial (no card), day-7 expiry to read-only, 30-day data retention if not converted
- [ ] **BILL-05**: Usage tracking enforces plan limits (subreddits, drafts/month, campaigns, monitors, concurrent collections)
- [ ] **BILL-06**: Cost caps enforced per plan tier (trial $5, starter $15, growth $40) — 80% threshold triggers warning
- [ ] **BILL-07**: Monthly usage resets on billing cycle (invoice.paid webhook)

### Dashboard & UX

- [ ] **DASH-01**: Project Briefing stage — user adds SaaS details, system maps ideal subreddits and scrapes conversation DNA
- [ ] **DASH-02**: Strategic Selection stage — user selects archetype ("Attack Card": Journey, Solution, Feedback), system analyzes community rules
- [ ] **DASH-03**: Community Intelligence stage — user views "Community Etiquette Manual" with ISC, ban risk level, forbidden patterns
- [ ] **DASH-04**: Alchemical Transmutation stage — user provides rough draft or leaves empty, system creates/refines post with mimicry filters
- [ ] **DASH-05**: Deployment & Sentinel stage — user copies text, posts on Reddit, pastes URL, system validates and starts monitoring
- [ ] **DASH-06**: Post-Audit & Loop stage — user tracks progress via dashboard, reads instruction emails, system evaluates success/pivot
- [ ] **DASH-07**: Monitoring dashboard showing active/removed/shadowbanned counts, success rate, recent alerts
- [ ] **DASH-08**: Usage & billing UI showing plan limits, usage stats, upgrade prompts, Stripe portal link

### Infrastructure

- [ ] **INFR-01**: Supabase PostgreSQL with pgvector extension, RLS enabled on all tenant-scoped tables
- [ ] **INFR-02**: FastAPI backend with async-first architecture, Pydantic validation, JWT middleware
- [ ] **INFR-03**: Celery + Redis worker infrastructure with separate queues (scraping, analysis, generation, monitoring)
- [ ] **INFR-04**: InferenceClient abstraction for OpenRouter with per-task model routing and fallback chains
- [ ] **INFR-05**: Cost tracking middleware that checks plan cap before every LLM call
- [ ] **INFR-06**: Standard error shape with error codes across all API endpoints

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Notifications & Engagement

- **NOTF-01**: In-app real-time notifications via Supabase Realtime
- **NOTF-02**: Email digest of weekly campaign performance

### Advanced Features

- **ADVN-01**: Semantic search UI on raw_posts using pgvector embeddings
- **ADVN-02**: A/B testing of draft variations per subreddit
- **ADVN-03**: Multi-language NLP support (additional SpaCy models)
- **ADVN-04**: OAuth login options (Google, GitHub)

### Platform Expansion

- **PLAT-01**: Hacker News support (different API/dynamics)
- **PLAT-02**: Multi-platform content adaptation (Twitter, LinkedIn)
- **PLAT-03**: Team/multi-user accounts

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Auto-posting to Reddit | ToS violation, trust anti-pattern — user must post manually |
| Real-time WebSocket dashboard | Polling every 30s is sufficient for MVP |
| Custom model fine-tuning | OpenRouter model selection covers needs |
| Mobile app | Responsive web sufficient |
| Public API / webhooks | Not needed until platform play |
| White-label / agency tier | Growth plan handles small agencies; V2 |
| Multi-account management | Reddit actively detects, legal/detection risk |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Pending |
| AUTH-02 | Phase 1 | Pending |
| AUTH-03 | Phase 1 | Pending |
| AUTH-04 | Phase 1 | Pending |
| AUTH-05 | Phase 6 | Pending |
| CAMP-01 | Phase 1 | Pending |
| CAMP-02 | Phase 1 | Pending |
| CAMP-03 | Phase 1 | Pending |
| CAMP-04 | Phase 1 | Pending |
| CAMP-05 | Phase 6 | Pending |
| COLL-01 | Phase 2 | Pending |
| COLL-02 | Phase 2 | Pending |
| COLL-03 | Phase 2 | Pending |
| COLL-04 | Phase 2 | Pending |
| COLL-05 | Phase 2 | Pending |
| COLL-06 | Phase 2 | Pending |
| COLL-07 | Phase 2 | Pending |
| PATN-01 | Phase 3 | Complete |
| PATN-02 | Phase 3 | Complete |
| PATN-03 | Phase 3 | Complete |
| PATN-04 | Phase 3 | Complete |
| PATN-05 | Phase 3 | Complete |
| PATN-06 | Phase 3 | Complete |
| GENR-01 | Phase 4 | Pending |
| GENR-02 | Phase 4 | Pending |
| GENR-03 | Phase 4 | Pending |
| GENR-04 | Phase 4 | Pending |
| GENR-05 | Phase 4 | Pending |
| GENR-06 | Phase 4 | Pending |
| GENR-07 | Phase 4 | Pending |
| GENR-08 | Phase 4 | Pending |
| GENR-09 | Phase 4 | Pending |
| ORCH-01 | Phase 5 | Pending |
| ORCH-02 | Phase 5 | Pending |
| ORCH-03 | Phase 5 | Pending |
| ORCH-04 | Phase 5 | Pending |
| ORCH-05 | Phase 5 | Pending |
| ORCH-06 | Phase 5 | Pending |
| ORCH-07 | Phase 5 | Pending |
| EMAL-01 | Phase 5 | Pending |
| EMAL-02 | Phase 5 | Pending |
| EMAL-03 | Phase 5 | Pending |
| EMAL-04 | Phase 6 | Pending |
| EMAL-05 | Phase 6 | Pending |
| BILL-01 | Phase 6 | Pending |
| BILL-02 | Phase 6 | Pending |
| BILL-03 | Phase 6 | Pending |
| BILL-04 | Phase 6 | Pending |
| BILL-05 | Phase 6 | Pending |
| BILL-06 | Phase 6 | Pending |
| BILL-07 | Phase 6 | Pending |
| DASH-01 | Phase 4 | Pending |
| DASH-02 | Phase 4 | Pending |
| DASH-03 | Phase 4 | Pending |
| DASH-04 | Phase 4 | Pending |
| DASH-05 | Phase 5 | Pending |
| DASH-06 | Phase 5 | Pending |
| DASH-07 | Phase 5 | Pending |
| DASH-08 | Phase 6 | Pending |
| INFR-01 | Phase 1 | Pending |
| INFR-02 | Phase 1 | Pending |
| INFR-03 | Phase 1 | Pending |
| INFR-04 | Phase 1 | Pending |
| INFR-05 | Phase 1 | Pending |
| INFR-06 | Phase 1 | Pending |

**Coverage:**
- v1 requirements: 60 total
- Mapped to phases: 60
- Unmapped: 0

**Coverage by phase:**
- Phase 1 (Foundation & Core Setup): 14 requirements
- Phase 2 (Collection Pipeline): 7 requirements
- Phase 3 (Pattern Engine): 6 requirements
- Phase 4 (Draft Generation): 13 requirements
- Phase 5 (Monitoring & Feedback Loop): 10 requirements
- Phase 6 (Billing & Production Polish): 10 requirements

---
*Requirements defined: 2026-02-07*
*Last updated: 2026-02-07 after roadmap creation - 100% coverage achieved*
