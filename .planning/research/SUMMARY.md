# Project Research Summary

**Project:** BC-RAO (Social Intelligence Platform)
**Domain:** Reddit behavioral analysis + AI content generation + post monitoring
**Researched:** 2026-02-07
**Confidence:** HIGH

## Executive Summary

BC-RAO is a social intelligence platform that helps indie hackers and SaaS founders engage authentically on Reddit by analyzing community patterns, generating contextually-appropriate content, and monitoring post survival. Research confirms this is a validated market (GummySearch closure left gap, competitors like SubredditSignals generating 78 leads/month), but success depends on navigating Reddit's strict anti-scraping enforcement and managing multi-vendor costs (Apify + OpenRouter + Supabase).

The recommended architecture splits cleanly: Next.js 15 frontend on Vercel, FastAPI backend + Celery workers on Railway/Render, Supabase for database + auth, and OpenRouter for LLM routing. This stack is production-proven with established integration patterns. The critical technical differentiator is behavioral mimicry through multi-layered conditioning (archetype classification + Community Sensitivity Index + syntax rhythm analysis + blacklist constraints), which no competitor explicitly offers.

The primary risks are cost control (Apify + LLM can exceed revenue at $49/month without aggressive filtering), legal exposure (Reddit actively suing scrapers who violate ToS), and shadowban detection accuracy (false positives damage credibility). Mitigation strategy: use official Reddit API exclusively (never HTML scraping), implement 80% regex pre-filter before LLM processing, build dual-session shadowban detection with confidence scoring, and set hard spending caps on all external APIs.

## Key Findings

### Recommended Stack

BC-RAO's locked stack represents a mature, production-ready combination validated through extensive research. The architecture leverages Next.js 15 (stable App Router, React 19, Turbopack), FastAPI 0.128.4+ (Pydantic v2, async-first), Supabase (managed Postgres + auth + RLS + pgvector), Celery 5.6.2+ (memory leak fixes), Redis 7.x (broker + backend), and OpenRouter (unified LLM routing). This configuration has established integration patterns documented across multiple production deployments.

**Core technologies:**
- **Next.js 15 + React 19**: Frontend framework with SSR/SSG — 76.7% faster dev server, stable App Router, full TypeScript support with next.config.ts
- **FastAPI 0.128.4+**: API framework — latest stable with Pydantic v2 integration, automatic OpenAPI docs, async-first design for high concurrency
- **Supabase**: Database + auth + real-time — managed Postgres 15+, built-in RLS for tenant isolation, pgvector for embeddings, 99.9% SLA
- **Celery 5.6.2 + Redis 7.x**: Task queue — distributed async processing, memory leak fixes in latest release, sub-millisecond broker latency
- **OpenRouter**: LLM routing gateway — access 400+ models, automatic fallbacks, cost optimization, prevents vendor lock-in
- **spaCy 3.8.11 + en_core_web_md**: Local NLP — zero API cost, 20k word vectors for behavioral analysis, Python 3.13 support
- **Apify**: Reddit scraping service — pre-built actors, handles OAuth + rate limits, webhook-based async results

**Critical version requirements:**
- Python 3.11 or 3.12 (best performance + stability balance for FastAPI + Celery + spaCy)
- Node.js 18.18.0+ (Next.js 15 minimum requirement)
- Supabase Transaction Mode (port 6543) with disabled prepared statements for production
- Celery 5.6+ required (earlier versions have critical memory leaks)

### Expected Features

Research across 7 Reddit marketing tools and 15+ social listening platforms reveals clear feature expectations. BC-RAO's differentiators (behavioral mimicry, Community Sensitivity Index, negative reinforcement learning) fill gaps left by GummySearch's closure and competitor limitations.

**Must have (table stakes):**
- Content Discovery & Keyword Monitoring — users expect automated scanning of relevant subreddits/posts (SubredditSignals, F5Bot, Brand24 all provide this)
- Sentiment Analysis (Basic) — positive/neutral/negative classification to filter irrelevant posts
- Engagement Metrics Tracking — upvotes, comments, CTR, engagement trends (Reddit's algorithm prioritizes upvote rate)
- Shadowban Detection — users assume tools warn about shadowbans proactively (multiple free checkers exist)
- Community Profile/Research — insight into subreddit culture, demographics, posting patterns (GummySearch pioneered this)
- Post Scheduling (Notification-based) — standard in all social tools, but must avoid API-based posting (Reddit shadowbans API posts 8x more)

**Should have (competitive differentiators):**
- Behavioral Mimicry / Style Matching — generate content that "sounds native" to specific communities (BC-RAO's archetype + syntax rhythm analysis is unique)
- Community Sensitivity Index (ISC) — quantify how strict/sensitive a subreddit is to self-promotion (no competitor offers explicitly)
- Negative Reinforcement Learning — feed removal/shadowban data back to improve content generation (Meta's Dec 2025 research shows 100x data efficiency)
- Post Archetype Classification — identify Journey/ProblemSolution/Feedback patterns for better targeting
- Syntax Rhythm Analysis — match linguistic patterns beyond keywords (sentence length, punctuation, conversational flow via SpaCy)
- Dual-Check Shadowban Detection — multi-method verification reduces false positives

**Defer (v2+):**
- Managed Account Posting — operational complexity requires infrastructure BC-RAO doesn't have yet (ReplyAgent.ai model)
- Multi-Account Management — legally/practically risky (Reddit actively detects)
- Full Multi-Platform Monitoring — Reddit + Twitter + Facebook = 4x complexity, stay focused until dominance
- Competitor Auto-Response Templates — likely to be misused, leads to spam

**Anti-features to avoid:**
- Direct API Auto-Posting — Reddit shadowbans API posts (8x higher removal rate), use notification-based posting instead
- Universal Content Templates — Reddit communities are highly distinct, templates get downvoted
- Real-Time Everything — creates notification fatigue, batch non-urgent alerts

### Architecture Approach

Standard architecture for social intelligence platforms processing Reddit data follows API-first pattern with async workers. FastAPI handles orchestration and returns task IDs immediately while Celery workers process long-running operations (scraping, analysis, monitoring). This enables non-blocking API, horizontal scaling of workers, and graceful degradation.

**Major components:**
1. **Client Layer (Vercel)** — Next.js 15 frontend with Server Components for direct Supabase queries (read-heavy), dashboard polling for task status, JWT auth via cookies
2. **API Layer (Railway/Render)** — FastAPI backend with service layer isolation, campaign/collector/analyzer/generator/monitor routes, JWT validation middleware, Pydantic request/response validation
3. **Worker Layer (Railway/Render)** — Celery workers + Beat scheduler, separate queues (scraping, ml_processing, ai_generation, monitoring), Redis broker + backend with separate DBs
4. **Inference Layer** — InferenceClient abstraction wrapping OpenRouter (prevents vendor lock-in), model routing by task (Haiku for classification, Sonnet for generation), cost tracking + quota enforcement
5. **Local NLP Layer** — SpaCy en_core_web_md for zero-cost processing (sentence length, formality scoring, rhythm analysis, regex filtering)
6. **Data Layer (Supabase)** — PostgreSQL + pgvector + Auth + RLS, all tables isolated by user_id via RLS policies, HNSW indexes for vector similarity

**Key patterns:**
- Event-driven pipeline: campaigns → raw_posts → community_profiles → generated_drafts → shadow_table → syntax_blacklist (feedback loop)
- Cost-gated inference: check plan caps BEFORE LLM calls, track usage immediately AFTER, enforce hard limits at 80% threshold
- Dual-session monitoring: authenticated + anonymous HTTP checks to detect shadowbans (single-check misses them)
- Tenant isolation via RLS: database-level enforcement prevents data leaks even if application logic breaks
- Tiered filtering: regex pre-filter (80% reduction) → SpaCy scoring → top 10% get LLM processing

### Critical Pitfalls

Research across Reddit scraping, LLM security, and Celery production deployments reveals 8 critical failure modes. Top 5 by severity:

1. **Reddit Rate Limiting Escalation** — 60 req/min limit escalates to IP blocks lasting days if ignored. Avoid: centralized rate limiting before Apify actors, batch endpoints, circuit breaker on HTTP 429, OAuth authentication always, max 1-2 concurrent requests
2. **Prompt Injection via Scraped Content** — malicious Reddit posts can hijack LLM prompts (13% of web chatbots exposed). Avoid: isolate AI instructions from user data, sanitize all scraped content (strip markdown, detect "Ignore previous instructions"), LLM guardrails, output validation
3. **LLM + Apify Cost Explosion** — variable costs can exceed $49 Starter revenue ($500+ bills). Avoid: hard spending caps (Apify $20/month, OpenRouter $30/month), 80% regex pre-filter before LLM, max_tokens=500, cheaper models for classification, real-time cost alerts at 80%
4. **Reddit ToS Violation and Legal Exposure** — Reddit suing Perplexity, SerpAPI, Oxylabs for "unlawful scraping." Avoid: official API ONLY (never HTML scraping), no proxy rotation/user-agent spoofing, OAuth authentication, Reddit attribution, audit logs proving API-only usage
5. **Shadowban Detection False Positives** — tools can't distinguish shadowban/suspended/deleted (same signals). Avoid: multi-signal detection (API checks, score monitoring, modlog), confidence scores not binary yes/no, flag ambiguous cases as "uncertain," transparency about limitations

**Additional gotchas:**
- Celery + Redis memory leaks (use 5.6+, configure worker_max_tasks_per_child=1000, worker_max_memory_per_child=250000)
- Supabase RLS performance degradation (index ALL user_id columns, use IN/ANY operators not direct equality, monitor with Performance Advisors)
- Apify actor "Under Maintenance" cascading failures (health checks, fallback to direct Reddit API, pin versions)

## Implications for Roadmap

Based on combined research, recommended 6-phase structure aligns with technical dependencies and risk mitigation:

### Phase 1: Foundation + Authentication
**Rationale:** Auth + database are dependencies for everything else. Early deploy pipeline prevents integration issues. Cost monitoring must be built FIRST before any external API usage (Pitfall #3).

**Delivers:** User signup/login, dashboard scaffold, campaign CRUD, cost tracking infrastructure

**Addresses features:**
- Basic campaign management (table stakes)
- User authentication via Supabase
- Billing groundwork (usage tracking tables)

**Avoids pitfalls:**
- Cost explosion — build spending caps before Apify/OpenRouter integration
- RLS performance — design policies with indexes from day 1

**Research flag:** Standard authentication patterns, no deep research needed. Supabase Next.js integration well-documented.

---

### Phase 2: Collection Pipeline (Module 1)
**Rationale:** Data collection is the input for entire pipeline. Must establish legal Reddit API usage patterns before building analysis/generation features (Pitfall #4). Implements 80% regex pre-filter to control LLM costs (Pitfall #3).

**Delivers:** Reddit scraping via Apify → regex filtering → archetype classification → storage in raw_posts table

**Uses stack:**
- Apify SDK for Reddit scraping (OAuth-based, handles rate limits)
- Celery workers for async processing
- Redis broker + backend
- OpenRouter via InferenceClient for archetype classification
- Supabase for raw_posts storage

**Addresses features:**
- Content Discovery & Keyword Monitoring (must-have)
- Post Archetype Classification (differentiator)

**Avoids pitfalls:**
- Reddit ToS violation — use official API only, no HTML scraping
- Rate limiting escalation — centralized rate limiting, circuit breaker pattern
- Cost explosion — 80% regex pre-filter before LLM, hard spending caps

**Research flag:** NEEDS DEEP RESEARCH for Apify integration specifics (webhook patterns, actor selection, rate limit coordination with Reddit API).

---

### Phase 3: Pattern Engine (Module 2)
**Rationale:** Depends on Module 1 data. Community profiles provide context for Module 3 generation. SpaCy local processing minimizes API costs. Aggregation logic is complex and requires careful design.

**Delivers:** Raw posts analyzed → community profiles generated → ISC scores calculated → syntax patterns extracted

**Implements architecture:**
- SpaCy NLP analyzer (local, zero-cost)
- InferenceClient for success/engagement scoring
- Pattern service aggregation logic
- community_profiles table with embeddings

**Addresses features:**
- Community Profile/Research (must-have)
- Community Sensitivity Index (differentiator)
- Syntax Rhythm Analysis (differentiator)

**Avoids pitfalls:**
- Cost explosion — SpaCy processing is free, only top candidates get LLM scoring
- Prompt injection — sanitize scraped content before LLM analysis

**Research flag:** NEEDS RESEARCH for SpaCy rhythm analysis patterns and ISC scoring algorithm design.

---

### Phase 4: Draft Generation (Module 3)
**Rationale:** Depends on Module 2 profiles. Critical path to user value. Implements core differentiator (behavioral mimicry). Cost tracking ensures we don't exceed plan revenue.

**Delivers:** User generates drafts conditioned on community profiles + blacklist constraints → drafts stored with metadata

**Implements architecture:**
- Generator service (prompt building, blacklist checking)
- Prompt templates per archetype
- InferenceClient with cost enforcement
- generated_drafts table

**Addresses features:**
- AI Content Generation with Community Conditioning (differentiator)
- Behavioral Mimicry / Style Matching (differentiator)

**Avoids pitfalls:**
- Cost explosion — max_tokens=500, cost cap checks BEFORE LLM calls
- Prompt injection — isolate instructions from scraped content, output validation

**Research flag:** Standard LLM integration patterns. OpenRouter well-documented. No deep research unless custom prompting techniques needed.

---

### Phase 5: Monitoring + Feedback (Module 4)
**Rationale:** Completes the loop (generate → post → monitor → learn). Shadowban detection is must-have feature. Feedback loop (removed posts → blacklist) enables negative reinforcement learning (differentiator).

**Delivers:** User registers posted drafts → periodic dual-session HTTP checks → email alerts on status change → blacklist updated on removals

**Implements architecture:**
- Monitor service (dual-session HTTP checks)
- Celery Beat for scheduled tasks
- Resend for email alerts
- shadow_table + syntax_blacklist

**Addresses features:**
- Shadowban Detection (must-have)
- Engagement Metrics Tracking (must-have)
- Negative Reinforcement Learning from Removals (differentiator)

**Avoids pitfalls:**
- Shadowban detection false positives — multi-signal detection, confidence scores, transparent limitations
- Celery memory leaks — worker recycling, result expiration

**Research flag:** Shadowban detection requires validation testing (no single authoritative source on Reddit's exact signals). Plan for experimental verification.

---

### Phase 6: Billing + Plan Limits
**Rationale:** Monetization layer. Can be built in parallel with Phases 3-4 if needed. Enforces cost controls that prevent business model failure.

**Delivers:** Trial expires → user upgrades via Stripe → plan limits enforced → usage stats visible

**Implements architecture:**
- Stripe integration (checkout, portal, webhooks)
- Usage service (limit enforcement in all endpoints)
- Plan limit middleware

**Addresses features:**
- Subscription tiers (Trial $0/7d, Starter $49/mo, Growth $99/mo)
- Usage tracking dashboard

**Avoids pitfalls:**
- Cost explosion — hard caps prevent users from exceeding plan revenue
- Runaway testing — free tier limits prevent abuse

**Research flag:** Standard Stripe patterns, well-documented FastAPI integrations. No deep research needed.

---

### Phase Ordering Rationale

- **Phases 1-2 must be sequential:** Can't collect data without auth/database foundation
- **Phase 2 blocks Phases 3-4:** Analysis and generation require raw_posts data
- **Phase 3 blocks Phase 4:** Generation needs community profiles for conditioning
- **Phase 4 blocks Phase 5:** Monitoring needs generated_drafts to track
- **Phase 6 can parallel Phases 3-5:** Billing is independent, can accelerate if needed

**Critical path:** 1 → 2 → 3 → 4 → 5 (can ship without 6 for beta, but not sustainable)

**Earliest viable demo:** End of Phase 4 (can generate conditioned drafts, but no monitoring)

**Earliest revenue-generating launch:** End of Phase 6 (full loop + self-serve billing)

### Research Flags

**Phases needing deeper research during planning:**
- **Phase 2 (Collection):** Apify actor selection, webhook integration, Reddit API rate limit coordination, cost optimization
- **Phase 3 (Pattern Engine):** SpaCy rhythm analysis implementation, ISC scoring algorithm design, aggregation performance optimization

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Foundation):** Supabase Next.js auth, FastAPI JWT validation — extensive official docs
- **Phase 4 (Generation):** OpenRouter LLM integration — standard API patterns
- **Phase 5 (Monitoring):** Celery Beat scheduling, HTTP checks — well-documented
- **Phase 6 (Billing):** Stripe FastAPI integration — mature ecosystem

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technologies have official docs, established integration patterns verified across multiple production deployments |
| Features | MEDIUM-HIGH | Competitor analysis solid (7 tools analyzed), but some features (ISC, behavioral mimicry) are BC-RAO innovations requiring validation |
| Architecture | HIGH | Standard patterns for Reddit scraping + LLM platforms, extensive FastAPI + Celery production guides, Supabase RLS best practices well-documented |
| Pitfalls | HIGH | Multiple authoritative sources (Reddit legal actions, OWASP LLM security, Celery GitHub issues), but some risks (ToS enforcement) unpredictable |

**Overall confidence:** HIGH

The locked stack is production-validated, architecture patterns are established, and pitfalls have documented mitigation strategies. Main uncertainty is market validation (GummySearch's closure suggests demand, but need to test pricing/positioning) and Reddit's ToS enforcement unpredictability.

### Gaps to Address

**During Phase 2 planning:**
- **Apify actor reliability:** Research shows "Under Maintenance" risk, but specific actor for Reddit (trudax/reddit-scraper) needs evaluation. May need direct Reddit API fallback.
- **Rate limit coordination:** Apify actors handle OAuth internally, but coordination with direct API calls (if fallback needed) requires testing.

**During Phase 3 planning:**
- **ISC scoring algorithm:** No competitor publishes methodology. Requires original research: analyze correlation between subreddit rules, removal rates, and successful post patterns.
- **SpaCy rhythm analysis:** en_core_web_md vectors sufficient for MVP, but may need upgrade to en_core_web_lg for production quality.

**During Phase 5 planning:**
- **Shadowban detection accuracy:** Research shows false positive risk, but exact signals Reddit uses are undocumented. Requires experimental validation with test accounts across multiple subreddits.

**Ongoing validation:**
- **Cost model viability:** Research confirms Apify + OpenRouter costs manageable with filtering, but real-world COGS need monitoring in first 100 users to validate $49 Starter pricing.
- **Legal compliance:** Reddit's API ToS evolving (Jan 2025 enforcement changes), monitor for updates during development.

## Sources

### Primary (HIGH confidence)
- **Official Documentation:**
  - [Next.js 15 Release Notes](https://nextjs.org/blog/next-15) — App Router stability, React 19 support
  - [FastAPI Documentation](https://fastapi.tiangolo.com/) — Pydantic v2 integration, async patterns
  - [Celery 5.6 Documentation](https://docs.celeryq.dev/en/main/) — Memory leak fixes, worker configuration
  - [Supabase Guides](https://supabase.com/docs) — RLS best practices, pgvector integration
  - [OpenRouter API Reference](https://openrouter.ai/docs/api/reference/overview) — Model routing, pricing

- **Integration Guides:**
  - [Supabase Connection Scaling for FastAPI](https://medium.com/@papansarkar101/supabase-connection-scaling-the-essential-guide-for-fastapi-developers-2dc5c428b638) — Transaction Mode with disabled prepared statements
  - [Complete Guide to Background Processing with FastAPI × Celery](https://blog.greeden.me/en/2026/01/27/the-complete-guide-to-background-processing-with-fastapi-x-celery-redishow-to-separate-heavy-work-from-your-api-to-keep-services-stable/) — API-first async patterns

### Secondary (MEDIUM confidence)
- **Competitor Analysis:**
  - [7 Best Reddit Marketing Tools 2026](https://www.subredditsignals.com/blog/the-ultimate-guide-to-reddit-marketing-tools-2026-update) — Feature comparison
  - [7 Best GummySearch Alternatives](https://painonsocial.com/blog/gummysearch-alternatives-reddit-market-research) — Gap analysis post-closure
  - [Reddit Comment Services With Managed Accounts](https://www.replyagent.ai/blog/reddit-comment-services-with-managed-accounts) — Competitive positioning

- **Security & Compliance:**
  - [Reddit API Rate Limits Guide 2026](https://painonsocial.com/blog/reddit-api-rate-limits-guide) — 60 req/min limit, OAuth requirements
  - [How to Scrape Reddit Legally 2026](https://painonsocial.com/blog/how-to-scrape-reddit-legally) — ToS compliance, legal risk analysis
  - [OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) — Sanitization requirements
  - [Reddit Launches Legal Action Against AI Data Scrapers](https://www.socialmediatoday.com/news/reddit-launches-legal-action-against-ai-data-scrapers/803572/) — Enforcement precedent

- **Cost & Performance:**
  - [OpenRouter API Pricing 2026](https://zenmux.ai/blog/openrouter-api-pricing-2026-full-breakdown-of-rates-tiers-and-usage-costs) — Token cost analysis
  - [Apify Review 2026](https://hackceleration.com/apify-review/) — Pricing, reliability data
  - [Supabase RLS Performance Best Practices](https://supabase.com/docs/guides/troubleshooting/rls-performance-and-best-practices-Z5Jjwv) — Index requirements

### Tertiary (LOW confidence, needs validation)
- **Shadowban Detection:**
  - [Reddit Shadowbans 2025: How They Work](https://reddifier.com/blog/reddit-shadowbans-2025-how-they-work-how-to-detect-them-and-what-to-do-next) — Detection heuristics (Reddit doesn't publish official signals)
  - [Apify Reddit Shadowban Checker](https://apify.com/iskander/reddit-shadowban-checker) — Actor implementation approach

- **NLP for Social Media:**
  - SpaCy rhythm analysis for Reddit content — no direct research found, inferred from general NLP patterns
  - Community Sensitivity Index scoring — BC-RAO innovation, no precedent found

---
*Research completed: 2026-02-07*
*Ready for roadmap: yes*
