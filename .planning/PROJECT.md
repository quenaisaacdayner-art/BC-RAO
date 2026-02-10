# BC-RAO

## What This Is

BC-RAO is a social intelligence platform that automates market validation and organic user acquisition for SaaS founders on Reddit. It reads the behavioral DNA of online communities, generates content conditioned to match community norms (archetypes, syntax rhythm, vulnerability patterns), and monitors post survival — transforming founders from obvious marketers into legitimate community collaborators.

## Core Value

Founders can generate Reddit posts that survive moderation and earn genuine engagement by mimicking native community behavior patterns, not by guessing.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] User can create campaigns with product context, keywords, and target subreddits
- [ ] Module 1 (Collector) scrapes Reddit via Apify, filters with regex, stores raw posts
- [ ] Module 2 (Pattern Engine) classifies archetypes, scores posts, builds community profiles with ISC
- [ ] SpaCy performs local rhythm analysis (sentence length, formality, tone) at zero API cost
- [ ] Module 3 (Generator) produces conditioned drafts using community profile + archetype + blacklist constraints
- [ ] Draft generation respects ISC gating, account status, and decision tree logic
- [ ] Syntax blacklist prevents repeating patterns that caused past removals
- [ ] Module 4 (Orchestrator) monitors posted content with dual-check shadowban detection
- [ ] Negative reinforcement loop feeds removal data back into blacklist and community profiles
- [ ] Supabase Auth with profiles, subscriptions, and RLS tenant isolation
- [ ] Stripe billing with trial (7-day, no card), Starter ($49), and Growth ($99) plans
- [ ] Usage tracking enforces plan limits (subreddits, drafts/month, campaigns, monitors)
- [ ] Guided onboarding (4 steps) from signup to first data collection
- [ ] Next.js dashboard with campaign management, community profiles, draft editor, monitoring dashboard
- [ ] Email alerts for emergency (shadowban), success, and trial lifecycle events

### Out of Scope

- Auto-posting to Reddit — ToS violation, trust anti-pattern
- Hacker News support — different API/dynamics, V2
- Multi-language NLP — English-first, other SpaCy models later
- Team/multi-user accounts — single-founder focus
- Real-time WebSocket dashboard — polling every 30s sufficient
- Custom model fine-tuning — OpenRouter model selection covers needs
- Mobile app — responsive web sufficient
- Public API / webhooks — not needed until platform play
- A/B testing of drafts — after baseline established
- Semantic search UI on raw_posts — pgvector column exists, UI deferred
- White-label / agency tier — V2

## Context

**System spec:** `bc-rao-system-spec_1.md` is the locked source of truth for schema, API design, module architecture, inference routing, pricing, and deployment.

**Build priority:** Core loop first (Collect → Analyze → Generate) with end-to-end dashboard. Auth stubbed initially, real Supabase Auth added when connecting frontend. Monitoring (Module 4) and billing (Stripe) follow after core loop works.

**External services ready:** Apify account with Reddit actor selected, OpenRouter API key ready. No mocking needed — real integrations from the start.

**4-Module architecture:**
1. Module 1 (Data Collector): Apify → Regex filter → AI processing → raw_posts storage
2. Module 2 (Pattern Engine): Archetype classification + SpaCy rhythm analysis + community profiling + ISC scoring
3. Module 3 (Conditioning Generator): Community profile + archetype + blacklist → conditioned draft via OpenRouter
4. Module 4 (Orchestrator): Shadow table monitoring + dual-check shadowban detection + negative reinforcement feedback loop

**Cost control is critical:** Apify credits + LLM tokens are the main variable cost. Regex pre-filtering reduces AI volume by ~80%. Only top 10% of posts get full LLM processing. SpaCy runs locally for zero-cost NLP. Per-plan cost caps enforced.

## Deployment Rules (LAW)

- **Testing environment:** All UAT testing is done on Vercel via the production deploy, NOT localhost
- **Vercel URL:** https://bc-rao-frontend.vercel.app/
- **GitHub repo:** https://github.com/quenaisaacdayner-art/BC-RAO.git
- **Auto-commit:** Every code change MUST be committed and pushed to GitHub automatically — no waiting for user confirmation
- **Deploy flow:** Code change → git commit → git push → Vercel auto-deploys from GitHub
- **These rules are permanent and override any defaults**

## Constraints

- **Tech stack**: Next.js 15 + Tailwind + Shadcn/UI (frontend), Python 3.11+ / FastAPI (backend), Supabase (database + auth), Celery + Redis (workers), OpenRouter (AI), Apify (scraping) — locked per system spec
- **Pricing**: Trial $0/7d, Starter $49/mo, Growth $99/mo — locked per system spec
- **Database schema**: As defined in system spec Section 4 — locked
- **API design**: As defined in system spec Section 5 — locked
- **Inference routing**: OpenRouter with model-per-task routing as defined in system spec Section 6 — locked
- **Project structure**: Backend follows `bc-rao-api/` structure from system spec Section 12 — locked

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Spec is locked source of truth | Comprehensive system spec already covers schema, API, modules, pricing, deployment | — Pending |
| Core loop first, monitoring/billing later | Get Collect → Analyze → Generate working end-to-end before adding Module 4 and Stripe | — Pending |
| Stub auth during core loop build | Move faster on module development, add real Supabase Auth when connecting frontend | — Pending |
| Real integrations from start (no mocks) | Apify and OpenRouter ready, skip mock layer complexity | — Pending |
| Full dashboard from start | End-to-end UI (Next.js) not just API — user wants to see the value loop visually | — Pending |

---
*Last updated: 2026-02-07 after initialization*
