# Technology Stack Research

**Project:** BC-RAO (Social Intelligence Platform)
**Domain:** Reddit behavioral analysis + AI content generation + post monitoring
**Researched:** 2026-02-07
**Confidence:** HIGH

## Executive Summary

BC-RAO's locked stack represents a mature, production-ready combination for building AI-powered social intelligence platforms. The architecture splits cleanly between Next.js 15 (frontend + BFF), FastAPI (Python backend + ML processing), Supabase (database + auth + real-time), and Celery/Redis (async task processing). This research validates the stack choices and provides specific versions, integration patterns, and critical gotchas.

**Key Finding:** This stack combination is well-documented with established integration patterns. The primary risks are around connection pooling (Supabase Transaction Mode breaks prepared statements), CORS configuration (Next.js/FastAPI requires explicit setup), and Celery serialization security (never use pickle for untrusted data).

---

## Core Technologies

### Frontend Stack

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Next.js | 15.1.6+ | React framework with SSR/SSG | App Router stable, React 19 support, 76.7% faster dev server, Turbopack stable | HIGH |
| React | 19.x | UI library | Required for Next.js 15 App Router, improved hydration errors, Server Components stable | HIGH |
| TypeScript | 5.x | Type safety | Required for next.config.ts, full type safety with FastAPI OpenAPI codegen | HIGH |
| Tailwind CSS | 4.x | Utility-first CSS | V4 is stable, 40% smaller bundle, native CSS cascade layers, performance optimized | HIGH |
| Shadcn/UI | Latest | Component library | React 19 + Tailwind v4 compatible, accessible, customizable, tree-shakeable | HIGH |

**Node.js Requirement:** 18.18.0+ (Next.js 15 minimum requirement)

### Backend Stack

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Python | 3.11-3.13 | Language runtime | FastAPI 0.128.4 supports 3.9-3.14, Celery 5.6.2 supports 3.9-3.13, spaCy 3.8+ requires 3.9+ | HIGH |
| FastAPI | 0.128.4+ | API framework | Latest stable (released 2026-02-07), async-first, automatic OpenAPI docs, Pydantic v2 integration | HIGH |
| Pydantic | 2.x | Data validation | Required by FastAPI 0.128+, 5-50x faster than v1, better error messages | HIGH |
| Uvicorn | Latest | ASGI server | Production-ready with `fastapi[standard]`, async I/O, WebSocket support | HIGH |

**Recommended Python Version:** 3.11 or 3.12 (best performance + stability balance)

### Database Stack

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Supabase | Latest | Postgres + Auth + Real-time | Managed Postgres, built-in Auth + RLS, pgvector included, 99.9% SLA | HIGH |
| PostgreSQL | 15+ | Relational database | Supabase runs Postgres 15+, production-grade, ACID compliance | HIGH |
| pgvector | 0.5.x+ | Vector similarity search | Native Postgres extension, HNSW + IVFFlat indexing, 10x cheaper than Pinecone | HIGH |
| SQLAlchemy | 2.0+ | Python ORM | Async support stable, type-safe queries, Alembic migration support | HIGH |
| Asyncpg | 0.29+ | Async Postgres driver | Fastest Python Postgres driver, required for SQLAlchemy async | HIGH |

### Task Queue Stack

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Celery | 5.6.2+ | Distributed task queue | Latest stable (2026-01-04), Python 3.9-3.13 support, memory leak fixes, battle-tested | HIGH |
| Redis | 7.x | Message broker + result backend | Celery-recommended, sub-millisecond latency, persistence support | HIGH |

### AI/ML Stack

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| OpenRouter | API | LLM routing gateway | Access 400+ models, automatic fallbacks, cost optimization, unified API | HIGH |
| spaCy | 3.8.11+ | NLP processing | Latest stable, Python 3.13 support (Cython 3), fast local processing, no API costs | HIGH |
| en_core_web_md | 3.8.x | English NLP model | 20k word vectors, 500k vocabulary, sufficient for behavioral analysis, 43MB size | MEDIUM |

### Scraping Stack

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Apify | API | Reddit scraping service | Pre-built Reddit scrapers, handles rate limits, no API key needed, webhook support | HIGH |

### Supporting Services

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Stripe | API v2 | Payment processing | FastAPI integration patterns mature, webhook handling robust, PCI compliant | HIGH |
| Resend | API | Transactional email | Node.js SDK official, React Email support, 99.5% deliverability, developer-friendly | HIGH |

---

## Recommended Supporting Libraries

### Frontend (Node.js/TypeScript)

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| @tanstack/react-query | 5.x | Server state management | API data fetching, caching, optimistic updates | HIGH |
| Zod | 3.x | Schema validation | Type-safe form validation, matches Pydantic on backend | HIGH |
| next-safe-action | Latest | Type-safe Server Actions | Validation + error handling for Next.js 15 Server Actions | HIGH |
| openapi-typescript-codegen | Latest | API client generation | Auto-generate typed FastAPI clients from OpenAPI schema | HIGH |
| react-hook-form | 7.x | Form state management | Complex forms, works with Zod validation | HIGH |
| stripe | Latest (Node) | Stripe client | Webhook verification, Checkout integration | HIGH |
| resend | Latest | Email client | Transactional emails from Next.js API routes or Server Actions | HIGH |

### Backend (Python)

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| supabase-py | 2.x | Supabase client | Auth, Storage, RLS interactions from Python | HIGH |
| python-dotenv | 1.x | Environment variables | Load .env files in development | HIGH |
| httpx | 0.27+ | Async HTTP client | API calls from FastAPI (OpenRouter, Apify), replaces requests | HIGH |
| alembic | 1.13+ | Database migrations | SQLAlchemy schema versioning | HIGH |
| redis-py | 5.x | Redis client | Celery result backend, caching | HIGH |
| stripe | Latest (Python) | Stripe SDK | Payment processing, webhook signature verification | HIGH |
| pytest | 8.x | Testing framework | Unit + integration tests | HIGH |
| pytest-asyncio | 0.23+ | Async test support | Test async FastAPI endpoints | HIGH |

---

## Integration Patterns

### Next.js 15 + FastAPI Integration

**Approach:** Separate deployments with API proxy in development

```typescript
// next.config.ts
import type { NextConfig } from 'next'

const config: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination:
          process.env.NODE_ENV === 'development'
            ? 'http://127.0.0.1:8000/api/:path*'
            : 'https://your-fastapi-backend.com/api/:path*',
      },
    ]
  },
}

export default config
```

**FastAPI CORS Setup:**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CRITICAL: Explicit origins, never use ["*"] with credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev
        "https://your-production-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

**Type Safety Pattern:**

1. FastAPI generates OpenAPI schema at `/openapi.json`
2. Use `openapi-typescript-codegen` to generate TypeScript client
3. Import generated types in Next.js components
4. Changes to FastAPI routes automatically update TypeScript types

**Sources:**
- [Next.js FastAPI Template](https://www.vintasoftware.com/blog/next-js-fastapi-template)
- [Mastering CORS: FastAPI and Next.js](https://medium.com/@vaibhavtiwari.945/mastering-cors-configuring-cross-origin-resource-sharing-in-fastapi-and-next-js-28c61272084b)
- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)

**Confidence:** HIGH

---

### Supabase + FastAPI Integration

**Connection Pooling Pattern (CRITICAL):**

Supabase provides two connection modes via Supavisor (replaced PgBouncer):

1. **Transaction Mode (Port 6543)** - DEFAULT for serverless/web
   - Connection released immediately after transaction
   - **BREAKS prepared statements** - must disable in SQLAlchemy
   - Use for: FastAPI endpoints, Celery tasks, short-lived operations

2. **Session Mode (Port 5432)** - For long-lived connections
   - Connection held for entire session
   - Supports prepared statements
   - Use for: Local development, long-running workers

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Production (Transaction Mode) - MUST disable prepared statements
DATABASE_URL = "postgresql+asyncpg://user:pass@host:6543/db"
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    # CRITICAL: Disable prepared statements for Transaction Mode
    connect_args={
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0,
    }
)

# Local development (Session Mode) - prepared statements OK
# DATABASE_URL = "postgresql+asyncpg://user:pass@host:5432/db"
# engine = create_async_engine(DATABASE_URL, echo=True)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
```

**Dependency Injection Pattern:**

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_session)
):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    return user
```

**Sources:**
- [Supabase Connection Scaling for FastAPI](https://medium.com/@papansarkar101/supabase-connection-scaling-the-essential-guide-for-fastapi-developers-2dc5c428b638)
- [Supabase Connection Management Docs](https://supabase.com/docs/guides/database/connection-management)
- [FastAPI with Async SQLAlchemy 2.0](https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308)

**Confidence:** HIGH

---

### Celery + Redis + FastAPI Integration

**Configuration Pattern:**

```python
# celery_config.py
from celery import Celery

celery_app = Celery(
    "bc_rao",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",  # Separate DB for results
    broker_connection_retry_on_startup=True,
)

celery_app.conf.update(
    task_serializer="json",  # NEVER use pickle for security
    accept_content=["json"],  # Only accept JSON
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3500,  # Soft limit before hard kill
    worker_prefetch_multiplier=1,  # For task prioritization
    worker_max_tasks_per_child=1000,  # Prevent memory leaks
)

# Task routing for different queues
celery_app.conf.task_routes = {
    "tasks.scrape_reddit": {"queue": "scraping"},
    "tasks.analyze_behavior": {"queue": "ml_processing"},
    "tasks.generate_content": {"queue": "ai_generation"},
    "tasks.monitor_post": {"queue": "monitoring"},
}
```

**Task Definition:**

```python
# tasks.py
from celery_config import celery_app
from typing import Dict, Any

@celery_app.task(
    name="tasks.analyze_behavior",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def analyze_behavior(self, subreddit: str, posts: list[Dict[str, Any]]):
    try:
        # Load spaCy model (cache in worker)
        import spacy
        nlp = spacy.load("en_core_web_md")

        # Process posts
        results = []
        for post in posts:
            doc = nlp(post["content"])
            results.append({
                "post_id": post["id"],
                "entities": [ent.text for ent in doc.ents],
                "sentiment": doc.sentiment,
            })

        return results
    except Exception as exc:
        raise self.retry(exc=exc)
```

**Trigger from FastAPI:**

```python
from fastapi import FastAPI, BackgroundTasks
from tasks import analyze_behavior

@app.post("/analyze/{subreddit}")
async def trigger_analysis(subreddit: str):
    # Async task dispatch (non-blocking)
    task = analyze_behavior.delay(subreddit, posts_data)

    return {
        "task_id": task.id,
        "status": "processing",
    }

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    from celery.result import AsyncResult
    task = AsyncResult(task_id, app=celery_app)

    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None,
    }
```

**CRITICAL SECURITY NOTES:**

1. **Never use pickle serialization** - JSON only (pickle can execute arbitrary code)
2. **Use separate Redis DBs** for broker (0) and backend (1) to avoid conflicts
3. **Configure worker_max_tasks_per_child** to prevent memory leaks in ML workloads
4. **Set task time limits** to prevent runaway tasks

**Sources:**
- [Celery 2026: Python Distributed Task Queue](https://www.programming-helper.com/tech/celery-2026-python-distributed-task-queue-redis-rabbitmq)
- [Task Serialization Security in Celery](https://docs.celeryq.dev/en/stable/userguide/security.html)
- [Celery Redis Best Practices](https://medium.com/@jasidhassan/celery-and-redis-asynchronous-task-processing-a1ea58956f3e)

**Confidence:** HIGH

---

### OpenRouter + FastAPI Integration

**HTTP Client Pattern:**

```python
import httpx
from pydantic import BaseModel
from typing import List, Optional

class OpenRouterRequest(BaseModel):
    model: str
    messages: List[dict]
    temperature: float = 0.7
    max_tokens: Optional[int] = None

class OpenRouterClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.client = httpx.AsyncClient(timeout=60.0)

    async def chat_completion(
        self,
        messages: List[dict],
        model: str = "anthropic/claude-3.5-sonnet",  # Explicit model
        **kwargs
    ) -> dict:
        """
        AVOID openrouter/auto in production - unpredictable model selection.
        Pin specific models for consistent output quality.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://bc-rao.com",  # Required for analytics
            "X-Title": "BC-RAO",  # Required for analytics
        }

        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }

        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()

# Usage in FastAPI endpoint
@app.post("/generate-content")
async def generate_content(
    subreddit: str,
    behavioral_profile: dict,
    openrouter: OpenRouterClient = Depends(get_openrouter_client)
):
    messages = [
        {
            "role": "system",
            "content": f"Generate content matching this behavioral profile: {behavioral_profile}"
        },
        {
            "role": "user",
            "content": f"Create a post for r/{subreddit}"
        }
    ]

    result = await openrouter.chat_completion(
        messages=messages,
        model="anthropic/claude-3.5-sonnet",
        temperature=0.8,
    )

    return {"generated_content": result["choices"][0]["message"]["content"]}
```

**Fallback Chain Pattern:**

```python
async def generate_with_fallback(self, messages: List[dict]) -> dict:
    """
    Implement manual fallback chain for production reliability.
    OpenRouter provides automatic fallbacks, but explicit control is better.
    """
    models = [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4-turbo",
        "google/gemini-pro",
    ]

    for model in models:
        try:
            return await self.chat_completion(messages, model=model)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limit
                continue  # Try next model
            raise  # Don't retry on other errors

    raise Exception("All fallback models failed")
```

**Sources:**
- [OpenRouter Quickstart Guide](https://openrouter.ai/docs/quickstart)
- [OpenRouter API Reference](https://openrouter.ai/docs/api/reference/overview)
- [A Practical Guide to OpenRouter](https://medium.com/@milesk_33/a-practical-guide-to-openrouter-unified-llm-apis-model-routing-and-real-world-use-d3c4c07ed170)

**Confidence:** HIGH

---

### Apify Reddit Scraper Integration

**Webhook Pattern (Recommended):**

```python
import httpx
from pydantic import BaseModel

class ApifyScraperConfig(BaseModel):
    actor_id: str = "trudax/reddit-scraper"
    api_token: str
    webhook_url: str

async def trigger_reddit_scrape(
    subreddit: str,
    max_posts: int = 100,
    config: ApifyScraperConfig,
):
    """
    Trigger Apify Reddit scraper with webhook for async results.
    Actor runs independently and calls webhook when complete.
    """
    payload = {
        "subreddits": [subreddit],
        "maxPosts": max_posts,
        "type": "posts",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.apify.com/v2/acts/{config.actor_id}/runs",
            params={
                "token": config.api_token,
                "webhooks": [
                    {
                        "eventTypes": ["ACTOR.RUN.SUCCEEDED"],
                        "requestUrl": config.webhook_url,
                    }
                ]
            },
            json=payload,
        )
        response.raise_for_status()
        run_data = response.json()

        return {
            "run_id": run_data["data"]["id"],
            "status": run_data["data"]["status"],
        }

# Webhook receiver endpoint
@app.post("/webhooks/apify")
async def handle_apify_webhook(webhook_data: dict):
    """
    Apify calls this when scrape completes.
    Store data and trigger Celery task for analysis.
    """
    run_id = webhook_data["resource"]["id"]
    dataset_id = webhook_data["resource"]["defaultDatasetId"]

    # Fetch results from Apify dataset
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.apify.com/v2/datasets/{dataset_id}/items",
            params={"token": config.api_token, "format": "json"}
        )
        posts = response.json()

    # Trigger Celery task for behavioral analysis
    from tasks import analyze_behavior
    analyze_behavior.delay(subreddit, posts)

    return {"status": "processing"}
```

**Rate Limiting Considerations:**

Apify handles Reddit rate limits internally:
- Uses OAuth authentication (60 req/min vs 10 req/min unauthenticated)
- Automatic retry with exponential backoff
- Rotating proxies to avoid IP bans
- Respects Reddit's `X-Ratelimit-*` headers

**Sources:**
- [Apify Reddit Scraper](https://apify.com/trudax/reddit-scraper)
- [Reddit API Rate Limits Guide 2026](https://painonsocial.com/blog/reddit-api-rate-limits-guide)
- [Apify Integration Options](https://data365.co/blog/apify-reddit-scraper)

**Confidence:** HIGH

---

### spaCy + Celery Integration

**Model Loading Pattern:**

```python
import spacy
from functools import lru_cache

@lru_cache(maxsize=1)
def get_nlp_model():
    """
    Load spaCy model once per worker process (cache in memory).
    Model loading is expensive (~1-2 seconds), so cache it.
    """
    return spacy.load("en_core_web_md")

@celery_app.task(name="tasks.extract_behavioral_patterns")
def extract_behavioral_patterns(posts: list[dict]) -> dict:
    nlp = get_nlp_model()

    patterns = {
        "entities": [],
        "syntax_patterns": [],
        "vocabulary_level": [],
    }

    for post in posts:
        doc = nlp(post["content"])

        # Extract named entities
        patterns["entities"].extend([
            {"text": ent.text, "label": ent.label_}
            for ent in doc.ents
        ])

        # Analyze syntax patterns
        patterns["syntax_patterns"].append({
            "avg_sentence_length": len(doc) / len(list(doc.sents)),
            "noun_chunks": [chunk.text for chunk in doc.noun_chunks],
        })

        # Word vector similarity (behavioral mimicry)
        # en_core_web_md has 20k word vectors
        vocabulary = [token for token in doc if token.has_vector]
        patterns["vocabulary_level"].append(len(vocabulary) / len(doc))

    return patterns
```

**Installation:**

```bash
# Install spaCy
pip install spacy==3.8.11

# Download en_core_web_md model (43MB)
python -m spacy download en_core_web_md
```

**Model Comparison:**

| Model | Size | Vectors | Vocab | Use Case | Confidence |
|-------|------|---------|-------|----------|------------|
| en_core_web_sm | 13MB | 0 | 0 | Quick NER/POS, no vectors | N/A |
| en_core_web_md | 43MB | 20k | 500k | **Recommended for BC-RAO** - good balance | HIGH |
| en_core_web_lg | 560MB | 685k | 685k | Better accuracy, 13x larger | N/A |

**Why en_core_web_md:**
- Contains word vectors for similarity analysis (required for behavioral mimicry)
- 43MB is acceptable for Docker images
- 20k vectors sufficient for social media vocabulary
- Fast inference (~100 posts/sec per worker)

**Sources:**
- [spaCy Models Documentation](https://spacy.io/models)
- [spaCy Install Guide](https://spacy.io/usage)
- [spaCy 3.8 Release](https://github.com/explosion/spacy/releases)

**Confidence:** MEDIUM (en_core_web_lg might be better for production, but en_core_web_md is sufficient for MVP)

---

### Stripe + FastAPI Integration

**Webhook Pattern:**

```python
import stripe
from fastapi import Request, HTTPException

stripe.api_key = "sk_test_..."

@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = "whsec_..."

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle event types
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        # Fulfill order, upgrade subscription tier
        await upgrade_user_subscription(session["customer"], session["metadata"])

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        # Downgrade user to free tier
        await downgrade_user(subscription["customer"])

    return {"status": "success"}

# Create checkout session
@app.post("/create-checkout-session")
async def create_checkout_session(user_id: str, plan: str):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price": "price_..." if plan == "starter" else "price_...",
                "quantity": 1,
            }
        ],
        mode="subscription",
        success_url="https://bc-rao.com/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="https://bc-rao.com/pricing",
        metadata={"user_id": user_id, "plan": plan},
    )

    return {"checkout_url": session.url}
```

**Sources:**
- [FastAPI Stripe Integration Tutorial](https://www.fast-saas.com/blog/fastapi-stripe-integration/)
- [Building Payment Backend with FastAPI and Stripe](https://medium.com/@abdulikram/building-a-payment-backend-with-fastapi-stripe-checkout-and-webhooks-08dc15a32010)

**Confidence:** HIGH

---

### Next.js 15 Server Actions Best Practices

**Type-Safe Server Actions with next-safe-action:**

```typescript
// app/actions/analyze.ts
'use server'

import { createSafeActionClient } from 'next-safe-action'
import { z } from 'zod'

const action = createSafeActionClient()

const analyzeSubredditSchema = z.object({
  subreddit: z.string().min(1).max(50),
  maxPosts: z.number().min(1).max(1000).default(100),
})

export const analyzeSubreddit = action
  .schema(analyzeSubredditSchema)
  .action(async ({ parsedInput: { subreddit, maxPosts } }) => {
    // Call FastAPI backend
    const response = await fetch(`${process.env.API_URL}/analyze/${subreddit}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ maxPosts }),
    })

    if (!response.ok) {
      throw new Error('Analysis failed')
    }

    return await response.json()
  })
```

**Usage in Client Component:**

```typescript
'use client'

import { useAction } from 'next-safe-action/hooks'
import { analyzeSubreddit } from '@/app/actions/analyze'

export function AnalyzeForm() {
  const { execute, status, result } = useAction(analyzeSubreddit)

  const handleSubmit = (formData: FormData) => {
    execute({
      subreddit: formData.get('subreddit') as string,
      maxPosts: 100,
    })
  }

  return (
    <form action={handleSubmit}>
      <input name="subreddit" placeholder="e.g., SaaS" />
      <button disabled={status === 'executing'}>
        {status === 'executing' ? 'Analyzing...' : 'Analyze'}
      </button>

      {result?.data && (
        <div>Analysis complete: {result.data.task_id}</div>
      )}
    </form>
  )
}
```

**Security Best Practices:**

1. Always validate user permissions in Server Actions
2. Never expose sensitive logic - Server Actions are POST-only
3. Use Zod schemas for input validation (matches Pydantic on backend)
4. Server Actions can't be cached - use Route Handlers for GET requests

**Sources:**
- [Next.js 15 Server Actions Best Practice](https://medium.com/@lior_amsalem/nextjs-15-actions-best-practice-bf5cc023301e)
- [Next.js Server Actions: Complete Guide 2026](https://makerkit.dev/blog/tutorials/nextjs-server-actions)
- [Type-safe Server Actions with next-safe-action](https://next-safe-action.dev/)

**Confidence:** HIGH

---

## Installation & Setup

### Frontend Setup (Next.js 15)

```bash
# Create Next.js 15 project with TypeScript + Tailwind
npx create-next-app@latest bc-rao-frontend --typescript --tailwind --app

cd bc-rao-frontend

# Install core dependencies
npm install @tanstack/react-query zod react-hook-form @hookform/resolvers
npm install next-safe-action stripe resend

# Install Shadcn/UI
npx shadcn@latest init
npx shadcn@latest add button card form input textarea

# Install dev dependencies
npm install -D openapi-typescript-codegen @types/node

# Environment variables (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
STRIPE_PUBLIC_KEY=pk_test_...
RESEND_API_KEY=re_...
```

### Backend Setup (FastAPI)

```bash
# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install core dependencies
pip install "fastapi[standard]==0.128.4"
pip install "sqlalchemy[asyncio]==2.0.36"
pip install asyncpg==0.29.0
pip install alembic==1.13.3
pip install supabase==2.10.0
pip install celery[redis]==5.6.2
pip install httpx==0.27.2
pip install python-dotenv==1.0.1
pip install stripe==11.3.0

# Install AI/ML dependencies
pip install spacy==3.8.11
python -m spacy download en_core_web_md

# Install dev dependencies
pip install pytest==8.3.4
pip install pytest-asyncio==0.23.8
pip install black==24.10.0
pip install mypy==1.13.0

# Environment variables (.env)
DATABASE_URL=postgresql+asyncpg://...@...supabase.co:6543/postgres
REDIS_URL=redis://localhost:6379/0
OPENROUTER_API_KEY=sk-or-...
APIFY_API_TOKEN=apify_api_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Database Setup (Supabase)

```sql
-- Enable pgvector extension
create extension if not exists vector;

-- Create tables with RLS
create table public.users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  subscription_tier text default 'trial',
  created_at timestamp with time zone default now()
);

alter table public.users enable row level security;

create table public.behavioral_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(id) on delete cascade,
  subreddit text not null,
  archetype_embeddings vector(384),  -- spaCy en_core_web_md has 96-dim, but store 384 for future models
  syntax_patterns jsonb,
  created_at timestamp with time zone default now()
);

alter table public.behavioral_profiles enable row level security;

-- Create HNSW index for vector similarity
create index behavioral_profiles_embeddings_idx
  on public.behavioral_profiles
  using hnsw (archetype_embeddings vector_cosine_ops);
```

### Redis Setup

```bash
# Install Redis (Docker recommended)
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Or install locally
# macOS: brew install redis && brew services start redis
# Ubuntu: sudo apt install redis-server && sudo systemctl start redis
```

### Celery Worker Setup

```bash
# Start Celery worker with multiple queues
celery -A celery_config worker \
  --loglevel=info \
  --queues=scraping,ml_processing,ai_generation,monitoring \
  --concurrency=4 \
  --max-tasks-per-child=1000

# Start Celery Beat (periodic tasks)
celery -A celery_config beat --loglevel=info
```

---

## What NOT to Use

### Avoid These Patterns

| Avoid | Why | Use Instead | Confidence |
|-------|-----|-------------|------------|
| pickle for Celery serialization | Security risk - can execute arbitrary code | JSON serialization only | HIGH |
| Supabase port 5432 in production | Session mode doesn't scale, uses more connections | Port 6543 (Transaction Mode) | HIGH |
| SQLAlchemy prepared statements with port 6543 | Transaction Mode breaks prepared statements | Disable prepared statement cache | HIGH |
| openrouter/auto model | Unpredictable model selection in production | Pin specific models (claude-3.5-sonnet) | HIGH |
| CORS `allow_origins=["*"]` with credentials | Security vulnerability, blocks cookies | Explicit origin list | HIGH |
| Unauthenticated Reddit API | 10 req/min limit, gets IP banned | Use Apify (handles OAuth + rate limits) | HIGH |
| Next.js Pages Router | Legacy, missing React 19 features | App Router (stable in Next.js 15) | HIGH |
| requests library | Blocking I/O, no async support | httpx (async HTTP client) | HIGH |
| SQLAlchemy 1.4 | Old async API, deprecated | SQLAlchemy 2.0+ | HIGH |
| Pydantic v1 | 5-50x slower than v2 | Pydantic v2 (required by FastAPI 0.128+) | HIGH |

### Deprecated/Outdated Technologies

| Technology | Status | Notes |
|------------|--------|-------|
| Scrapy for Reddit | Outdated | Reddit blocks scrapers, use Apify instead |
| PRAW (Python Reddit API Wrapper) | Limited | 60 req/min cap, use Apify for scale |
| spaCy < 3.0 | Deprecated | Missing modern features, use 3.8+ |
| Celery < 5.0 | Deprecated | Missing async support, memory leaks |
| FastAPI < 0.100 | Outdated | Use 0.128+ for Pydantic v2 |
| Next.js < 14 | Outdated | Use 15+ for stable App Router + React 19 |

---

## Version Compatibility Matrix

| Package | Version | Compatible With | Notes | Confidence |
|---------|---------|-----------------|-------|------------|
| FastAPI | 0.128.4 | Python 3.9-3.14 | Latest stable, Pydantic v2 | HIGH |
| Celery | 5.6.2 | Python 3.9-3.13 | Memory leak fixes, stable | HIGH |
| spaCy | 3.8.11 | Python 3.9-3.13 | Python 3.13 support via Cython 3 | HIGH |
| en_core_web_md | 3.8.x | spaCy >=3.8.0,<3.9.0 | Must match spaCy major.minor | HIGH |
| SQLAlchemy | 2.0+ | Python 3.8+ | Async ORM stable | HIGH |
| Next.js | 15.x | Node.js 18.18.0+ | Requires React 19 | HIGH |
| React | 19.x | - | App Router requirement | HIGH |
| Pydantic | 2.x | Python 3.8+ | Required by FastAPI 0.100+ | HIGH |

---

## Critical Gotchas & Known Issues

### 1. Supabase Transaction Mode + SQLAlchemy Prepared Statements

**Problem:** Supabase Transaction Mode (port 6543) releases connections after each transaction, breaking SQLAlchemy's prepared statement cache.

**Symptom:** `server closed the connection unexpectedly` errors in production.

**Solution:** Disable prepared statements in asyncpg connection:

```python
engine = create_async_engine(
    DATABASE_URL,
    connect_args={
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0,
    }
)
```

**Source:** [Supabase Connection Scaling for FastAPI](https://medium.com/@papansarkar101/supabase-connection-scaling-the-essential-guide-for-fastapi-developers-2dc5c428b638)

**Confidence:** HIGH

---

### 2. Next.js/FastAPI CORS Configuration

**Problem:** Browser preflight OPTIONS requests fail if CORS middleware is misconfigured.

**Symptoms:**
- CORS errors in browser console
- Requests work in Postman but not browser
- 404 on OPTIONS requests

**Solution:**

1. **FastAPI:** Add CORSMiddleware BEFORE routes
2. **FastAPI:** Explicitly allow OPTIONS method
3. **Next.js:** Use rewrites, not proxy middleware (deprecated)
4. **Never use** `allow_origins=["*"]` with `allow_credentials=True`

```python
# Correct order: middleware BEFORE routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Explicit origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok"}
```

**Source:** [Mastering CORS: FastAPI and Next.js](https://medium.com/@vaibhavtiwari.945/mastering-cors-configuring-cross-origin-resource-sharing-in-fastapi-and-next-js-28c61272084b)

**Confidence:** HIGH

---

### 3. Celery pickle Serialization Security

**Problem:** pickle can execute arbitrary code during deserialization. If an attacker gains access to your Redis broker, they can execute code on your workers.

**Symptoms:** None until exploited (silent security vulnerability).

**Solution:** Use JSON serialization exclusively:

```python
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],  # Reject pickle, yaml, etc.
    result_serializer="json",
)
```

**Trade-off:** JSON can't serialize arbitrary Python objects. For complex data, use Pydantic models + `.model_dump()`:

```python
from pydantic import BaseModel

class AnalysisResult(BaseModel):
    subreddit: str
    patterns: dict

@celery_app.task
def process_analysis(data: dict):
    result = AnalysisResult(**data)
    # Process...
    return result.model_dump()  # JSON-serializable
```

**Source:** [Celery Security Documentation](https://docs.celeryq.dev/en/stable/userguide/security.html)

**Confidence:** HIGH

---

### 4. Reddit Rate Limiting via Apify

**Problem:** Direct Reddit API access gets rate-limited (60 req/min authenticated, 10 req/min unauthenticated) and IP-banned for scraping.

**Symptoms:**
- 429 Too Many Requests errors
- Shadowbanned accounts
- Incomplete data extraction

**Solution:** Use Apify Reddit Scraper:

- Handles OAuth authentication (60 req/min)
- Rotates proxies to avoid IP bans
- Respects Reddit's rate limit headers
- Webhook-based async results

**Do NOT:** Build custom scraper with PRAW or requests - Reddit actively blocks scrapers.

**Sources:**
- [Reddit API Rate Limits Guide 2026](https://painonsocial.com/blog/reddit-api-rate-limits-guide)
- [How to Scrape Reddit Legally](https://painonsocial.com/blog/how-to-scrape-reddit-legally)

**Confidence:** HIGH

---

### 5. spaCy Model Loading in Celery Workers

**Problem:** spaCy model loading is slow (~1-2 seconds). Loading on every task wastes CPU and memory.

**Symptoms:** Slow task execution, high worker startup time.

**Solution:** Use `@lru_cache` to load model once per worker process:

```python
from functools import lru_cache
import spacy

@lru_cache(maxsize=1)
def get_nlp_model():
    return spacy.load("en_core_web_md")

@celery_app.task
def analyze_text(text: str):
    nlp = get_nlp_model()  # Cached after first call
    doc = nlp(text)
    return [ent.text for ent in doc.ents]
```

**Confidence:** MEDIUM (based on standard Python patterns, not spaCy-specific documentation)

---

### 6. Next.js 15 Async Request APIs

**Problem:** Next.js 15 made `cookies()`, `headers()`, `params`, `searchParams` async. Old code breaks.

**Symptoms:** TypeScript errors, runtime Promise errors.

**Solution:** Await all request-dependent APIs:

```typescript
// Next.js 14 (OLD)
import { cookies } from 'next/headers'
const cookieStore = cookies()

// Next.js 15 (NEW)
import { cookies } from 'next/headers'
const cookieStore = await cookies()
```

**Migration:** Run codemod: `npx @next/codemod@canary next-async-request-api .`

**Source:** [Next.js 15 Release Notes](https://nextjs.org/blog/next-15)

**Confidence:** HIGH

---

### 7. OpenRouter Auto-Routing Unpredictability

**Problem:** `openrouter/auto` model selects "best" model dynamically. Output quality varies day-to-day as model rankings change.

**Symptoms:**
- Inconsistent content quality
- Different response styles
- Hard to reproduce issues

**Solution:** Pin specific models in production:

```python
# AVOID in production
model = "openrouter/auto"

# DO in production
model = "anthropic/claude-3.5-sonnet"  # Consistent output
```

**Use auto-routing for:** Cost optimization in non-critical tasks (monitoring, summaries).

**Source:** [A Practical Guide to OpenRouter](https://medium.com/@milesk_33/a-practical-guide-to-openrouter-unified-llm-apis-model-routing-and-real-world-use-d3c4c07ed170)

**Confidence:** MEDIUM (based on general model routing patterns)

---

## Development vs Production Differences

| Concern | Development | Production | Notes |
|---------|-------------|------------|-------|
| Supabase connection | Port 5432 (Session Mode) | Port 6543 (Transaction Mode) + disabled prepared statements | Transaction Mode required for scale |
| Next.js API proxy | `http://127.0.0.1:8000` | `https://api.bc-rao.com` | Configure in next.config.ts |
| CORS origins | `["http://localhost:3000"]` | `["https://bc-rao.com"]` | Never use wildcard |
| Redis persistence | No persistence (default) | Enable AOF or RDB | Prevent data loss on restart |
| Celery workers | 1 worker, all queues | Multiple workers per queue | Separate scraping/ML/AI queues |
| spaCy model | en_core_web_sm (faster dev) | en_core_web_md (production) | Vectors required for mimicry |
| OpenRouter models | Cheaper models for testing | Pin specific models | Consistency > cost |
| Stripe keys | Test keys (`sk_test_...`) | Live keys (`sk_live_...`) | Separate webhooks |

---

## Performance Optimization Guidelines

### Database (Supabase)

1. **Use indexes on frequently queried columns:**
   ```sql
   create index idx_users_email on public.users(email);
   create index idx_profiles_subreddit on public.behavioral_profiles(subreddit);
   ```

2. **Use HNSW indexes for vector similarity** (10-100x faster than sequential scan):
   ```sql
   create index behavioral_profiles_embeddings_idx
     on public.behavioral_profiles
     using hnsw (archetype_embeddings vector_cosine_ops);
   ```

3. **Connection pooling:** Port 6543 (Transaction Mode) with 10-20 max connections.

### FastAPI

1. **Use async/await everywhere** (no blocking I/O in async routes)
2. **Use httpx instead of requests** (async HTTP client)
3. **Enable Gzip compression** for API responses
4. **Use Pydantic models** for request/response (automatic validation + serialization)

### Celery

1. **Separate queues by workload type:** scraping, ml_processing, ai_generation, monitoring
2. **Configure worker_prefetch_multiplier=1** for task prioritization
3. **Set worker_max_tasks_per_child=1000** to prevent memory leaks in ML tasks
4. **Use JSON serialization** (40% faster than pickle, more secure)

### Next.js 15

1. **Use Server Components by default** (zero client JS)
2. **Use `loading.tsx` for instant feedback** (streaming SSR)
3. **Optimize images with next/image** (automatic WebP, lazy loading)
4. **Enable Turbopack in dev** (76.7% faster startup) - stable in Next.js 15

---

## Recommended Project Structure

```
bc-rao/
├── frontend/                 # Next.js 15 app
│   ├── app/
│   │   ├── (dashboard)/     # Dashboard routes
│   │   ├── (marketing)/     # Marketing pages
│   │   ├── actions/         # Server Actions
│   │   ├── api/             # API routes (webhooks)
│   │   └── layout.tsx
│   ├── components/
│   │   ├── ui/              # Shadcn components
│   │   └── features/        # Feature components
│   ├── lib/
│   │   ├── api-client.ts    # Generated from OpenAPI
│   │   └── utils.ts
│   └── next.config.ts
│
├── backend/                  # FastAPI app
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/      # API endpoints
│   │   │   └── dependencies.py
│   │   ├── core/
│   │   │   ├── config.py    # Settings (Pydantic BaseSettings)
│   │   │   └── security.py
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── main.py
│   ├── tasks/               # Celery tasks
│   │   ├── scraping.py
│   │   ├── analysis.py
│   │   ├── generation.py
│   │   └── monitoring.py
│   ├── celery_config.py
│   ├── alembic/             # DB migrations
│   └── tests/
│
├── docker-compose.yml       # Local development (Redis, Postgres)
└── README.md
```

---

## Sources Summary

**Official Documentation (HIGH Confidence):**
- [Next.js 15 Release Notes](https://nextjs.org/blog/next-15)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery 5.6.2 Documentation](https://docs.celeryq.dev/en/main/)
- [Supabase pgvector Guide](https://supabase.com/docs/guides/database/extensions/pgvector)
- [spaCy Models Documentation](https://spacy.io/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api/reference/overview)

**Integration Guides (HIGH Confidence):**
- [Next.js FastAPI Template](https://www.vintasoftware.com/blog/next-js-fastapi-template)
- [Supabase Connection Scaling for FastAPI](https://medium.com/@papansarkar101/supabase-connection-scaling-the-essential-guide-for-fastapi-developers-2dc5c428b638)
- [FastAPI with Async SQLAlchemy 2.0](https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308)

**Best Practices (MEDIUM-HIGH Confidence):**
- [Next.js 15 Best Practices](https://www.serviots.com/blog/nextjs-development-best-practices)
- [FastAPI Best Practices Production 2026](https://fastlaunchapi.dev/blog/fastapi-best-practices-production-2026)
- [Celery Redis Best Practices](https://medium.com/@jasidhassan/celery-and-redis-asynchronous-task-processing-a1ea58956f3e)
- [Reddit API Rate Limits Guide 2026](https://painonsocial.com/blog/reddit-api-rate-limits-guide)

**Security (HIGH Confidence):**
- [Celery Security Documentation](https://docs.celeryq.dev/en/stable/userguide/security.html)
- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)

---

## Recommended Next Steps

### Phase 1: Foundation Setup
1. Initialize Next.js 15 + TypeScript + Tailwind project
2. Set up FastAPI with async SQLAlchemy 2.0
3. Connect to Supabase (port 6543, disable prepared statements)
4. Configure Redis for Celery
5. Set up CORS (explicit origins)

### Phase 2: Core Integrations
1. Implement Celery tasks for scraping, analysis, generation
2. Integrate Apify Reddit Scraper with webhooks
3. Set up OpenRouter client (pin models)
4. Load spaCy en_core_web_md in Celery workers
5. Generate TypeScript client from FastAPI OpenAPI schema

### Phase 3: Feature Development
1. Build behavioral analysis pipeline (Celery + spaCy)
2. Implement content generation (OpenRouter)
3. Add post monitoring (Celery periodic tasks)
4. Integrate Stripe payments + webhooks
5. Set up Resend for email notifications

### Phase 4: Production Readiness
1. Configure connection pooling (Supabase Transaction Mode)
2. Set up Celery queues (scraping, ml, ai, monitoring)
3. Implement rate limiting (per subscription tier)
4. Add monitoring (Sentry, PostHog)
5. Deploy (Vercel for Next.js, Railway/Fly.io for FastAPI)

---

**Stack Research Complete**
**Overall Confidence:** HIGH (locked stack validated, integration patterns documented, critical gotchas identified)

**Key Takeaway:** This stack is production-ready for BC-RAO. The primary engineering challenges are around connection management (Supabase Transaction Mode), task orchestration (Celery queue design), and content quality consistency (OpenRouter model selection). All have documented solutions.
