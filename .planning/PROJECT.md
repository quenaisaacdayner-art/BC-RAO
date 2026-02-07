# BC-RAO

## What This Is

BC-RAO is a Reddit content generation tool for solo SaaS founders who want to promote their products organically without getting banned or shadowbanned. It analyzes the "DNA" of subreddit communities — tone, rhythm, forbidden topics, what works — and generates posts that blend in as authentic contributions while subtly promoting the user's product.

## Core Value

Generated posts must feel 100% human and community-native, never triggering spam detection or moderator flags. If nothing else works, this must.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] User can input their SaaS details (problem, solution, target audience) during onboarding
- [ ] System identifies and suggests ideal subreddits based on product-audience fit
- [ ] System scrapes and analyzes successful conversations in target subreddits via Apify
- [ ] User can select an "Attack Card" archetype (Journey, Solution, Feedback) or create custom ones
- [ ] System analyzes community unwritten rules: tone, rhythm, forbidden topics
- [ ] System generates a Community Sensitivity Index (CSI) indicating ban risk level
- [ ] User can view a "Community Etiquette Manual" for each target subreddit
- [ ] User can optionally provide a rough draft or leave input empty for full generation
- [ ] System generates (or refines) a final post using mimicry filters for human-native feel
- [ ] System enforces a syntax blacklist to avoid spam-flagged patterns
- [ ] Free trial with paid tiers, differentiated by number of subreddits tracked
- [ ] Stripe-based billing with plan limit enforcement
- [ ] User authentication via Supabase (email/password signup, session persistence)

### Out of Scope

- Sentinel monitoring (post-deployment tracking) — v2, after core generation proves value
- Post-audit loop and pivot suggestions — v2, depends on monitoring
- Hacker News / other platforms — Reddit-only for v1
- Mobile app — web-first
- Real-time chat or collaboration — solo founder tool
- OAuth login (Google, GitHub) — email/password sufficient for v1
- Video content generation — text posts only

## Context

- The product name "BC-RAO" references the alchemical nature of transmuting marketing intent into authentic community conversation
- The 6-stage user journey (Briefing → Selection → Intelligence → Generation → Sentinel → Audit) is the full vision; MVP covers stages 1-4
- Attack Cards are content archetypes: Journey (personal story), Solution (helpful answer), Feedback (asking for input) — defaults plus user-created custom archetypes
- Community analysis uses SpaCy NLP for rhythm/linguistic pattern detection and LLMs (via OpenRouter) for archetype classification
- The infrastructure document (`bc-rao-infrastructure_1.md`) defines the full deployment architecture: monorepo with Turborepo, GitHub Actions CI/CD, Vercel preview environments
- Reddit data collection uses Apify's Reddit Scraper actor
- LLM inference goes through OpenRouter (multi-model routing)
- All user data is isolated via Supabase Row Level Security (RLS)

## Constraints

- **Tech stack (frontend)**: Next.js 15 on Vercel — SSR/ISR for dashboard, edge functions for auth
- **Tech stack (backend)**: FastAPI + Celery on Railway — long-running collection tasks, SpaCy model in memory
- **Database**: Supabase (PostgreSQL + Auth + RLS) — staging and production projects
- **Monorepo**: Turborepo with `apps/web`, `apps/api`, `packages/shared`
- **LLM costs**: Must track and cap per-user LLM spending (OpenRouter cost tracking)
- **External APIs**: Apify (Reddit scraping), OpenRouter (LLM), Stripe (billing), Resend (email)
- **Reddit only**: v1 targets Reddit exclusively; architecture should not over-abstract for multi-platform

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Monorepo (Turborepo) | Shared types between TS frontend and Python backend, unified CI, coherent previews | — Pending |
| Railway for backend (not Vercel) | Celery workers need persistent processes, SpaCy model needs persistent RAM | — Pending |
| Supabase over self-hosted Postgres | Auth + RLS built-in, free staging tier, managed infrastructure | — Pending |
| OpenRouter over direct OpenAI | Multi-model routing, cost optimization, model flexibility | — Pending |
| MVP = Generate only (stages 1-4) | Prove core value (safe posts) before investing in monitoring pipeline | — Pending |
| Subreddits as billing dimension | Subreddit count is the natural scaling metric for this product | — Pending |

---
*Last updated: 2026-02-07 after initialization*
