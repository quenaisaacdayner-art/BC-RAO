# Project Research Summary

**Project:** BC-RAO - Reddit Content Generation Tool
**Domain:** Reddit Marketing Automation / AI-Powered Community Engagement
**Researched:** 2026-02-07
**Confidence:** HIGH

## Executive Summary

BC-RAO is a Reddit marketing automation tool for SaaS founders that generates community-native content to avoid AI detection and shadowbans. The research reveals this is a high-risk, high-value domain where the primary challenge is not technical complexity but navigating Reddit's sophisticated bot detection, community norms, and TOS compliance. Success depends on three pillars: (1) authentic content mimicry through NLP analysis of community patterns, (2) proactive ban risk assessment before posting, and (3) strict adherence to Reddit's API limits and anti-spam policies.

The recommended approach is an event-driven async pipeline built on Next.js 16 + FastAPI + Celery + Supabase. Four core modules handle the lifecycle: Collector (scrape Reddit via Apify), Pattern Engine (SpaCy NLP for "Conversation DNA"), Generator (LLM with mimicry constraints via OpenRouter), and Monitor (shadowban detection + engagement tracking). The architecture must prioritize resilience over speed—tasks are long-running (1-5 minutes for scraping), users must review content before posting (no full automation), and community profiles require weekly refreshes to avoid staleness.

Critical risks include shadowbans from AI-detected content (70-90% risk for new accounts), Reddit API bans from rate limit violations, Supabase RLS security breaches (170+ apps compromised in 2026), and LLM cost explosion from inefficient prompts. Mitigation requires security-first development (RLS enabled from day 1), multi-layer content safety (blacklist + LLM moderation + human review), aggressive cost controls (prompt caching, model routing), and honest UX about Reddit's barriers (account age/karma requirements).

## Key Findings

### Recommended Stack

The stack is optimized for async background processing with strong type safety and cost control. Next.js 16 + Vercel handles the frontend with native React Server Components. FastAPI + Railway provides the backend API and Celery workers (Redis broker) for long-running tasks. Supabase delivers PostgreSQL + Auth + Realtime subscriptions with Row Level Security. OpenRouter routes LLM requests across 300+ models with cost-based selection and prompt caching.

**Core technologies:**
- **Next.js 16** (frontend): React 19 Server Components, ISR for dashboards, Edge Functions for auth — native Vercel integration
- **FastAPI 0.128.2** (backend): Async-first API framework, automatic OpenAPI generation for type-safe monorepo, Pydantic v2 validation
- **Celery 5.6** (task queue): Industry standard for distributed async tasks, Redis broker, Beat scheduler for monitoring jobs
- **SpaCy 3.8** (NLP): Production-grade text analysis (tokenization, POS tagging, dependency parsing) for rhythm analysis — model `en_core_web_md` balances accuracy/speed
- **Supabase** (database): PostgreSQL 15+ with RLS, built-in auth, realtime subscriptions — critical for security and live updates
- **OpenRouter** (LLM gateway): Multi-model routing (Claude 3.5 Sonnet → GPT-4 → Llama 3), prompt caching (0.25x cost), cost limits
- **Apify** (Reddit scraping): Unlimited scraping without login, structured data extraction, avoids direct Reddit API rate limits for collection
- **Redis 7.x** (broker + cache): Dual-purpose for Celery task queue and caching community profiles
- **Turborepo** (monorepo): Optimizes Next.js + FastAPI builds, intelligent caching, parallel task execution

**Critical version notes:**
- FastAPI 0.126+ requires Pydantic v2 (v1 support dropped)
- Python 3.11 recommended (FastAPI requires 3.9+, Celery supports 3.9-3.13)
- OpenRouter SDK is beta — pin version to avoid breaking changes
- Avoid Python 3.8 (FastAPI dropped support), Requests library (use httpx for async), Jest (use Vitest)

### Expected Features

Research identified clear table stakes vs. differentiators. Competitors (GummySearch, Subreddit Signals, ReplyAgent, Redreach) focus on monitoring/discovery OR managed accounts, but none combine content generation + ban risk intelligence + community mimicry.

**Must have (table stakes):**
- **Subreddit Discovery** — users expect intelligent filtering by ICP match, engagement quality (free tools like SubredditStats set baseline)
- **Keyword/Topic Monitoring** — real-time alerts for brand mentions (F5Bot offers this free, must exceed)
- **Rules Checking** — Reddit now has native "Rule Check" feature, must beat it by explaining why rules apply and predicting mod behavior
- **Engagement Analytics** — post-publication tracking (upvotes, comments, upvote ratio) to validate what works
- **Shadowban Detection** — 70-90% ban risk makes this critical; multiple free checkers exist (ShadowBan, PixelScan)
- **Basic Post Scheduling** — standard in all marketing tools (Postpone, Redreach already offer)
- **Multi-Subreddit Management** — SaaS founders promote across 5-15 communities, need dashboard view

**Should have (competitive advantage):**
- **Community Etiquette Manual + CSI Score** — BC-RAO's unique differentiator: quantifies ban risk per subreddit by analyzing mod behavior, enforcement patterns, sensitivity triggers
- **Conversation DNA Scraping & Mimicry** — analyze top posts to extract linguistic fingerprints (sentence rhythm, tone, vocabulary), apply to generation for 100% human-feel
- **Attack Card Strategy Framework** — Journey/Solution/Feedback/Custom cards educate users on Reddit-native promotion patterns
- **Ban Risk Prediction** — combine CSI + content analysis + timing + account history to estimate probability ("72% chance this gets removed")
- **Draft Refinement Mode** — user provides rough draft, system applies mimicry filters to preserve authenticity while reducing ban triggers
- **Purchase Intent Scoring** — AI estimates user likelihood to buy based on language/context, prioritizes high-intent threads
- **Cross-Post Optimization** — adjust tone, framing, timing per community (one draft → 5 community-specific versions)

**Defer (v2+):**
- **Managed Account Network** — ReplyAgent charges $3/post using karma-aged accounts; eliminates warmup but requires major infrastructure + legal review
- **Multi-Platform Support** — LinkedIn, X, HN expansion only after Reddit mastery proven (different dynamics, dilutes focus)
- **Karma Farming Automation** — violates Reddit TOS, creates legal/ethical risk; instead educate users on manual warming best practices
- **Fully Automated Posting** — removes human oversight, triggers AI detection + community backlash; keep human in loop

**Anti-features (avoid):**
- **Mass Cross-Posting Same Content** — Reddit flags as spam
- **Comment Auto-Replies** — users detect and hate automated responses
- **AI Detection Evasion Tools** — arms race mentality; better to focus on genuine authenticity

### Architecture Approach

Event-driven async pipeline where each module triggers the next via Celery tasks, with state persisted to PostgreSQL between stages. This is the standard pattern for long-running multi-stage data processing where failures must be isolated and retryable.

**Major components:**
1. **Frontend (Next.js 16 on Vercel)** — Server Components for SEO/data fetching, Client Components for interactivity, real-time updates via Supabase subscriptions
2. **API Gateway (FastAPI on Railway)** — HTTP endpoints for CRUD operations, orchestrates Celery tasks, enforces plan limits
3. **Task Queue (Celery + Redis)** — Async job execution with specialized queues (scraping: I/O-bound high concurrency, NLP: CPU-bound low concurrency, generation: API-bound medium concurrency)
4. **Module 1: Collector** — Apify scrapes Reddit → Regex archetype classifier → AI confidence scorer → stores raw_posts table
5. **Module 2: Pattern Engine** — SpaCy NLP analysis → rhythm scoring (sentence length, clause density) → calculate ISC (Influence Style Coefficient) → stores community_profiles table
6. **Module 3: Generator** — RAG pattern (retrieve top posts as context) → check syntax blacklist → LLM generation via OpenRouter → mimicry filters (ISC match, tone calibration) → stores generated_drafts table
7. **Module 4: Monitor** — Celery Beat scheduler (every 4h) → Reddit API fetch metrics → shadowban heuristics → alert on degradation
8. **Database (Supabase)** — PostgreSQL with RLS policies (critical security requirement), auth integration, real-time subscriptions for live UI updates

**Key patterns:**
- **Event-Driven Pipeline:** Collection → Analysis → Generation triggered via Celery chains, user gets immediate response ("Campaign started, we'll notify when ready")
- **RAG for Context:** LLM generation retrieves successful post examples from database, injects into prompt to ground mimicry in real patterns
- **Worker Pool Routing:** Specialized queues optimize resources (scraping gets 10 workers, NLP gets 2 CPU-optimized, generation gets 4)
- **Push-Based Updates:** Supabase Realtime (PostgreSQL LISTEN/NOTIFY) for UI state changes, not database polling

**Critical anti-patterns to avoid:**
- Synchronous API calls in HTTP endpoints (causes timeouts)
- Loading SpaCy model on every request (2-3s latency, should load once at startup)
- Storing raw Reddit JSON in database (causes bloat, use structured columns)
- Polling database for task status (use Supabase Realtime push-based updates)
- Generating content without blacklist enforcement (wastes credits, risks bans)

### Critical Pitfalls

These are domain-specific risks beyond standard web development mistakes. Each has caused production failures in similar tools.

1. **Disabled Row Level Security (RLS) on Supabase** — The #1 security breach cause in Supabase apps. Moltbook incident (Jan 2026) exposed 1.5M API keys because RLS was disabled. Must enable RLS immediately when creating tables, create policies before adding production data, never use service_role keys in client code. Test with different user roles before deployment. Address in Phase 1 (Foundation) — non-negotiable.

2. **AI Content Detection Leading to Shadowbans** — Reddit's bot detection identifies LLM patterns at token level (statistical word choice, sentence structures). 15% of Reddit posts are AI-generated, moderators use heuristics to detect "tells." Avoid by never using raw LLM output, adopt varied sentence rhythm, use creative essayist style (84% bypass rate vs. 7% for standard generation), test with GPTZero before posting. Address in Phase 2 (Content Generation) and Phase 4 (Safety & Quality).

3. **Reddit API/TOS Violations Through Automated Posting** — Reddit pursued legal action against Perplexity for scraping. Rules prohibit posting identical content across subreddits, automated spam, scraping without consent. Avoid by using official API with OAuth, respecting 60 requests/minute rate limit, unique content per subreddit, following 10% self-promotion rule, building organic karma first, adding human review before posting. Address in Phase 1 (Foundation) and Phase 3 (Attack Cards & Posting).

4. **Unreliable Shadowban Detection** — All three states (shadowban, suspension, deleted account) look identical to outside observers. Reddit doesn't notify users of shadowbans. Must implement multi-method detection: check profile when logged out, monitor engagement metrics, use Reddit Shadowban Checker tool, check post visibility in incognito mode. Set automated alerts for zero-engagement posts. Address in Phase 4 (Safety & Quality) and Phase 5 (Monitoring).

5. **Data Staleness in Community Profiles** — Reddit content changes rapidly (weekly/daily shifts in tone, memes, trending topics, mod policies). One-time scraping produces "off" content that gets detected. Avoid by implementing freshness tracking (timestamp all scraped data), re-scrape high-priority subreddits weekly, flag stale profiles (>30 days), prioritize recent posts in analysis, allow manual refresh before posting. Address in Phase 2 (NLP Analysis) and Phase 5 (Monitoring).

**Additional critical pitfalls:**
- **Celery Worker Failures During Railway Deployments** — Long tasks interrupted during deploys, causing data loss. Configure `RAILWAY_DEPLOYMENT_OVERLAP_SECONDS` and `DRAINING_SECONDS` for graceful shutdown.
- **LLM Cost Explosion** — Prompts routinely exceed 20K tokens without optimization. Implement prompt caching (0.25x cost), compression (LLMLingua: 20x), max price limits, model routing for simple tasks.
- **Reddit Rate Limit Violations** — 60 requests/minute with 10-minute rolling window. Burst scraping triggers bans. Use client-side rate limiting, exponential backoff on 429 errors, queue requests through Celery.
- **Karma/Account Age Filtering** — New accounts auto-filtered by most subreddits (50-500 karma, 30+ days required). Build account readiness checker in onboarding, educate on warming strategy, show estimated readiness per subreddit.

## Implications for Roadmap

Based on research, the roadmap must follow a strict dependency chain: Auth → Module 1 (Collector) → Module 2 (Pattern Engine) → Module 3 (Generator) → Module 4 (Monitor). Each module requires data from the previous, and security/compliance must be built from day 1 (not retrofitted).

### Phase 1: Foundation & Security
**Rationale:** RLS security, Reddit API compliance, and Celery infrastructure are prerequisites for all other work. The research shows that 170+ apps were compromised in 2026 by skipping RLS setup, and Reddit actively pursues legal action for TOS violations. Building on an insecure or non-compliant foundation requires complete rebuilds later.

**Delivers:**
- Supabase database with RLS enabled on all tables
- FastAPI app with auth middleware and plan limit enforcement
- Celery + Redis configured with graceful shutdown for Railway
- Next.js frontend with Supabase auth integration
- Reddit API OAuth flow with rate limiting infrastructure

**Addresses (from FEATURES.md):**
- Authentication (table stakes for SaaS)
- Plan limit enforcement (prevents cost explosion)

**Avoids (from PITFALLS.md):**
- Pitfall #1: Disabled RLS (must be enabled before any user data)
- Pitfall #3: Reddit API/TOS violations (OAuth + rate limiting from start)
- Pitfall #6: Celery worker failures (graceful shutdown configured)
- Pitfall #8: Rate limit violations (client-side rate limiting built in)

**Stack elements (from STACK.md):**
- Supabase (PostgreSQL + Auth + RLS)
- FastAPI (API framework)
- Celery + Redis (task queue)
- Next.js (frontend framework)

### Phase 2: Module 1 - Collection & Classification
**Rationale:** Cannot analyze community patterns or generate content without data. Module 1 provides the raw material (Reddit posts) for all downstream processing. Research shows Apify integration is the de-risking priority (validates data structure before building analysis pipeline).

**Delivers:**
- Apify client integration for Reddit scraping
- Regex-based archetype classification (Journey, Solution, Feedback, Custom)
- AI-powered classification confidence scoring (OpenRouter)
- Celery task: collect_posts (1-5 minute async job)
- Frontend: Campaign creation form with subreddit discovery

**Addresses (from FEATURES.md):**
- Subreddit Discovery (table stakes)
- Conversation DNA Scraping (differentiator)
- Attack Card data foundation (archetypes feed card selection)

**Avoids (from PITFALLS.md):**
- Pitfall #8: Rate limit violations (scraping queued through Celery, distributed over time)

**Stack elements (from STACK.md):**
- Apify Client (Reddit scraping)
- OpenRouter (AI classification)
- Celery (async task execution)

**Architecture components (from ARCHITECTURE.md):**
- Module 1: Collector (Apify API → Regex filter → AI classifier → raw_posts table)

### Phase 3: Module 2 - Pattern Engine (NLP Analysis)
**Rationale:** Conversation DNA is BC-RAO's core differentiator. Without NLP analysis of community linguistic patterns, the tool becomes a generic AI writer (no competitive advantage). Research shows SpaCy rhythm analysis requires validation with 100+ real posts to tune the weight matrix.

**Delivers:**
- SpaCy NLP pipeline integration (model loaded at startup)
- Rhythm analyzer (sentence length, clause density, transitional patterns)
- Scoring engine (ISC = Influence Style Coefficient, 0-10 scale)
- Community profiler (aggregates metrics, identifies dominant tone)
- Celery task: analyze_patterns
- Frontend: Community profile display (ISC score, rhythm metrics, top hooks)

**Addresses (from FEATURES.md):**
- Conversation DNA Scraping (differentiator)
- Community Etiquette Manual (requires pattern analysis)

**Avoids (from PITFALLS.md):**
- Pitfall #5: Data staleness (implement freshness tracking from start)

**Stack elements (from STACK.md):**
- SpaCy 3.8 (NLP analysis)
- Sentence Transformers (semantic similarity for pattern matching)
- scikit-learn (TF-IDF + cosine similarity)

**Architecture components (from ARCHITECTURE.md):**
- Module 2: Pattern Engine (SpaCy pipeline → Rhythm analysis → ISC calculation → community_profiles table)
- Anti-pattern avoidance: Load SpaCy model once at startup, not per request

### Phase 4: Module 3 - Content Generation & Safety
**Rationale:** Generation is the primary user-facing feature, but research shows 70-90% shadowban risk if content is detected as AI. Multi-layer safety (blacklist + LLM moderation + human review) must be built into generation from day 1, not added later.

**Delivers:**
- OpenRouter LLM client with cost controls (prompt caching, max price limits, model routing)
- RAG retrieval (fetch top posts as context for mimicry)
- Syntax blacklist checker (pre-generation validation)
- Mimicry filters (post-generation ISC matching, tone calibration)
- Attack Card framework implementation (Journey/Solution/Feedback/Custom)
- Ban Risk Prediction score (CSI + content + timing + account history)
- Celery task: generate_draft
- Frontend: Draft editor with preview, refinement mode, ban risk display

**Addresses (from FEATURES.md):**
- Attack Card Strategy Framework (differentiator)
- Mimicry Quality Filters (differentiator)
- Ban Risk Prediction (differentiator)
- Draft Refinement Mode (differentiator)
- Enhanced Rules Checking (table stakes)

**Avoids (from PITFALLS.md):**
- Pitfall #2: AI content detection (mimicry filters + human editing required)
- Pitfall #7: LLM cost explosion (caching + compression + price limits)
- Pitfall #9: Blacklist ineffectiveness (multi-layer safety: keywords + LLM + human)

**Stack elements (from STACK.md):**
- OpenRouter (LLM gateway with cost controls)
- Sentence Transformers (semantic similarity for RAG retrieval)
- Pydantic (validation for blacklist rules)

**Architecture components (from ARCHITECTURE.md):**
- Module 3: Generator (RAG retrieval → Blacklist check → LLM generation → Mimicry filters → generated_drafts table)
- RAG pattern: Retrieve top posts → Inject into prompt → Generate with context

### Phase 5: Module 4 - Monitoring & Shadowban Detection
**Rationale:** Silent failures (shadowbans) destroy user trust. Research shows shadowbans, suspensions, and deleted accounts look identical to outside observers, requiring multi-method detection. Monitoring validates the effectiveness of earlier safety measures.

**Delivers:**
- Reddit API client (PRAW) for post metrics
- Multi-method shadowban detection (profile accessibility, engagement heuristics, Reddit Shadowban Checker integration)
- Alert service (Resend for email notifications)
- Celery Beat scheduler (periodic checks every 4 hours)
- Celery task: check_post_status
- Frontend: Monitoring dashboard (post health, engagement trends, shadowban alerts)

**Addresses (from FEATURES.md):**
- Shadowban Detection/Alerts (table stakes)
- Engagement Analytics (table stakes)
- Post URL Monitoring (v1.x feature)

**Avoids (from PITFALLS.md):**
- Pitfall #4: Unreliable shadowban detection (multi-method approach)
- Pitfall #5: Data staleness (monitoring triggers profile refresh when community changes detected)

**Stack elements (from STACK.md):**
- Celery Beat (scheduler for periodic tasks)
- Resend (email API for alerts)
- Redis (rate limiting for Reddit API calls)

**Architecture components (from ARCHITECTURE.md):**
- Module 4: Monitor (Periodic checks → Fetch metrics → Shadowban heuristics → Alert on degradation)

### Phase 6: Billing & Usage Tracking
**Rationale:** Can be built in parallel with Module 4 (no dependency). Research shows per-user token budgets are critical to prevent LLM cost explosion. Stripe integration follows standard SaaS patterns (well-documented, low risk).

**Delivers:**
- Stripe integration (checkout, webhooks, subscription management)
- Usage tracking service (tokens per user, scraping quota, generation count)
- Plan limit enforcement middleware (enforced at API layer)
- Billing API endpoints (upgrade, downgrade, cancel)
- Frontend: Billing settings, usage meters, upgrade prompts

**Addresses (from FEATURES.md):**
- Freemium pricing model (business requirement)

**Avoids (from PITFALLS.md):**
- Pitfall #7: LLM cost explosion (per-user token budgets aligned with plan limits)

**Stack elements (from STACK.md):**
- Stripe SDK (payment processing)

### Phase Ordering Rationale

**Dependency chain (critical path):** Foundation → Module 1 → Module 2 → Module 3 → Module 4 takes 10-12 weeks. Each module requires data from the previous:
- Module 1 needs Foundation (auth, Celery, database)
- Module 2 needs Module 1 (raw_posts to analyze)
- Module 3 needs Module 2 (community_profiles for mimicry)
- Module 4 needs Module 3 (approved drafts to monitor)

**Parallelization opportunities:**
- Frontend UI development can occur alongside backend services within each phase
- Phase 6 (Billing) can be built in parallel with Phase 5 (Monitoring) — no dependency
- Testing can occur continuously (unit tests per module, integration tests after each phase)

**De-risking timeline:**
- Week 3 (after Phase 1): Validate Apify integration with real Reddit data before building analysis pipeline
- Week 5 (after Phase 2): Validate SpaCy NLP accuracy with 100+ posts, tune weight matrix before generation depends on it
- Week 7 (after Phase 3): Human evaluation of 50 generated drafts, iterate on prompt engineering before users see output
- Week 9 (after Phase 4): Test shadowban detection with known shadowbanned accounts, refine heuristics

**Security-first philosophy:** Research shows retrofitting RLS, rate limiting, and compliance is expensive (complete rebuilds). Build foundation correctly in Phase 1, validate with security scanners before proceeding to Phase 2.

### Research Flags

**Phases likely needing deeper research during planning:**
- **Phase 3 (Module 2 - Pattern Engine):** SpaCy weight matrix tuning is domain-specific, sparse documentation on "conversation DNA" extraction. Needs iterative experimentation with Reddit data to validate ISC scoring accuracy.
- **Phase 4 (Module 3 - Generation):** LLM prompt engineering for mimicry is evolving rapidly (OpenRouter released SDK in Jan 2026). May need to research prompt compression techniques (LLMLingua) and multi-model fallback strategies during implementation.
- **Phase 5 (Module 4 - Monitoring):** Shadowban heuristics are community knowledge (not official Reddit documentation). Needs research into latest detection techniques and validation with test accounts.

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Foundation):** Supabase RLS, FastAPI auth, Celery setup are well-documented with established patterns. Use official docs and integration guides.
- **Phase 6 (Billing):** Stripe integration follows standard SaaS patterns. Official SDK has comprehensive documentation and examples.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | All core technologies verified with 2026 sources. Next.js 16, FastAPI 0.128.2, Celery 5.6, SpaCy 3.8, Supabase 2.27.3 releases confirmed. OpenRouter SDK marked as beta (pin version). 90%+ of recommendations have official documentation. |
| Features | **HIGH** | Competitive analysis covered 6+ direct competitors (GummySearch, Subreddit Signals, ReplyAgent, Redreach, Brand24, Unbannnable). Clear white space identified: no competitor combines generation + ban risk intelligence + community mimicry. Table stakes validated against free tools (F5Bot, SubredditStats). |
| Architecture | **HIGH** | Event-driven async pipeline is the standard pattern for long-running data processing. FastAPI + Celery integration extensively documented. Monorepo with Turborepo is proven approach for Next.js + backend. RAG pattern for LLM context grounding is established best practice. |
| Pitfalls | **HIGH** | RLS breach (Moltbook incident Jan 2026 with 1.5M API keys exposed) and Reddit's legal action against Perplexity are recent, well-documented cases. Shadowban heuristics validated through Reddit community sources and moderation tools. AI detection statistics (15% of posts AI-generated) from Originality.AI study. |

**Overall confidence:** **HIGH**

Research is grounded in official documentation, recent case studies (2025-2026), and competitive analysis of active products. Key risks (shadowbans, RLS security, API compliance) are well-documented with concrete prevention strategies.

### Gaps to Address

Despite high confidence, some areas require validation during implementation:

- **SpaCy ISC Scoring Accuracy:** Weight matrix for rhythm analysis is BC-RAO-specific. Research provides the framework (sentence length, clause density, transitional patterns) but exact weights need tuning with real Reddit data. Plan to iterate on scoring engine in Phase 3 based on human evaluation of 100+ posts.

- **Shadowban Detection Heuristics:** Reddit doesn't provide official shadowban API. Detection relies on heuristics (profile accessibility, zero engagement, invisibility in incognito mode). These may evolve as Reddit's anti-spam systems change. Plan to continuously validate detection accuracy in Phase 5 with test accounts and user reports.

- **OpenRouter SDK Stability:** Released Jan 2026, marked as beta. May have breaking changes. Mitigation: Pin to specific version in Phase 4, monitor changelog, implement adapter pattern to isolate SDK dependency (easy to swap if necessary).

- **LLM Mimicry Bypass Rate:** Research shows creative essayist style achieves 84% AI detector bypass vs. 7% for standard generation, but this is based on general content, not Reddit-specific. Plan to validate with GPTZero and Reddit moderator feedback in Phase 4 beta testing.

- **Apify Data Structure Stability:** Apify Reddit Scraper is third-party service. Data format could change without notice. Mitigation: Build flexible parsing layer in Module 1 with schema validation (Pydantic), monitor for API changes, have fallback to direct Reddit API if Apify fails.

**Validation strategy:** Build each module with testability in mind (unit tests for core logic, integration tests for external APIs). Plan 2-week buffer after Phase 4 for beta testing with 10-20 real users to validate mimicry quality and ban avoidance before public launch.

## Sources

### Primary (HIGH confidence)

**Official Documentation:**
- Next.js 15/16 Release Notes — verified React 19 support, Turbopack stability
- FastAPI Documentation (0.128.2) — confirmed Pydantic v2 requirement, async patterns
- Celery 2026 Overview — verified Python 3.9-3.13 support, Redis/RabbitMQ broker compatibility
- SpaCy Processing Pipelines — confirmed en_core_web_md model compatibility, production optimization
- Supabase Python Client (2.27.3) — verified async operations, RLS integration
- OpenRouter API Docs — confirmed prompt caching (0.25x cost), provider routing, max price limits
- Stripe Python SDK (14.3.0) — verified API version 2026-01-28.clover, webhook handling
- Reddit API Documentation — verified 60 requests/minute rate limit, OAuth requirements

**Security Incidents:**
- Moltbook Data Breach (Jan 2026) — 1.5M API keys + 35K emails exposed due to disabled Supabase RLS
- Reddit vs. Perplexity Legal Case — Reddit pursued legal action for TOS violations (scraping without consent)

**Market Research:**
- Competitive landscape analysis: GummySearch (defunct Nov 2025), Subreddit Signals ($20-50/mo), ReplyAgent ($3/post), Redreach, Brand24
- AI content statistics: 15% of Reddit posts AI-generated (Originality.AI study 2025)
- Shadowban risk data: 70-90% ban rate for new accounts (multiple community sources)

### Secondary (MEDIUM confidence)

**Technical Integration Guides:**
- FastAPI + Celery + Redis integration patterns (blog.greeden.me, testdriven.io)
- Turborepo + Next.js monorepo setup (Turborepo official guide, Strapi blog)
- Supabase + SQLAlchemy connection pooling best practices (GitHub discussions)
- Railway FastAPI deployment guides (official Railway docs)

**AI Detection Research:**
- Stylometry: AI writing fingerprints (NetusAI blog, Johns Hopkins study)
- AI humanization bypass rates: 84% for essayist style vs. 7% for standard (Medium research)
- Reddit moderator AI detection strategies (Cornell AI study, ArXiv papers)

**LLM Cost Optimization:**
- Prompt compression techniques: LLMLingua 20x compression (Machine Learning Mastery)
- OpenRouter State of AI 2025: 100T token usage study
- LLM cost reduction strategies: 80% savings potential (Koombea blog)

### Tertiary (LOW confidence, needs validation)

**Community Knowledge:**
- Reddit account warming strategies — multiple blogs (Multilogin, AdsPower, Dicloak) with similar advice but no official Reddit guidance
- Shadowban heuristics — community-developed tools (Reddit Shadowban Checker, PixelScan) without official API
- Karma/age requirements per subreddit — user-reported data (PostIz, RedKarmas) not systematically verified
- AI detector bypass techniques — rapidly evolving landscape, strategies may be outdated by implementation

**Validation plan for tertiary sources:**
- Account warming: Test with 3-5 fresh accounts following different strategies, track ban rates
- Shadowban heuristics: Validate with known shadowbanned accounts (create test accounts, intentionally trigger bans)
- Karma requirements: Scrape public subreddit rules, cross-reference with user reports, update database quarterly
- AI bypass techniques: Continuous A/B testing with GPTZero and real Reddit moderator feedback

---
*Research completed: 2026-02-07*
*Ready for roadmap: yes*
