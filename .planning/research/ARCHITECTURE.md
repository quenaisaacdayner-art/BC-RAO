# Architecture Research

**Domain:** Reddit Content Generation / Community Mimicry Tools
**Researched:** 2026-02-07
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                              │
│  Next.js 15 (SSR/ISR) + Edge Functions (Auth) → Vercel              │
├─────────────────────────────────────────────────────────────────────┤
│                          API GATEWAY                                 │
│  FastAPI (async HTTP endpoints) → Railway                           │
├─────────────────────────────────────────────────────────────────────┤
│                       ASYNC TASK LAYER                               │
│  Celery Workers (long-running tasks) + Beat (scheduler)             │
│  Redis (broker + result backend)                                    │
├─────────────────────────────────────────────────────────────────────┤
│                       PROCESSING PIPELINE                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │
│  │  Collector │→ │   Pattern  │→ │ Generator  │→ │  Monitor   │   │
│  │  (Module 1)│  │   Engine   │  │ (Module 3) │  │ (Module 4) │   │
│  │            │  │ (Module 2) │  │            │  │            │   │
│  │ Apify API  │  │  SpaCy NLP │  │ LLM (via   │  │ Reddit API │   │
│  │ → Regex    │  │  → Scoring │  │ OpenRouter)│  │ → Analytics│   │
│  │ → AI Class │  │  → Profile │  │ → Filters  │  │ → Shadowban│   │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘   │
├─────────────────────────────────────────────────────────────────────┤
│                       DATA PERSISTENCE                               │
│  Supabase PostgreSQL (with RLS) + Auth                              │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Frontend (Next.js)** | User interface, dashboards, real-time updates | SSR for SEO, ISR for data pages, Edge Functions for auth checks |
| **API Gateway (FastAPI)** | HTTP endpoints, request validation, orchestration | Async endpoints, Pydantic models, dependency injection |
| **Task Queue (Celery)** | Async job execution, scheduling, retry logic | Workers with gevent/async pool, Beat for cron jobs |
| **Collector (Module 1)** | Reddit scraping, content classification, archetype detection | Apify API client → Regex filters → LLM classifier → DB storage |
| **Pattern Engine (Module 2)** | NLP analysis, rhythm scoring, community profiling | SpaCy pipeline → Weight matrix → ISC score calculation |
| **Generator (Module 3)** | LLM-powered content generation, mimicry filtering | Profile input → Blacklist check → LLM prompt → Post-processing |
| **Monitor (Module 4)** | Post tracking, shadowban detection, engagement analytics | Periodic checks → Visibility tests → Alert generation |
| **Database (Supabase)** | Structured data storage, user auth, RLS enforcement | PostgreSQL with migrations, RLS policies, auth integration |
| **Cache/Broker (Redis)** | Celery task broker, result backend, rate limiting | Redis 7 with persistence for task queue reliability |

## Recommended Project Structure

```
bc-rao/                              # Monorepo root
├── apps/
│   ├── web/                         # Next.js 15 frontend
│   │   ├── app/                     # App Router (RSC)
│   │   │   ├── (auth)/              # Auth routes (grouped)
│   │   │   ├── (dashboard)/         # Dashboard routes
│   │   │   │   ├── campaigns/       # Campaign management
│   │   │   │   ├── drafts/          # Draft editing
│   │   │   │   ├── monitoring/      # Post monitoring
│   │   │   │   └── analytics/       # ISC scores, insights
│   │   │   └── api/                 # Route handlers (if needed)
│   │   ├── components/              # Shared UI components
│   │   │   ├── ui/                  # Base components
│   │   │   ├── campaigns/           # Campaign-specific
│   │   │   ├── drafts/              # Draft-specific
│   │   │   └── monitoring/          # Monitor-specific
│   │   ├── lib/                     # Client utilities
│   │   │   ├── api-client.ts        # API wrapper
│   │   │   ├── auth.ts              # Supabase auth
│   │   │   └── hooks/               # React hooks
│   │   └── __tests__/               # Vitest tests
│   │
│   └── api/                         # FastAPI backend
│       ├── app/
│       │   ├── main.py              # FastAPI app entry
│       │   ├── api/                 # HTTP endpoints
│       │   │   ├── v1/              # API v1 routes
│       │   │   │   ├── campaigns.py
│       │   │   │   ├── drafts.py
│       │   │   │   ├── monitoring.py
│       │   │   │   └── billing.py
│       │   ├── workers/             # Celery tasks
│       │   │   ├── celery_app.py    # Celery config
│       │   │   ├── collector.py     # Module 1 tasks
│       │   │   ├── analyzer.py      # Module 2 tasks
│       │   │   ├── generator.py     # Module 3 tasks
│       │   │   └── monitor.py       # Module 4 tasks
│       │   ├── services/            # Business logic
│       │   │   ├── collector/       # Module 1 services
│       │   │   │   ├── apify_client.py
│       │   │   │   ├── regex_classifier.py
│       │   │   │   └── ai_classifier.py
│       │   │   ├── analyzer/        # Module 2 services
│       │   │   │   ├── spacy_analyzer.py
│       │   │   │   ├── scoring_engine.py
│       │   │   │   └── profiler.py
│       │   │   ├── generator/       # Module 3 services
│       │   │   │   ├── llm_client.py
│       │   │   │   ├── blacklist_checker.py
│       │   │   │   └── mimicry_filter.py
│       │   │   └── monitor/         # Module 4 services
│       │   │       ├── reddit_client.py
│       │   │       ├── shadowban_detector.py
│       │   │       └── alert_service.py
│       │   ├── models/              # SQLAlchemy models
│       │   ├── schemas/             # Pydantic schemas
│       │   └── core/                # Config, dependencies
│       ├── tests/                   # Pytest tests
│       │   ├── unit/
│       │   ├── integration/
│       │   └── e2e/
│       ├── migrations/              # Supabase SQL migrations
│       └── pyproject.toml           # Poetry dependencies
│
├── packages/
│   └── shared/                      # Shared types/constants
│       ├── types/                   # TypeScript/Python types
│       └── constants/               # Enums, configs
│
├── .github/
│   └── workflows/                   # CI/CD workflows
│       ├── ci.yml                   # Lint + tests
│       ├── e2e.yml                  # E2E after Vercel preview
│       └── smoke.yml                # Smoke tests after prod
│
├── turbo.json                       # Turborepo config
├── package.json                     # Root workspace
├── docker-compose.yml               # Local dev environment
└── README.md
```

### Structure Rationale

- **Monorepo (Turborepo):** Single repository containing both frontend and backend enables shared types, unified CI/CD, and coherent preview environments. Changes to API contracts are visible in a single PR.
- **apps/web/:** Next.js 15 App Router structure with route grouping for auth and dashboard sections. Server Components for data fetching, Client Components for interactivity.
- **apps/api/:** Clean architecture with separation of concerns: HTTP layer (api/), async tasks (workers/), business logic (services/), data models (models/schemas/).
- **Module-based services/:** Each of the 4 core modules has its own service folder with clear boundaries and responsibilities.
- **Shared packages/:** Type definitions and constants shared between frontend and backend maintain contract consistency.

## Architectural Patterns

### Pattern 1: Event-Driven Async Pipeline

**What:** Reddit content generation follows an event-driven pipeline where each module triggers the next via Celery tasks, with state persisted to PostgreSQL between stages.

**When to use:** For long-running, multi-stage data processing workflows where each stage may take minutes and can fail independently.

**Trade-offs:**
- Pros: Resilient to failures (retry logic), scalable (add workers), non-blocking (user gets immediate response)
- Cons: Added complexity (async debugging), eventual consistency (results not instant), infrastructure overhead (Redis required)

**Example:**
```python
# Celery task chaining: Collection → Analysis → Generation
from celery import chain

# User triggers campaign
campaign_id = create_campaign(user_id, subreddit="SaaS")

# Chain tasks: each passes output to next
pipeline = chain(
    collect_posts.s(campaign_id, subreddit="SaaS"),  # Module 1
    analyze_patterns.s(campaign_id),                 # Module 2
    generate_draft.s(campaign_id, prompt="..."),     # Module 3
)
pipeline.apply_async()

# User sees: "Campaign started, we'll notify you when draft is ready"
# System: Runs tasks in background, stores results, sends alert
```

### Pattern 2: Modular Pipeline with Clear Boundaries

**What:** Each of the 4 modules (Collector, Pattern Engine, Generator, Monitor) operates independently with well-defined inputs/outputs and can be tested, deployed, and scaled separately.

**When to use:** For complex data processing pipelines where different stages have different computational requirements and scaling needs.

**Trade-offs:**
- Pros: Testability (mock interfaces), maintainability (isolated changes), scalability (scale expensive modules independently)
- Cons: Over-engineering risk for simple flows, interface contracts must be maintained, integration testing required

**Example:**
```python
# Module interfaces are clearly defined

# Module 1: Collector
class CollectorService:
    def collect(self, subreddit: str) -> List[RawPost]:
        """Scrape Reddit via Apify, classify posts"""
        pass

# Module 2: Pattern Engine
class PatternEngine:
    def analyze(self, posts: List[RawPost]) -> CommunityProfile:
        """NLP analysis → ISC score → profile"""
        pass

# Module 3: Generator
class GeneratorService:
    def generate(self, profile: CommunityProfile, prompt: str) -> Draft:
        """LLM generation with mimicry constraints"""
        pass

# Module 4: Monitor
class MonitorService:
    def track(self, post: RegisteredPost) -> PostStatus:
        """Track engagement, detect shadowban"""
        pass

# Each module can be tested/mocked independently
```

### Pattern 3: Retrieval-Augmented Generation (RAG) for Context

**What:** LLM generation (Module 3) uses RAG pattern: retrieve successful post examples from database, inject into prompt context, generate content that mimics patterns.

**When to use:** When LLM needs to generate content that matches specific stylistic patterns or domain knowledge not in training data.

**Trade-offs:**
- Pros: Better mimicry (grounded in real examples), reduced hallucination, dynamic context (learns from new data)
- Cons: Retrieval latency, prompt token cost (examples consume input tokens), embedding infrastructure (if using vector search)

**Example:**
```python
# RAG pattern in Generator module

async def generate_draft(profile: CommunityProfile, user_prompt: str) -> Draft:
    # 1. Retrieve: Get top performing posts matching profile
    similar_posts = db.query(RawPost).filter(
        RawPost.subreddit == profile.subreddit,
        RawPost.upvote_ratio > 0.85,
        RawPost.archetype.in_(["Solution", "Feedback"])
    ).order_by(RawPost.upvotes.desc()).limit(5).all()

    # 2. Augment: Inject examples into prompt
    examples = "\n".join([f"- {p.title} ({p.upvotes} upvotes)" for p in similar_posts])

    enhanced_prompt = f"""
    Community: r/{profile.subreddit}
    ISC Score: {profile.isc_score}
    Writing Style: {profile.dominant_tone}, avg {profile.avg_sentence_length} words/sentence

    Successful post examples:
    {examples}

    User's topic: {user_prompt}

    Generate a post title that matches this community's style.
    """

    # 3. Generate: Call LLM with augmented context
    response = await llm_client.complete(enhanced_prompt)

    return Draft(content=response.content, profile_id=profile.id)
```

### Pattern 4: Worker Pool with Task Routing

**What:** Celery workers are organized into specialized queues (scraping, NLP, generation, monitoring) with different concurrency settings optimized for each task type.

**When to use:** When different task types have different resource requirements (I/O-bound vs CPU-bound vs memory-intensive).

**Trade-offs:**
- Pros: Resource optimization (CPU-intensive NLP gets fewer workers), priority control (urgent tasks in fast queue), failure isolation (NLP crash doesn't block scraping)
- Cons: Configuration complexity, over-optimization risk for low traffic, monitoring overhead (multiple queues)

**Example:**
```python
# Celery config with task routing

CELERY_ROUTES = {
    'app.workers.collector.*': {'queue': 'scraping'},      # I/O-bound, high concurrency
    'app.workers.analyzer.*': {'queue': 'nlp'},            # CPU-bound, low concurrency
    'app.workers.generator.*': {'queue': 'generation'},    # LLM API, medium concurrency
    'app.workers.monitor.*': {'queue': 'monitoring'},      # I/O-bound, medium concurrency
}

# Railway services (different worker configs)
# Worker 1: scraping queue, concurrency=10 (lightweight I/O)
# Worker 2: nlp queue, concurrency=2 (CPU-intensive SpaCy)
# Worker 3: generation queue, concurrency=4 (API calls)
# Worker 4: monitoring queue, concurrency=6 (periodic checks)
```

## Data Flow

### Request Flow: Campaign Creation → Draft Generation

```
[User Action: Create Campaign]
    ↓
[Next.js API Route Handler]
    ↓ (HTTP POST /api/v1/campaigns)
[FastAPI Endpoint: POST /campaigns]
    ↓ (Validate request, check plan limits)
[Create campaign record in DB]
    ↓ (Trigger async pipeline)
[Celery: collect_posts.delay(campaign_id)]
    ↓
┌─────────────────────────────────────────┐
│ ASYNC PIPELINE (Celery Workers)         │
│                                          │
│ Module 1: Collector                     │
│   → Apify API (scrape Reddit)           │
│   → Regex classification (archetype)    │
│   → AI classification (confidence)      │
│   → Store raw_posts table               │
│   ↓                                      │
│ Module 2: Pattern Engine                │
│   → Load SpaCy model                    │
│   → Analyze rhythm patterns             │
│   → Calculate ISC score                 │
│   → Store community_profile table       │
│   ↓                                      │
│ Module 3: Generator                     │
│   → Retrieve profile + examples (RAG)   │
│   → Check syntax blacklist              │
│   → Call LLM (OpenRouter)               │
│   → Apply mimicry filters               │
│   → Store generated_drafts table        │
│   ↓                                      │
│ [Send notification: Draft ready]        │
└─────────────────────────────────────────┘
    ↓
[User views draft in dashboard]
    ↓ (HTTP GET /drafts/:id)
[FastAPI returns draft with profile data]
    ↓
[Next.js renders draft editor]
```

### State Management: Real-Time Updates

```
[Database State Change]
    ↓
[Supabase Realtime (PostgreSQL LISTEN/NOTIFY)]
    ↓
[Next.js subscribes to changes via Supabase client]
    ↓
[React state update → UI re-render]

Example: Campaign status updates in real-time as workers progress through pipeline
```

### Key Data Flows

1. **Collection Flow (Module 1):**
   - User input (subreddit) → Apify API call → JSON response → Regex filter (archetype) → LLM classifier (confidence) → PostgreSQL (raw_posts table) → Trigger Module 2

2. **Analysis Flow (Module 2):**
   - Load raw_posts → SpaCy NLP pipeline (tokenize, POS tag, dependency parse) → Rhythm analysis (sentence length, clause density) → Scoring engine (weight matrix) → Calculate ISC score → PostgreSQL (community_profiles table) → Trigger Module 3

3. **Generation Flow (Module 3):**
   - Load community_profile → Retrieve top posts (RAG) → Check user_blacklist (syntax/topics) → Build LLM prompt → OpenRouter API call → Parse response → Apply mimicry filters (ISC match, tone match) → PostgreSQL (generated_drafts table) → Send notification

4. **Monitoring Flow (Module 4):**
   - Celery Beat (cron: every 4h) → Load active_posts → Reddit API (fetch metrics) → Compare baseline → Detect anomalies (shadowban heuristics) → Update post_status → Send alert if degraded

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| **0-100 users** | Single Railway instance for API + worker, Supabase free tier, Redis on Railway. Current architecture is sufficient. |
| **100-1k users** | Separate worker service from API (already planned), increase Celery worker concurrency (2→6), enable Redis persistence, upgrade Supabase to Pro (connection pooling). |
| **1k-10k users** | Horizontal scaling: 2-3 worker instances, queue-based routing (scraping/nlp/generation queues), caching layer (Redis) for community profiles, database read replicas for analytics queries. |
| **10k-100k users** | Add dedicated NLP worker pool (CPU-optimized), implement job prioritization (paid users first), database partitioning (by user_id), CDN for static assets, consider background job batching. |
| **100k+ users** | Microservices: Split modules into separate services, message broker upgrade (Redis → RabbitMQ/Kafka), distributed tracing (OpenTelemetry), dedicated monitoring service, multi-region deployment. |

### Scaling Priorities

1. **First bottleneck (500-1k users):** Celery workers hit concurrency limit during peak hours.
   - **Fix:** Increase worker instances from 1 to 3, enable autoscaling on Railway based on queue depth.
   - **Cost:** ~$30/month additional worker capacity.

2. **Second bottleneck (2k-5k users):** SpaCy NLP analysis (Module 2) becomes CPU bottleneck.
   - **Fix:** Dedicated worker pool for NLP tasks with CPU-optimized instances, batch multiple posts per analysis job.
   - **Cost:** ~$50/month for 2 CPU-optimized workers.

3. **Third bottleneck (5k-10k users):** LLM API rate limits (OpenRouter).
   - **Fix:** Implement request queuing with exponential backoff, cache generated content for similar prompts, consider multi-provider fallback (OpenRouter → Anthropic direct).
   - **Cost:** Minimal (optimization, not infrastructure).

4. **Fourth bottleneck (10k+ users):** Database connections exhausted.
   - **Fix:** Supabase Pro with Supavisor connection pooling (10k concurrent connections), implement connection pooling in FastAPI (SQLAlchemy pool_size).
   - **Cost:** Supabase Pro $25/month.

## Anti-Patterns

### Anti-Pattern 1: Synchronous API Calls in HTTP Endpoints

**What people do:** Call Apify API or OpenRouter directly in FastAPI endpoint, make user wait 30s-5min for response.

**Why it's wrong:** HTTP request timeout (30s Vercel limit), poor UX (frozen UI), wasted resources (connection held open), cascade failures (API timeout breaks entire request).

**Do this instead:** Always offload long-running tasks to Celery. Return immediate response with task_id, let user poll or use websockets for updates.

```python
# ❌ BAD: Synchronous long-running task
@app.post("/campaigns")
async def create_campaign(subreddit: str):
    posts = await apify_client.scrape(subreddit)  # Takes 3-5 minutes!
    profile = analyzer.analyze(posts)              # Takes 30-60 seconds!
    draft = await generator.generate(profile)      # Takes 10-20 seconds!
    return {"draft": draft}  # User waited 5+ minutes

# ✅ GOOD: Async task with immediate response
@app.post("/campaigns")
async def create_campaign(subreddit: str):
    campaign = db.create(subreddit=subreddit, status="pending")
    collect_posts.delay(campaign.id)  # Offload to Celery
    return {"campaign_id": campaign.id, "status": "pending"}
```

### Anti-Pattern 2: Loading SpaCy Model on Every Request

**What people do:** Initialize SpaCy model (`spacy.load("en_core_web_md")`) inside the analysis function, 40MB model loaded from disk each time.

**Why it's wrong:** Extreme latency (2-3s per load), memory waste, disk I/O contention, worker startup slowdown.

**Do this instead:** Load model once at worker startup, store in global/class variable, reuse across tasks.

```python
# ❌ BAD: Load model per request
def analyze_rhythm(text: str):
    nlp = spacy.load("en_core_web_md")  # 2-3 seconds, 40MB RAM
    doc = nlp(text)
    return calculate_scores(doc)

# ✅ GOOD: Load model at startup
import spacy

# Global variable, loaded once when worker starts
NLP_MODEL = spacy.load("en_core_web_md")

def analyze_rhythm(text: str):
    doc = NLP_MODEL(text)  # Instant
    return calculate_scores(doc)
```

### Anti-Pattern 3: Storing Raw Reddit HTML/JSON in Database

**What people do:** Store entire Apify JSON response (with HTML, metadata, nested objects) in PostgreSQL text column.

**Why it's wrong:** Database bloat (posts table grows to GB), slow queries (no indexing on JSON), wasted storage cost, difficult analytics (can't query structured data).

**Do this instead:** Parse JSON, extract only needed fields, store in structured columns with proper indexes.

```python
# ❌ BAD: Store raw JSON
raw_post = {
    "title": "How I...",
    "selftext": "...",
    "html": "<div>...</div>",  # Large HTML blob
    "author": {...},            # Nested object
    "media": {...},             # Nested object
    "full_apify_response": {...}  # Entire API response
}
db.execute("INSERT INTO posts (data) VALUES (?)", json.dumps(raw_post))

# ✅ GOOD: Extract structured data
db.execute("""
    INSERT INTO raw_posts (title, content, author, upvotes, created_at, url, archetype)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    raw_post["title"],
    raw_post["selftext"],
    raw_post["author"]["name"],
    raw_post["ups"],
    raw_post["created_utc"],
    raw_post["permalink"],
    classify_archetype(raw_post["title"])
))
```

### Anti-Pattern 4: Polling Database for Task Status

**What people do:** Frontend polls `/tasks/:id/status` every 2 seconds to check if Celery task finished.

**Why it's wrong:** Database hammering (100s of queries per user), wasted bandwidth, poor UX (2s delay), scaling issue (N users = N*30 queries/minute).

**Do this instead:** Use Supabase Realtime (PostgreSQL LISTEN/NOTIFY) for push-based updates, or WebSockets for task progress.

```typescript
// ❌ BAD: Polling
const checkStatus = async () => {
  const interval = setInterval(async () => {
    const res = await fetch(`/api/tasks/${taskId}/status`)
    const data = await res.json()
    if (data.status === 'complete') {
      clearInterval(interval)
      showDraft(data.result)
    }
  }, 2000)  // Hammers DB every 2 seconds
}

// ✅ GOOD: Supabase Realtime (push-based)
const supabase = createClient(...)
supabase
  .channel('campaigns')
  .on('postgres_changes', {
    event: 'UPDATE',
    schema: 'public',
    table: 'campaigns',
    filter: `id=eq.${campaignId}`
  }, (payload) => {
    if (payload.new.status === 'complete') {
      showDraft(payload.new.draft_id)
    }
  })
  .subscribe()
```

### Anti-Pattern 5: Generating Content Without Blacklist Enforcement

**What people do:** Pass user prompt directly to LLM without checking blacklist, post gets generated with forbidden syntax/topics.

**Why it's wrong:** User wastes generation credit, content violates community rules, account at risk of ban, poor user experience.

**Do this instead:** Check blacklist BEFORE generation, show validation errors, let user fix prompt.

```python
# ❌ BAD: Generate without validation
async def generate_draft(campaign_id: int, prompt: str):
    profile = db.get_profile(campaign_id)
    draft = await llm_client.generate(profile, prompt)
    return draft  # May contain blacklisted patterns

# ✅ GOOD: Validate before generation
async def generate_draft(campaign_id: int, prompt: str):
    profile = db.get_profile(campaign_id)
    blacklist = db.get_blacklist(campaign_id)

    # Check prompt against blacklist
    violations = blacklist_checker.check(prompt, blacklist)
    if violations:
        raise ValidationError(f"Prompt contains forbidden patterns: {violations}")

    # Generate
    draft = await llm_client.generate(profile, prompt)

    # Post-process: Verify generated content matches ISC constraints
    if not mimicry_filter.matches_profile(draft.content, profile):
        # Regenerate with stronger constraints
        draft = await llm_client.generate(profile, prompt, strict=True)

    return draft
```

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **Apify** | REST API via Actor calls | Rate limit: 100 calls/hour (free tier). Use exponential backoff. Store actor_run_id for status polling. |
| **OpenRouter** | REST API via `/api/v1/chat/completions` | Multi-provider fallback: Claude 3.5 Sonnet → GPT-4 → Llama 3. Track costs per user in usage_tracking table. |
| **Supabase** | PostgreSQL client + Realtime subscriptions | Use connection pooling (SQLAlchemy), enable RLS policies, subscribe to table changes for real-time UI updates. |
| **Reddit API** | REST API via PRAW (Python Reddit API Wrapper) | OAuth2 flow for user's Reddit account. Rate limit: 60 requests/minute. Cache post data to reduce calls. |
| **Stripe** | Webhook events via `/billing/webhooks/stripe` | Verify webhook signature, handle `invoice.paid`, `customer.subscription.updated`, `customer.subscription.deleted`. |
| **Resend** | SMTP or REST API for transactional emails | Template-based emails for draft ready, shadowban alert, trial ending. Retry logic for failed sends. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **Frontend ↔ Backend** | REST API (JSON over HTTPS) | Next.js Route Handlers proxy to FastAPI. Auth via Supabase JWT in `Authorization: Bearer` header. |
| **API ↔ Workers** | Celery tasks via Redis | API enqueues tasks with `.delay()`, workers execute async, results stored in Redis or PostgreSQL. |
| **Workers ↔ Database** | SQLAlchemy ORM (async) | Connection pooling (pool_size=10), transactions for multi-step operations, bulk inserts for scraped data. |
| **Module 1 ↔ Module 2** | Database state + Celery chain | Module 1 stores raw_posts, triggers Module 2 task with campaign_id. Module 2 reads posts, stores profile. |
| **Module 2 ↔ Module 3** | Database state + Celery chain | Module 2 stores community_profile, triggers Module 3 task. Module 3 retrieves profile, generates draft. |
| **Module 3 ↔ Module 4** | User action (manual trigger) | User approves draft, clicks "Post & Monitor". Module 4 registers post, starts periodic checks. |
| **Frontend ↔ Supabase** | Direct PostgreSQL connection (RLS enforced) | Next.js calls Supabase client for auth, real-time subscriptions. RLS policies ensure user can only access own data. |

## Component Build Order & Dependencies

Based on the architecture analysis, here's the recommended build order with dependency rationale:

### Phase 1: Foundation (Week 1-2)
**Build Order:**
1. Database schema & migrations (Supabase)
2. FastAPI app skeleton with auth middleware
3. Celery setup with Redis connection
4. Next.js app with Supabase auth

**Why this order:**
- Database schema defines data contracts for all modules
- Auth layer required for any protected endpoints
- Celery infrastructure needed before async tasks
- Frontend can start building UI once API endpoints are defined

**Validation:**
- User can sign up, log in, see empty dashboard
- API health check endpoint returns 200
- Celery worker connects to Redis, processes test task

### Phase 2: Module 1 - Collector (Week 3-4)
**Build Order:**
1. Apify client service
2. Regex archetype classifier
3. AI archetype classifier (OpenRouter integration)
4. Celery task: collect_posts
5. Frontend: Campaign creation form

**Dependencies:**
- Requires: Database (raw_posts table), Celery, auth
- Blocks: Module 2 (needs collected posts)

**Validation:**
- User creates campaign, Apify scrapes Reddit
- Posts classified with archetype labels
- raw_posts table populated with 100+ posts

### Phase 3: Module 2 - Pattern Engine (Week 5-6)
**Build Order:**
1. SpaCy integration (load model)
2. Rhythm analyzer service
3. Scoring engine (weight matrix)
4. Profiler service (aggregate metrics)
5. Celery task: analyze_patterns
6. Frontend: Community profile display

**Dependencies:**
- Requires: Module 1 (raw_posts data)
- Blocks: Module 3 (needs community profile)

**Validation:**
- Posts analyzed with SpaCy NLP
- ISC score calculated (0-10 scale)
- community_profiles table populated
- Frontend displays rhythm metrics, top hooks

### Phase 4: Module 3 - Generator (Week 7-8)
**Build Order:**
1. LLM client service (OpenRouter)
2. Blacklist checker service
3. RAG retrieval (fetch top posts)
4. Mimicry filter (post-processing)
5. Celery task: generate_draft
6. Frontend: Draft editor with preview

**Dependencies:**
- Requires: Module 2 (community_profile)
- Blocks: Module 4 (needs generated drafts)

**Validation:**
- Draft generated matching community style
- Blacklist violations detected and prevented
- ISC score of draft within ±1.5 of profile
- Frontend shows draft with edit/approve actions

### Phase 5: Module 4 - Monitor (Week 9-10)
**Build Order:**
1. Reddit API client (PRAW)
2. Shadowban detector service
3. Alert service (Resend integration)
4. Celery Beat scheduler
5. Celery task: check_post_status (periodic)
6. Frontend: Monitoring dashboard

**Dependencies:**
- Requires: Module 3 (approved drafts)
- No blockers (final module)

**Validation:**
- Post registered for monitoring
- Periodic checks (every 4h) fetch metrics
- Shadowban heuristics detect degraded posts
- User receives email alert on shadowban

### Phase 6: Billing & Usage (Week 11-12)
**Build Order:**
1. Stripe integration (webhooks)
2. Usage tracking service
3. Plan limit enforcement middleware
4. Billing API endpoints
5. Frontend: Billing settings, usage meters

**Dependencies:**
- Requires: All modules (track usage per module)
- Can be built in parallel with Module 4

**Validation:**
- User upgrades plan via Stripe checkout
- Usage limits enforced (trial: 3 campaigns)
- Dashboard shows usage meters

### Critical Path
The longest dependency chain (critical path for MVP):

```
Auth → Module 1 → Module 2 → Module 3 → Module 4
```

**Estimated timeline:** 10-12 weeks for full pipeline (Phases 1-5)

**Parallelization opportunities:**
- Frontend UI can be built alongside backend services
- Module 4 and Billing (Phase 6) can be developed in parallel
- Testing can occur continuously (unit tests per module)

### De-risking Strategy

**Week 3 (after Phase 1):** Validate Apify integration
- Risk: Apify API doesn't return expected data structure
- Mitigation: Build Apify client first, test with real Reddit data

**Week 5 (after Phase 2):** Validate SpaCy NLP accuracy
- Risk: SpaCy rhythm analysis produces unreliable ISC scores
- Mitigation: Test scoring engine with 100+ real posts, tune weight matrix

**Week 7 (after Phase 3):** Validate LLM mimicry quality
- Risk: Generated content doesn't match community style
- Mitigation: Human evaluation of 50 generated drafts, iterate on prompt engineering

**Week 9 (after Phase 4):** Validate shadowban detection accuracy
- Risk: False positives or false negatives in shadowban detection
- Mitigation: Test with known shadowbanned accounts, refine heuristics

## Sources

- [Top 5 Web Scraping AI Agents of 2026](https://www.gptbots.ai/blog/web-scraping-ai-agents)
- [Reddit Scraping Guide 2025](https://webscrapingsite.com/guide/how-to-scrape-reddit/)
- [FastAPI + Celery Async Architecture](https://medium.com/@hitorunajp/celery-and-background-tasks-aebb234cae5d)
- [Celery Best Practices 2026](https://testdriven.io/blog/fastapi-and-celery/)
- [Building Async Pipelines with FastAPI and Celery](https://devcenter.upsun.com/posts/building-async-processing-pipelines-with-fastapi-and-celery-on-upsun/)
- [Complete Guide to FastAPI Background Processing](https://blog.greeden.me/en/2026/01/27/the-complete-guide-to-background-processing-with-fastapi-x-celery-redishow-to-separate-heavy-work-from-your-api-to-keep-services-stable/)
- [Celery 2026: Distributed Task Queue](https://www.programming-helper.com/tech/celery-2026-python-distributed-task-queue-redis-rabbitmq)
- [Social Media Data Pipeline Architecture](https://aws.amazon.com/solutions/guidance/social-media-data-pipeline-on-aws/)
- [LLM Content Creation Strategy 2026](https://wellows.com/blog/llm-content-creation-strategy/)
- [LLMEO Strategies 2026: LLM Optimization](https://techiehub.blog/llmeo-strategies-2026/)
- [spaCy Processing Pipelines Documentation](https://spacy.io/usage/processing-pipelines)
- [spaCy 101: Everything You Need to Know](https://spacy.io/usage/spacy-101)
- [Monorepo Architecture with Turborepo](https://medium.com/@ignatovich.dm/monorepos-with-turborepo-6aa0852708ee)
- [Monorepo Architecture Ultimate Guide 2025](https://feature-sliced.design/blog/frontend-monorepo-explained)
- [Turborepo Guide for Multiple Frontends](https://strapi.io/blog/turborepo-guide)
- [Reddit Bot Automation with AI](https://n8n.io/workflows/5894-reddit-bot-automation-ai-auto-reply-and-post-monitor-with-gpt-4-google-sheets/)
- [NLP Pipeline: Key Steps to Process Text Data](https://airbyte.com/data-engineering-resources/natural-language-processing-pipeline)
- [Data Engineering Trends 2026](https://www.trigyn.com/insights/data-engineering-trends-2026-building-foundation-ai-driven-enterprises)

---

*Architecture research for: BC-RAO Reddit Content Generation Tool*
*Researched: 2026-02-07*
