# Architecture Research

**Domain:** Social intelligence platform (scraping + NLP + LLM generation)
**Researched:** 2026-02-07
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER (Vercel)                              │
├──────────────────────────────────────────────────────────────────────────────┤
│  Next.js 15 Frontend                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐      │
│  │  Dashboard  │  │  Campaign    │  │  Draft       │  │  Monitor    │      │
│  │  (polling)  │  │  Management  │  │  Editor      │  │  Status     │      │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘      │
│         │                │                  │                  │              │
│         └────────────────┴──────────────────┴──────────────────┘              │
│                                     │                                         │
│         ┌───────────────────────────┴──────────────────────┐                 │
│         │                                                   │                 │
│    [JWT Auth]                                      [Realtime Updates]         │
│         │                                                   │                 │
├─────────┴───────────────────────────────────────────────────┴─────────────────┤
│                         API LAYER (Railway/Render)                           │
├──────────────────────────────────────────────────────────────────────────────┤
│  FastAPI Backend (Python 3.11+)                                              │
│  ┌──────────┐  ┌───────────┐  ┌───────────┐  ┌──────────┐  ┌─────────┐     │
│  │  Auth    │  │ Campaign  │  │ Collector │  │ Analyzer │  │ Monitor │     │
│  │  Routes  │  │  Routes   │  │  Routes   │  │  Routes  │  │ Routes  │     │
│  └────┬─────┘  └─────┬─────┘  └─────┬─────┘  └────┬─────┘  └────┬────┘     │
│       │              │               │              │              │          │
│       └──────────────┴───────────────┴──────────────┴──────────────┘          │
│                                     │                                         │
│       ┌─────────────────────────────┴─────────────────────────────┐          │
│       │                    Service Layer                           │          │
│       │  ┌────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐     │          │
│       │  │  Auth  │  │ Pattern │  │Generator │  │ Monitor  │     │          │
│       │  │Service │  │ Service │  │ Service  │  │ Service  │     │          │
│       │  └────────┘  └─────────┘  └──────────┘  └──────────┘     │          │
│       └───────────────────────────────────────────────────────────┘          │
│                                     │                                         │
├─────────────────────────────────────┼─────────────────────────────────────────┤
│                        WORKER LAYER (Railway/Render)                         │
├─────────────────────────────────────┴─────────────────────────────────────────┤
│  Celery Workers + Celery Beat                                                │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐  ┌────────────┐       │
│  │  Collection  │  │  Analysis   │  │  Monitoring  │  │   Email    │       │
│  │    Tasks     │  │   Tasks     │  │    Tasks     │  │   Tasks    │       │
│  │ (Apify SDK)  │  │ (SpaCy+LLM) │  │ (HTTP check) │  │  (Resend)  │       │
│  └──────────────┘  └─────────────┘  └──────────────┘  └────────────┘       │
│         │                 │                  │                 │              │
│         └─────────────────┴──────────────────┴─────────────────┘              │
│                                     │                                         │
│                          ┌──────────┴──────────┐                             │
│                          │  Redis (Message     │                             │
│                          │  Broker + Backend)  │                             │
│                          └─────────────────────┘                             │
│                                     │                                         │
├─────────────────────────────────────┼─────────────────────────────────────────┤
│                         INFERENCE LAYER                                      │
├─────────────────────────────────────┴─────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────┐          │
│  │                 InferenceClient Abstraction                     │          │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐    │          │
│  │  │   Classify  │  │   Generate   │  │   Extract Patterns │    │          │
│  │  │  Archetype  │  │    Draft     │  │   & Score Posts    │    │          │
│  │  │   (Haiku)   │  │   (Sonnet)   │  │      (Haiku)       │    │          │
│  │  └──────┬──────┘  └──────┬───────┘  └─────────┬──────────┘    │          │
│  │         └─────────────────┴───────────────────┬┘               │          │
│  │                                               │                 │          │
│  │              ┌────────────────────────────────┘                 │          │
│  │              │         OpenRouter                               │          │
│  │              │   (Model routing + fallback)                     │          │
│  │              └────────────────────────────────┐                 │          │
│  │                                               │                 │          │
│  │         ┌──────────────┐  ┌──────────────┐  ┌┴──────────────┐ │          │
│  │         │  Claude API  │  │ OpenAI API   │  │  Gemini API   │ │          │
│  │         │   (primary)  │  │  (fallback)  │  │  (fallback)   │ │          │
│  │         └──────────────┘  └──────────────┘  └───────────────┘ │          │
│  └────────────────────────────────────────────────────────────────┘          │
│                                     │                                         │
│  ┌────────────────────────────────────────────────────────────────┐          │
│  │              SpaCy Local NLP (Zero API cost)                    │          │
│  │  • Sentence length analysis   • Formality scoring               │          │
│  │  • Rhythm analysis            • Tone classification             │          │
│  │  • Vocabulary complexity      • Regex filtering                 │          │
│  └────────────────────────────────────────────────────────────────┘          │
│                                     │                                         │
├─────────────────────────────────────┼─────────────────────────────────────────┤
│                          DATA LAYER (Supabase)                               │
├─────────────────────────────────────┴─────────────────────────────────────────┤
│  PostgreSQL + pgvector + Auth + RLS                                          │
│  ┌────────────┐  ┌───────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   users +  │  │ campaigns │  │  raw_posts   │  │  community   │         │
│  │    subs    │  │           │  │  (Module 1)  │  │   profiles   │         │
│  │            │  │           │  │              │  │  (Module 2)  │         │
│  └────────────┘  └───────────┘  └──────────────┘  └──────────────┘         │
│                                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  generated   │  │   shadow     │  │   syntax     │  │    usage     │    │
│  │   drafts     │  │   table      │  │  blacklist   │  │   tracking   │    │
│  │ (Module 3)   │  │ (Module 4)   │  │  (feedback)  │  │   (limits)   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                               │
│  All tables: RLS enabled, user_id FK for tenant isolation                    │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Next.js Frontend** | User interface, auth state, dashboard polling | Server-rendered React with Supabase client for auth + direct DB queries |
| **FastAPI Backend** | REST API, business logic, validation, orchestration | Async-first Python with Pydantic validation, JWT middleware |
| **Celery Workers** | Background tasks (scraping, monitoring, analysis, emails) | Python task queue with Redis broker, scheduled via Beat |
| **Redis** | Message broker + task result backend | In-memory data store for Celery task queuing |
| **InferenceClient** | LLM routing abstraction with cost tracking | Python wrapper around OpenRouter API with fallback logic |
| **SpaCy NLP** | Local NLP processing (rhythm, formality, syntax) | Python library (en_core_web_md), no API costs |
| **Supabase** | Database, auth, RLS, pgvector | Managed PostgreSQL with built-in auth and Row-Level Security |
| **Apify SDK** | Reddit scraping orchestration | Python SDK wrapping managed actors with proxy rotation |
| **OpenRouter** | Model routing, fallback, unified API | API gateway supporting multiple LLM providers |

## Recommended Project Structure

```
bc-rao/
├── frontend/                      # Next.js 15 application
│   ├── app/                       # App router (Next.js 15)
│   │   ├── (auth)/                # Auth pages group
│   │   │   ├── login/
│   │   │   └── signup/
│   │   ├── (dashboard)/           # Protected routes group
│   │   │   ├── campaigns/
│   │   │   ├── drafts/
│   │   │   ├── monitor/
│   │   │   └── settings/
│   │   └── api/                   # Next.js API routes (minimal)
│   │       └── supabase/
│   ├── components/                # React components
│   │   ├── ui/                    # Shadcn/UI components
│   │   └── features/              # Feature-specific components
│   ├── lib/                       # Client utilities
│   │   ├── supabase.ts            # Supabase client (auth + realtime)
│   │   └── api.ts                 # FastAPI client wrapper
│   └── types/                     # TypeScript types
│
├── backend/                       # FastAPI application
│   ├── app/
│   │   ├── api/v1/                # API endpoints
│   │   │   ├── auth.py            # Supabase JWT validation
│   │   │   ├── campaigns.py       # CRUD + orchestration
│   │   │   ├── collector.py       # Module 1: trigger Apify jobs
│   │   │   ├── analyzer.py        # Module 2: pattern engine
│   │   │   ├── generator.py       # Module 3: draft generation
│   │   │   ├── monitor.py         # Module 4: registration + status
│   │   │   ├── billing.py         # Stripe checkout + portal
│   │   │   └── onboarding.py      # Trial flow
│   │   ├── api/webhooks/
│   │   │   └── stripe.py          # Subscription lifecycle
│   │   ├── services/              # Business logic layer
│   │   │   ├── collector_service.py   # Orchestrate Apify + storage
│   │   │   ├── pattern_service.py     # ISC scoring + aggregation
│   │   │   ├── generator_service.py   # Draft generation pipeline
│   │   │   ├── monitor_service.py     # Shadowban detection
│   │   │   └── usage_service.py       # Plan limit enforcement
│   │   ├── inference/             # LLM abstraction
│   │   │   ├── client.py          # InferenceClient (OpenRouter)
│   │   │   ├── prompts/           # Prompt templates per task
│   │   │   └── cost_tracker.py    # Token usage tracking
│   │   ├── nlp/                   # Local NLP processing
│   │   │   ├── rhythm_analyzer.py # SpaCy sentence analysis
│   │   │   ├── regex_filters.py   # Regex-based filtering
│   │   │   └── blacklist_checker.py   # Syntax blacklist matching
│   │   ├── workers/               # Celery tasks
│   │   │   ├── celery_app.py      # Celery configuration
│   │   │   ├── collection_tasks.py    # Apify orchestration
│   │   │   ├── analysis_tasks.py      # Pattern aggregation
│   │   │   ├── monitoring_tasks.py    # HTTP checks (4h/1h)
│   │   │   └── email_tasks.py         # Resend integration
│   │   ├── integrations/          # External service clients
│   │   │   ├── apify_client.py    # Apify SDK wrapper
│   │   │   ├── stripe_client.py   # Stripe SDK wrapper
│   │   │   ├── supabase_client.py # Supabase service role
│   │   │   └── resend_client.py   # Resend email SDK
│   │   └── models/                # Pydantic schemas
│   │       ├── campaign.py
│   │       ├── post.py
│   │       ├── draft.py
│   │       └── monitor.py
│   ├── tests/
│   ├── migrations/                # SQL migrations
│   ├── Dockerfile                 # FastAPI + workers container
│   └── pyproject.toml             # Python dependencies
│
└── .planning/                     # Project planning files
```

### Structure Rationale

- **Frontend/Backend separation:** Vercel optimized for Next.js, Railway/Render for Python workers. No shared monorepo complexity.
- **Service layer isolation:** Business logic in `services/` keeps routes thin, testable, and reusable across API endpoints and workers.
- **Workers colocated with backend:** Celery tasks share `services/`, `integrations/`, and `nlp/` code. Single deployment target for backend logic.
- **Inference abstraction:** `inference/` layer prevents OpenRouter lock-in. Model swaps via config, not code changes.
- **Local NLP separation:** SpaCy processing in `nlp/` distinguishes zero-cost operations from LLM calls for cost control.

## Architectural Patterns

### Pattern 1: API-First with Async Workers

**What:** FastAPI returns task IDs immediately while Celery workers process long-running operations (scraping, analysis, monitoring).

**When to use:** Any operation taking >2 seconds (collection, analysis) or recurring tasks (monitoring cycles).

**Trade-offs:**
- **Pros:** Non-blocking API, horizontal scaling of workers, graceful degradation
- **Cons:** Complexity in task status polling, eventual consistency

**Example:**
```python
# FastAPI endpoint (returns immediately)
@router.post("/campaigns/{id}/collect")
async def trigger_collection(campaign_id: UUID, user: User = Depends(get_current_user)):
    # Validate plan limits synchronously
    usage_service.check_collection_limit(user.id)

    # Queue background task
    task = collection_tasks.run_apify_collection.delay(
        campaign_id=str(campaign_id),
        user_id=str(user.id)
    )

    return {"job_id": task.id, "status": "queued", "estimated_duration_seconds": 180}

# Celery worker (runs in background)
@celery_app.task
def run_apify_collection(campaign_id: str, user_id: str):
    # 1. Fetch campaign + keywords from Supabase
    # 2. Call Apify SDK with Reddit scraper actor
    # 3. Apply regex filtering (80% reduction)
    # 4. Process top 10% with LLM classification
    # 5. Store raw_posts with embeddings
    # 6. Update usage_tracking
    return {"total_collected": 234, "ai_processed": 23}
```

**Confidence:** HIGH - Verified via [Celery + FastAPI production guide](https://blog.greeden.me/en/2026/01/27/the-complete-guide-to-background-processing-with-fastapi-x-celery-redishow-to-separate-heavy-work-from-your-api-to-keep-services-stable/)

### Pattern 2: Event-Driven Data Pipeline

**What:** Data flows through transformations as events: `campaigns → raw_posts → community_profiles → generated_drafts → shadow_table → syntax_blacklist (feedback loop)`.

**When to use:** Multi-stage processing where each stage depends on prior stage completion but shouldn't block the user.

**Trade-offs:**
- **Pros:** Decoupled modules, each testable independently, replayable pipeline stages
- **Cons:** Harder to debug across stages, requires task dependencies in Celery

**Example:**
```python
# Pipeline stages as separate Celery tasks

# Stage 1: Collection (Module 1)
@celery_app.task
def run_apify_collection(campaign_id: str):
    # Apify → raw_posts table
    posts = apify_client.scrape_reddit(campaign_id)
    supabase.table("raw_posts").insert(posts).execute()

    # Trigger next stage
    run_pattern_analysis.delay(campaign_id)

# Stage 2: Analysis (Module 2)
@celery_app.task
def run_pattern_analysis(campaign_id: str):
    # raw_posts → community_profiles table
    posts = supabase.table("raw_posts").select("*").eq("campaign_id", campaign_id).execute()
    profile = pattern_service.aggregate_community_profile(posts)
    supabase.table("community_profiles").upsert(profile).execute()

# Stage 3: Generation (Module 3) - triggered by user action, not automatically
# User clicks "Generate Draft" → FastAPI endpoint → generator_service
# Reads community_profiles + syntax_blacklist → generates draft

# Stage 4: Monitoring (Module 4) - triggered when user posts draft
@celery_app.task
def register_monitor(draft_id: str, post_url: str):
    # generated_drafts → shadow_table
    # Celery Beat schedules periodic checks
    pass

# Feedback loop: shadow_table (removed) → syntax_blacklist
@celery_app.task
def audit_removed_post(shadow_id: str):
    # Extract forbidden patterns from removed post
    # Update syntax_blacklist for that subreddit
    pass
```

**Confidence:** HIGH - Standard pattern for [data pipelines](https://groupbwt.com/blog/web-scraping-in-data-science/), verified with Apify's [event-driven integration docs](https://docs.apify.com/platform/integrations)

### Pattern 3: Cost-Gated Inference with Fallback

**What:** InferenceClient abstraction routes LLM calls to cheapest suitable model, tracks costs in real-time, enforces plan caps, falls back on provider failure.

**When to use:** Any LLM call. Prevents vendor lock-in and cost overruns.

**Trade-offs:**
- **Pros:** Model swaps via config, automatic fallback, cost enforcement before call
- **Cons:** Extra abstraction layer, fallback model may have different quality

**Example:**
```python
# Abstraction prevents lock-in
class InferenceClient:
    def __init__(self, task: str):
        self.config = MODEL_ROUTING[task]  # From config, not hardcoded
        self.model = self.config["model"]
        self.fallback = self.config["fallback"]

    async def complete(self, prompt: str, user_id: str) -> dict:
        # 1. Check cost cap BEFORE calling API
        current_cost = usage_service.get_monthly_cost(user_id)
        plan_cap = COST_CAPS[user.plan]
        if current_cost >= plan_cap:
            raise PlanLimitReached("Token cost cap exceeded")

        # 2. Try primary model via OpenRouter
        try:
            response = await openrouter_client.complete(
                model=self.model,
                prompt=prompt,
                max_tokens=self.config["max_tokens"],
                temperature=self.config["temperature"]
            )
            tokens = response.usage.total_tokens
            cost = self._calculate_cost(tokens, self.model)
        except Exception as e:
            # 3. Fallback model on failure
            response = await openrouter_client.complete(
                model=self.fallback,
                prompt=prompt,
                max_tokens=self.config["max_tokens"],
                temperature=self.config["temperature"]
            )
            tokens = response.usage.total_tokens
            cost = self._calculate_cost(tokens, self.fallback)

        # 4. Track usage immediately
        usage_service.track_inference(user_id, tokens, cost, self.model)

        return {"content": response.choices[0].message.content, "tokens": tokens, "cost": cost}

# Usage in services
async def classify_archetype(post: RawPost, user_id: str) -> str:
    client = InferenceClient(task="classify_archetype")  # Auto-selects Haiku
    prompt = archetype_prompt.format(title=post.title, body=post.raw_text)
    result = await client.complete(prompt, user_id)
    return result["content"]
```

**Confidence:** HIGH - [OpenRouter model routing](https://openrouter.ai/) + [constrained decoding patterns](https://mbrenndoerfer.com/writing/constrained-decoding-structured-llm-output)

### Pattern 4: Dual-Session Monitoring for Shadowban Detection

**What:** Monitor service makes two HTTP requests per check: one authenticated (author's view), one anonymous (public view). Discrepancy = shadowban.

**When to use:** Reddit post monitoring (Module 4) where shadowbans are silent failures.

**Trade-offs:**
- **Pros:** Detects shadowbans (single-check misses them), no false positives
- **Cons:** 2x HTTP requests per check, requires session management

**Example:**
```python
@celery_app.task
def check_post_status(shadow_id: str):
    shadow_entry = supabase.table("shadow_table").select("*").eq("id", shadow_id).single().execute()
    post_url = shadow_entry.post_url

    # Check 1: Authenticated request (author's perspective)
    auth_response = requests.get(post_url, headers={"Cookie": REDDIT_AUTH_COOKIE})

    # Check 2: Anonymous request (public perspective)
    anon_response = requests.get(post_url)

    # Detection logic
    if auth_response.status_code == 200 and anon_response.status_code == 404:
        # Post visible to author but not public = shadowban
        status = "Shadowbanned"
        alert_service.send_emergency_alert(shadow_entry.user_id, "Shadowban detected")
    elif anon_response.status_code == 404:
        status = "Removido"
    elif anon_response.status_code == 200:
        status = "Ativo"
    else:
        status = "404"

    # Update shadow_table
    supabase.table("shadow_table").update({
        "status_vida": status,
        "last_check_status": anon_response.status_code,
        "last_check_at": datetime.now(),
        "total_checks": shadow_entry.total_checks + 1
    }).eq("id", shadow_id).execute()
```

**Confidence:** MEDIUM - Pattern derived from [BC-RAO spec defensive logic](https://github.com/bc-rao/spec), not found in general documentation. Requires validation with Reddit's actual behavior.

### Pattern 5: Tenant Isolation via RLS + JWT

**What:** Supabase Row-Level Security (RLS) enforces data isolation at database level. Every table filtered by `user_id = auth.uid()`. FastAPI validates JWT, Supabase enforces RLS.

**When to use:** Multi-tenant SaaS where data leakage is unacceptable.

**Trade-offs:**
- **Pros:** Defense-in-depth (can't bypass with broken API logic), automatic filtering, no application code changes
- **Cons:** Debugging harder (invisible filters), performance overhead on large datasets

**Example:**
```sql
-- RLS policy on campaigns table
CREATE POLICY "Users can only see their own campaigns"
ON campaigns
FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can only insert their own campaigns"
ON campaigns
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Same pattern for all user-scoped tables
-- raw_posts, community_profiles, generated_drafts, shadow_table, etc.
```

```python
# FastAPI middleware validates JWT
@router.get("/campaigns")
async def list_campaigns(user: User = Depends(get_current_user)):
    # No explicit user_id filter needed - Supabase RLS does it
    campaigns = supabase.table("campaigns").select("*").execute()
    return campaigns.data
```

**Confidence:** HIGH - [Supabase RLS multi-tenancy](https://www.antstack.com/blog/multi-tenant-applications-with-rls-on-supabase-postgress/) is standard pattern

## Data Flow

### Request Flow: User Action → API → Worker → Database

```
[User clicks "Collect Data"]
    ↓
[Next.js] POST /campaigns/:id/collect
    ↓
[FastAPI] Validates JWT, checks plan limits, queues Celery task
    ↓ (returns immediately with job_id)
[Next.js] Polls GET /campaigns/:id/collect/status
    ↓
[Celery Worker] Executes collection_tasks.run_apify_collection
    ↓
    1. Fetch campaign keywords from Supabase
    2. Call Apify SDK (scrape Reddit)
    3. Apify returns raw JSON (200-500 posts)
    4. Regex filter (Camada B: 80% reduction)
    5. Top 10% → LLM classification via InferenceClient
    6. Insert raw_posts with archetype + embedding
    7. Update usage_tracking
    ↓
[Celery Worker] Updates task status in Redis backend
    ↓
[Next.js] Polling detects completion, fetches raw_posts
```

### Module Pipeline Flow

```
MODULE 1 (Data Collector)
    campaigns → [Apify SDK] → raw_posts
                     ↓
              [Regex filter 80%]
                     ↓
              [LLM classify 10%]
                     ↓
            raw_posts.archetype populated

MODULE 2 (Pattern Engine)
    raw_posts → [SpaCy local analysis] → rhythm_metadata (sentence length, formality)
              → [LLM scoring] → success_score, engagement_score
              → [Aggregation] → community_profiles (per subreddit)
                                  • isc_score (Community Sensitivity Index)
                                  • avg_sentence_length
                                  • dominant_tone
                                  • archetype_distribution
                                  • forbidden_patterns

MODULE 3 (Conditioning Generator)
    User triggers: "Generate Draft"
    ↓
    1. [DB Query] Load community_profiles (subreddit)
    2. [DB Query] Load syntax_blacklist (subreddit)
    3. [Logic] Build dynamic prompt:
       - Archetype template (Journey/ProblemSolution/Feedback)
       - ISC gating (if >7.5, force Feedback mode)
       - Rhythm constraints (sentence length from profile)
       - Blacklist injection (forbidden patterns)
    4. [LLM call] InferenceClient.complete(prompt) → draft text
    5. [Post-processing]
       - Regex blacklist scan
       - Link density check
       - Jargon detection
    6. [DB Insert] generated_drafts with scores
    ↓
    generated_drafts.status = "generated"

MODULE 4 (Orchestrator)
    User posts draft manually, pastes URL
    ↓
    POST /monitor/register
    ↓
    1. [DB Insert] shadow_table with isc_at_post (snapshot)
    2. [Celery Beat] Schedules periodic checks:
       - New accounts: every 1 hour (first 3 posts)
       - Established: every 4 hours
    ↓
    [Celery Worker] monitoring_tasks.check_post_status
    ↓
    1. HTTP GET (authenticated) → author's view
    2. HTTP GET (anonymous) → public view
    3. Compare responses:
       - Both 200 → Ativo
       - Auth 200, Anon 404 → Shadowbanned (ALERT)
       - Both 404 → Removido
    4. [DB Update] shadow_table.status_vida
    5. If Removido → audit_removed_post → syntax_blacklist
    ↓
    FEEDBACK LOOP:
    syntax_blacklist (forbidden patterns) → MODULE 3 (generation constraints)
```

### Authentication Flow

```
[User signs up]
    ↓
[Next.js] POST /auth/signup → Supabase Auth
    ↓
[Supabase] Creates auth.users entry, returns JWT
    ↓
[FastAPI webhook or direct call] Creates profiles + subscriptions (trial)
    ↓
[Next.js] Stores JWT in cookie (Supabase SSR package)
    ↓
[User navigates to /campaigns]
    ↓
[Next.js Server Component] Reads JWT from cookie, passes to Supabase client
    ↓
[Supabase] Validates JWT, returns user_id
    ↓
[Next.js] Can query Supabase directly (RLS enforces user_id filter)
    OR
    Calls FastAPI with JWT in Authorization header
    ↓
[FastAPI] Validates JWT with SUPABASE_JWT_SECRET, extracts user_id
    ↓
[FastAPI] Uses service_role key for Supabase queries (RLS still enforced via user_id)
```

**Key insight:** Next.js can query Supabase directly for read-heavy operations (campaigns list, drafts list). FastAPI handles writes and orchestration (queue tasks, enforce limits). RLS prevents data leakage in both paths.

**Confidence:** HIGH - [Supabase Next.js integration](https://supabase.com/docs/guides/getting-started/quickstarts/nextjs) + [FastAPI JWT validation](https://medium.com/@ojasskapre/implementing-supabase-authentication-with-next-js-and-fastapi-5656881f449b)

### Key Data Flows

1. **Collection Flow:** User action → FastAPI queues task → Celery runs Apify SDK → Regex filter → LLM classify → Supabase raw_posts
2. **Analysis Flow:** raw_posts → Celery aggregates per subreddit → SpaCy local NLP → LLM scoring → Supabase community_profiles
3. **Generation Flow:** User action → FastAPI queries profiles + blacklist → InferenceClient builds prompt → LLM generates → Post-processing → Supabase generated_drafts
4. **Monitoring Flow:** Celery Beat triggers → Worker HTTP checks (dual-session) → Supabase shadow_table update → Email alerts if status change
5. **Feedback Loop:** shadow_table (removed) → Extract patterns → Supabase syntax_blacklist → MODULE 3 reads blacklist during generation

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-100 users | **Monolith is fine.** Single Railway dyno: FastAPI + Celery worker + Beat + Redis. Supabase free tier (500MB). Vercel hobby. Total cost: ~$20/month. |
| 100-1k users | **Horizontal worker scaling.** Separate Celery worker instances (2-3 workers). Redis scales vertically (Railway $10-20 plan). Supabase Pro ($25). Vercel Pro. Cost: ~$100-150/month. |
| 1k-10k users | **Database optimization.** Add indexes on `raw_posts(success_score DESC)`, `shadow_table(audit_due_at)`. Enable pgvector HNSW indexes for semantic search. Consider read replicas for dashboard queries. Separate Celery Beat from workers. Cost: ~$300-500/month. |
| 10k+ users | **Service disaggregation.** Separate inference service with its own Redis cache. Move monitoring to dedicated worker pool. Consider Supabase realtime subscriptions instead of polling. Evaluate Celery → Inngest migration for better observability. Cost: ~$1k-2k/month. |

### Scaling Priorities

1. **First bottleneck: Celery worker capacity**
   - **Symptoms:** Collection jobs queued for >5 minutes, monitoring checks delayed
   - **Fix:** Add horizontal workers (Railway allows 1-click scaling). Start with 2 workers, scale to 5-10 as needed.
   - **Cost:** $10-15 per worker dyno

2. **Second bottleneck: Database query performance**
   - **Symptoms:** Dashboard slow (>2s load), community profile aggregation times out
   - **Fix:** Add composite indexes: `(user_id, created_at DESC)`, `(campaign_id, success_score DESC)`. Enable pg_stat_statements for query analysis.
   - **Cost:** Supabase Pro required ($25/month), no additional cost for indexes

3. **Third bottleneck: OpenRouter rate limits**
   - **Symptoms:** 429 errors during batch processing
   - **Fix:** Implement exponential backoff in InferenceClient. Batch LLM calls (classify 10 posts per prompt instead of 1). Cache classification results.
   - **Cost:** Free (optimization only)

4. **Fourth bottleneck: Redis memory (Celery result backend)**
   - **Symptoms:** Task results evicted before frontend polls them
   - **Fix:** Configure `result_expires` (default 1 day → 1 hour). Scale Redis vertically (Railway 1GB → 2GB).
   - **Cost:** +$10/month for 2GB Redis

**Premature optimization to avoid:**
- Database sharding (not needed until 100k+ users)
- Microservices split (FastAPI + Celery workers sharing code is simpler)
- Custom worker orchestration (Celery Beat handles scheduling well)
- Read replicas (Supabase connection pooling sufficient until 10k users)

**Confidence:** MEDIUM-HIGH - Scaling patterns from [FastAPI production best practices](https://fastlaunchapi.dev/blog/fastapi-best-practices-production-2026) and [Celery scaling guides](https://docs.celeryq.dev/en/main/userguide/periodic-tasks.html)

## Anti-Patterns

### Anti-Pattern 1: Direct LLM Provider Imports

**What people do:**
```python
from openai import OpenAI  # ❌ Locked to OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

**Why it's wrong:** Vendor lock-in. Swapping providers requires code changes across services. Cost optimization blocked (can't A/B test cheaper models).

**Do this instead:**
```python
from app.inference import InferenceClient  # ✅ Abstraction layer
client = InferenceClient(task="classify_archetype")  # Config-driven routing
```

**Benefit:** Model swaps via environment variables. OpenRouter handles fallback, unified billing, model routing.

**Confidence:** HIGH - Core architectural principle from BC-RAO spec

---

### Anti-Pattern 2: Synchronous Scraping in API Endpoints

**What people do:**
```python
@router.post("/campaigns/{id}/collect")
async def collect_data(campaign_id: UUID):
    # ❌ Blocks request for 2-5 minutes
    posts = apify_client.scrape_reddit(campaign_id)
    return {"posts": posts}
```

**Why it's wrong:** Request timeout (FastAPI/Vercel: 30-60s max). User stares at loading spinner. Single-threaded scraping doesn't scale.

**Do this instead:**
```python
@router.post("/campaigns/{id}/collect")
async def collect_data(campaign_id: UUID):
    # ✅ Queue task, return immediately
    task = collection_tasks.run_apify_collection.delay(campaign_id)
    return {"job_id": task.id, "status": "queued"}
```

**Benefit:** Non-blocking API. Horizontal worker scaling. User gets progress updates via polling.

**Confidence:** HIGH - Standard pattern from [Celery + FastAPI guide](https://blog.greeden.me/en/2026/01/27/the-complete-guide-to-background-processing-with-fastapi-x-celery-redishow-to-separate-heavy-work-from-your-api-to-keep-services-stable/)

---

### Anti-Pattern 3: No Cost Tracking Before LLM Calls

**What people do:**
```python
async def generate_draft(user_id: str, prompt: str):
    # ❌ No cost check
    response = await openai_client.complete(prompt)
    # User exceeds $500 bill before limit enforced
```

**Why it's wrong:** Runaway costs. User can trigger $100+ bill in a single session. No recourse after tokens consumed.

**Do this instead:**
```python
async def generate_draft(user_id: str, prompt: str):
    # ✅ Check cost cap BEFORE API call
    current_cost = usage_service.get_monthly_cost(user_id)
    if current_cost >= COST_CAPS[user.plan]:
        raise PlanLimitReached()

    response = await inference_client.complete(prompt, user_id)
    # Tracks usage automatically
```

**Benefit:** Hard cost ceiling. 80% threshold warning. No surprise bills.

**Confidence:** HIGH - Critical for BC-RAO economics (COGS control)

---

### Anti-Pattern 4: Application-Level Tenant Filtering

**What people do:**
```python
@router.get("/campaigns")
async def list_campaigns(user: User = Depends(get_current_user)):
    # ❌ Relies on application logic
    campaigns = supabase.table("campaigns").select("*").eq("user_id", user.id).execute()
```

**Why it's wrong:** One forgotten `.eq("user_id", ...)` = data leak. Requires manual filtering in every query. Easy to bypass with SQL injection.

**Do this instead:**
```sql
-- ✅ Database-level enforcement via RLS
CREATE POLICY "Users see only their campaigns"
ON campaigns FOR SELECT
USING (auth.uid() = user_id);
```

```python
@router.get("/campaigns")
async def list_campaigns(user: User = Depends(get_current_user)):
    # No explicit filter needed - RLS does it
    campaigns = supabase.table("campaigns").select("*").execute()
```

**Benefit:** Defense-in-depth. Impossible to bypass. No manual filtering.

**Confidence:** HIGH - [Supabase RLS best practices](https://www.antstack.com/blog/multi-tenant-applications-with-rls-on-supabase-postgress/)

---

### Anti-Pattern 5: Single HTTP Check for Monitoring

**What people do:**
```python
# ❌ Misses shadowbans
response = requests.get(post_url)
if response.status_code == 200:
    status = "Ativo"
```

**Why it's wrong:** Shadowbans return 200 to author but 404 to public. False positive: "post is live" when actually invisible.

**Do this instead:**
```python
# ✅ Dual-session detection
auth_response = requests.get(post_url, headers={"Cookie": auth_cookie})
anon_response = requests.get(post_url)

if auth_response.status_code == 200 and anon_response.status_code == 404:
    status = "Shadowbanned"  # Critical alert
```

**Benefit:** Detects Reddit's silent moderation. No false positives. Early warning system.

**Confidence:** MEDIUM - BC-RAO spec defensive logic, requires validation

---

### Anti-Pattern 6: Storing Secrets in Frontend

**What people do:**
```typescript
// ❌ Next.js client component
const OPENROUTER_API_KEY = process.env.NEXT_PUBLIC_OPENROUTER_KEY;
```

**Why it's wrong:** `NEXT_PUBLIC_*` variables bundled in JavaScript, visible to all users. API keys leaked in browser DevTools.

**Do this instead:**
```typescript
// ✅ Next.js calls FastAPI, FastAPI holds secrets
const response = await fetch(`${API_URL}/drafts/generate`, {
    headers: { "Authorization": `Bearer ${supabaseToken}` }
});
```

**Benefit:** Secrets stay server-side. Supabase anon key is the only client-exposed key (designed for it).

**Confidence:** HIGH - Standard security practice

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **Apify** | Python SDK in Celery workers. Async actor execution with webhook callbacks. | Store actor run IDs in metadata for resumability. Configure proxy rotation for Reddit scraping. Enable result storage persistence (7 days). |
| **OpenRouter** | HTTP POST to `/chat/completions` via InferenceClient abstraction. | Set `http-referer` header (required for some models). Track usage via `x-ratelimit-*` headers. Configure fallback models in MODEL_ROUTING. |
| **Supabase** | Python `supabase-py` with service_role key in backend. JavaScript `@supabase/ssr` in Next.js. | Use service_role for admin operations (bypassing RLS when needed). Use anon key + JWT in frontend (RLS enforced). Enable realtime subscriptions for monitoring dashboard. |
| **Stripe** | Python `stripe` SDK. Webhook signature verification with `stripe.Webhook.construct_event()`. | Store `stripe_customer_id` and `stripe_subscription_id` in subscriptions table. Handle all 5 webhook events: checkout.completed, invoice.paid/failed, subscription.updated/deleted. |
| **Resend** | Python `resend` SDK. Transactional emails with Jinja2 templates. | Use `send_email()` in Celery tasks (never block API requests). Configure DNS records (SPF, DKIM) for deliverability. Track delivery status in email_alerts table. |
| **SpaCy** | Local Python library. Load `en_core_web_md` model once at worker startup. | Preload model in `celery_app.py` to avoid per-task overhead. Use `nlp.pipe()` for batch processing (10x faster than loop). Zero API cost. |
| **Redis** | Celery broker + result backend. Standard `redis://` connection string. | Configure `result_expires=3600` (1 hour) to prevent memory bloat. Use Redis DB 0 for broker, DB 1 for results (isolation). Enable persistence (AOF) for task durability. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **Next.js ↔ Supabase** | Direct DB queries via Supabase JS client. JWT in cookie, RLS enforced. | Use for read-heavy operations (campaign list, drafts). Server Components query Supabase directly. Client Components use realtime subscriptions. |
| **Next.js ↔ FastAPI** | REST API over HTTPS. JWT in `Authorization: Bearer` header. | Use for writes and orchestration (queue tasks, enforce limits). Polling for async task status. |
| **FastAPI ↔ Supabase** | Python `supabase-py` with service_role key. RLS bypassed only when needed (admin operations). | Manually set `X-User-Id` header when using service_role to preserve RLS intent. Use `postgrest-py` for raw SQL when Supabase client too limiting. |
| **FastAPI ↔ Celery** | Redis as message broker. Tasks queued via `.delay()`. | API returns task ID immediately. Frontend polls `/tasks/{id}/status` for completion. Use `task.get(timeout=0.1)` for instant status check (non-blocking). |
| **Celery Workers ↔ Supabase** | Same as FastAPI (service_role key). | Workers have full DB access. Use RLS policies + manual user_id filtering for safety. |
| **Services ↔ InferenceClient** | Internal Python abstraction. Synchronous or async depending on endpoint. | Service layer calls `InferenceClient(task="...").complete(prompt, user_id)`. Client handles routing, fallback, cost tracking. Services never import OpenAI/Anthropic directly. |
| **Modules 1-4 ↔ Database** | PostgreSQL as source of truth. Workers write, API reads, frontend polls. | No inter-module direct communication. All state transitions via DB updates. Enables module independence and testability. |

## Build Order Implications

### Phase 1: Foundation (Week 1-2)
**Goal:** User can sign up, see dashboard, create campaign.

**Components to build:**
1. Supabase setup (database, auth, RLS policies)
2. Next.js scaffold (auth pages, dashboard layout, Supabase client)
3. FastAPI scaffold (auth middleware, campaign CRUD endpoints)
4. Deploy pipeline (Vercel + Railway/Render)

**Why this order:** Auth + database are dependencies for everything else. Early deploy pipeline prevents "works on my machine" issues.

**Blockers if skipped:** Can't test API with real auth, can't verify RLS, can't demonstrate progress.

---

### Phase 2: Module 1 (Collection Pipeline) (Week 3)
**Goal:** User triggers collection, sees raw posts in dashboard.

**Components to build:**
1. Celery + Redis setup
2. Apify client integration
3. Collection worker (Apify → regex → storage)
4. FastAPI collector endpoint (queue task, return job_id)
5. Next.js collection UI (trigger, poll status)

**Why this order:** Celery infrastructure needed for all async work. Apify is data source for entire pipeline.

**Blockers if skipped:** No data to analyze (Module 2 blocked), no drafts to generate (Module 3 blocked).

---

### Phase 3: Module 2 (Pattern Engine) (Week 4)
**Goal:** Raw posts analyzed, community profiles generated, ISC scores visible.

**Components to build:**
1. SpaCy NLP analyzer (local processing)
2. InferenceClient abstraction (LLM routing)
3. Pattern service (aggregation logic)
4. Analysis worker (posts → profiles)
5. FastAPI analyzer endpoint
6. Next.js community profile UI

**Why this order:** Depends on Module 1 data. Provides context for Module 3 generation.

**Blockers if skipped:** No community intelligence (Module 3 generates blind), no ISC gating.

---

### Phase 4: Module 3 (Draft Generation) (Week 5)
**Goal:** User generates drafts conditioned on community profiles + blacklist.

**Components to build:**
1. Generator service (prompt building, blacklist checking)
2. Prompt templates (archetype-specific)
3. Draft generation endpoint
4. Next.js draft editor UI
5. Cost tracking (usage_tracking updates)

**Why this order:** Depends on Module 2 profiles. Critical path to user value.

**Blockers if skipped:** User has data but can't act on it (incomplete loop).

---

### Phase 5: Module 4 (Monitoring + Feedback) (Week 6)
**Goal:** User registers posted drafts, receives alerts, blacklist updated on removals.

**Components to build:**
1. Monitor service (dual-session HTTP checks)
2. Monitoring workers (Celery Beat scheduled)
3. Email service (Resend integration)
4. Shadowban detection logic
5. Feedback loop (removed post → blacklist)
6. Next.js monitoring dashboard
7. Alert email templates

**Why this order:** Completes the loop (generation → post → monitor → learn).

**Blockers if skipped:** No feedback loop (system doesn't learn), no shadowban detection (silent failure).

---

### Phase 6: Billing + Limits (Week 7)
**Goal:** Trial expires, user upgrades, plan limits enforced.

**Components to build:**
1. Stripe integration (checkout, portal, webhooks)
2. Usage service (limit enforcement)
3. Subscription lifecycle (trial → paid → cancelled)
4. Plan limit checks in all endpoints
5. Next.js billing UI (upgrade prompt, usage stats)
6. Trial reminder emails

**Why this order:** Monetization layer. Can be built in parallel with Modules 3-4 if needed.

**Blockers if skipped:** No revenue. Can launch as free beta, but not sustainable.

---

### Critical Path Dependencies

```
Phase 1 (Foundation)
    ↓
Phase 2 (Module 1: Collection)
    ↓
Phase 3 (Module 2: Analysis)
    ↓
Phase 4 (Module 3: Generation)
    ↓
Phase 5 (Module 4: Monitoring)

Phase 6 (Billing) can run in parallel with Phases 3-5
```

**Earliest viable demo:** End of Phase 4 (can generate conditioned drafts, but no monitoring yet).

**Earliest revenue-generating launch:** End of Phase 6 (full loop + billing).

**Recommended MVP:** Phases 1-5 (full loop, manual payment for early adopters), then add Phase 6 for self-service.

---

## Sources

### Architecture Patterns
- [Celery + Redis + FastAPI Production Guide 2025](https://medium.com/@dewasheesh.rana/celery-redis-fastapi-the-ultimate-2025-production-guide-broker-vs-backend-explained-5b84ef508fa7)
- [Complete Guide to Background Processing with FastAPI × Celery](https://blog.greeden.me/en/2026/01/27/the-complete-guide-to-background-processing-with-fastapi-x-celery-redishow-to-separate-heavy-work-from-your-api-to-keep-services-stable/)
- [FastAPI Best Practices for Production: Complete 2026 Guide](https://fastlaunchapi.dev/blog/fastapi-best-practices-production-2026)

### Data Pipeline Architecture
- [Web Scraping in Data Science: Architecture & ML Pipelines](https://groupbwt.com/blog/web-scraping-in-data-science/)
- [Web Scraping Infrastructure 2026](https://blog.apify.com/web-scraping-infrastructure/)
- [Apify Platform Integrations](https://docs.apify.com/platform/integrations)

### LLM Architecture
- [Constrained Decoding: Grammar-Guided Generation for Structured LLM Output](https://mbrenndoerfer.com/writing/constrained-decoding-structured-llm-output)
- [Controlling your LLM: Deep dive into Constrained Generation](https://medium.com/@docherty/controlling-your-llm-deep-dive-into-constrained-generation-1e561c736a20)

### Integration Patterns
- [Implementing Supabase Authentication with Next.js and FastAPI](https://medium.com/@ojasskapre/implementing-supabase-authentication-with-next-js-and-fastapi-5656881f449b)
- [Use Supabase with Next.js - Official Docs](https://supabase.com/docs/guides/getting-started/quickstarts/nextjs)
- [Multi-Tenant Applications with RLS on Supabase](https://www.antstack.com/blog/multi-tenant-applications-with-rls-on-supabase-postgress/)

### Task Scheduling
- [Celery Periodic Tasks - Official Docs](https://docs.celeryq.dev/en/main/userguide/periodic-tasks.html)
- [Celery Beat: Complete Guide to Python Task Scheduling](https://spice.alibaba.com/spice-basics/celery-beat)

---
*Architecture research for: BC-RAO social intelligence platform*
*Researched: 2026-02-07*
