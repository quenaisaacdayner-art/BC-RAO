# Phase 2: Collection Pipeline - Research

**Researched:** 2026-02-10
**Domain:** Async data collection with Reddit scraping, LLM classification, and real-time progress tracking
**Confidence:** HIGH

## Summary

Phase 2 implements a complete data collection pipeline: Reddit scraping via Apify, local regex pre-filtering, LLM-based archetype classification, and real-time progress tracking. The architecture must handle async operations with Celery workers, stream progress updates to the frontend, and present results through an interactive filtering UI.

The standard approach combines Apify Python SDK for managed Reddit scraping, Celery for async task orchestration with `update_state()` progress tracking, Server-Sent Events (SSE) for one-way real-time updates to the browser, and Shadcn/UI components for the progress bar and card grid interface. PostgreSQL `INSERT ON CONFLICT` provides atomic deduplication for re-collection scenarios.

Key insight: SSE is preferred over WebSockets for progress updates because the communication is unidirectional (server → client), simpler to implement, and works better with existing HTTP infrastructure. Celery's `bind=True` pattern with `update_state()` provides the foundation for real-time progress tracking.

**Primary recommendation:** Use SSE with FastAPI streaming responses for progress updates, Celery bound tasks with custom PROGRESS state, and Shadcn Progress + Card components for the UI. Enforce deduplication at the database level with unique constraints on Reddit post IDs.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Collection trigger & progress:**
- Collection is part of a guided flow after campaign creation — "Now let's collect data for your subreddits" step
- Live progress bar with real-time stats: "Scraped 847 posts → 142 passed regex → 14 classified" with animated progress
- User is encouraged to stay on the page — "Collection in progress, are you sure?" prompt if navigating away
- Collection runs count: display remaining collections based on plan (5 free / 20 pro per week) — billing enforcement itself deferred to Phase 6, but UI should show the count

**Filtering & classification visibility:**
- Detailed funnel breakdown visible: "1,200 scraped → 180 passed regex (85% filtered) → 18 top posts classified" with expandable filter reasons
- Archetypes presented as grouped sections: "Journey Posts (7)" / "Problem-Solution Posts (5)" / "Feedback Posts (6)"
- No LLM classification reasoning exposed to user — just the archetype label
- Success score display: Claude's discretion on whether numeric score + bar or tier labels

**Collected data browsing:**
- Card grid layout (Reddit-style) — title, snippet, archetype badge, score, subreddit. Click to expand.
- Three filters available: archetype dropdown, subreddit dropdown, and score range slider
- Post detail opens in a modal: full Reddit post text, metadata (author, date, upvotes, comments), archetype, success score
- Re-collection via "Collect More" button — appends new posts with deduplication, does not replace
- Show remaining collection runs on the button (e.g., "Collect More (3 left)")

**Pipeline behavior & errors:**
- Partial failure: continue with successful subreddits, show warning for failed ones ("Failed to collect from r/xyz — try again later")
- No automatic retry — user can manually "Collect More" to try again
- Zero-match subreddits: aggregate warning only ("Some subreddits had no matching posts") — not per-subreddit granular feedback
- No cost estimate before collection — just run it, costs are low

### Claude's Discretion

- Completion UX (auto-transition to results vs toast notification)
- Success score display format (numeric + bar vs tier labels)
- Exact progress bar implementation and update frequency
- Card grid column count and responsive breakpoints
- Filter UI component choices (dropdowns, sliders, chips)

### Deferred Ideas (OUT OF SCOPE)

- Billing enforcement for collection limits (5 free / 20 pro per week) — Phase 6 handles plan limit enforcement, but Phase 2 UI should be designed to support displaying remaining count
- Scheduled/automatic collection — would be a new capability, not in scope
</user_constraints>

---

## Standard Stack

The established libraries/tools for this domain:

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `apify-client` | Latest | Python SDK for Apify actor execution | Official Apify SDK with automatic retries, JSON handling, and managed actor orchestration |
| `celery[redis]` | 5.3.0+ | Async task queue with progress tracking | Industry standard for Python async jobs with `update_state()` for real-time progress |
| `redis` | 5.0.0+ | Message broker and result backend | Fast, reliable broker for Celery with pub/sub support |
| Shadcn Progress | Latest | Progress bar component | Accessible Radix UI-based component with smooth CSS transitions |
| Shadcn Card | Latest | Card grid layout | Responsive, mobile-first card component with Tailwind styling |
| Shadcn Dialog | Latest | Modal for post details | Accessible modal with focus trapping and keyboard navigation |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| FastAPI SSE | Built-in | Server-Sent Events streaming | Real-time one-way updates (progress tracking) |
| `EventSource` (browser) | Native API | SSE client connection | Frontend consumption of SSE streams |
| Shadcn Slider | Latest | Range slider for score filtering | Accessible range input with Radix UI primitives |
| Shadcn Select | Latest | Dropdown filters (archetype, subreddit) | Keyboard-navigable, accessible dropdown |
| `useSearchParams` (Next.js) | Built-in | URL state for filters | Shareable, bookmarkable filter states |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SSE | WebSockets | WebSockets add complexity for bidirectional communication we don't need; SSE is simpler for one-way updates |
| Celery `update_state()` | Polling task status | Custom polling requires more client code; `update_state()` is Celery's built-in pattern |
| Apify managed actors | Custom Reddit API client | Reddit API has strict rate limits and auth complexity; Apify actors handle proxy rotation and blocks |
| PostgreSQL unique constraint | Application-level deduplication | App logic can miss race conditions; DB constraint is atomic and guaranteed |

**Installation:**

```bash
# Backend
pip install apify-client celery[redis] redis

# Frontend (already installed in Phase 1)
npx shadcn-ui@latest add progress card dialog slider select
```

---

## Architecture Patterns

### Recommended Project Structure

```
bc-rao-api/app/
├── workers/
│   ├── celery_app.py              # Celery instance (exists)
│   └── collection_worker.py       # NEW: Collection task with progress tracking
├── integrations/
│   └── apify_client.py            # NEW: Apify SDK wrapper
├── api/
│   └── collection.py              # NEW: Endpoints for triggering collection + SSE progress
├── services/
│   └── collection_service.py      # NEW: Business logic for collection pipeline
└── models/
    └── raw_posts.py               # NEW: Pydantic models for raw_posts

bc-rao-frontend/
├── app/
│   ├── api/
│   │   └── collection/
│   │       └── [campaignId]/
│   │           └── progress/
│   │               └── route.ts   # NEW: SSE endpoint proxy
│   └── campaigns/
│       └── [id]/
│           └── collect/
│               └── page.tsx       # NEW: Collection UI
└── components/
    ├── collection/
    │   ├── ProgressTracker.tsx    # NEW: Live progress component
    │   ├── PostGrid.tsx           # NEW: Filtered card grid
    │   └── PostDetailModal.tsx    # NEW: Post detail modal
    └── ui/
        ├── progress.tsx           # Shadcn (add via CLI)
        ├── card.tsx               # Shadcn (exists)
        ├── dialog.tsx             # Shadcn (add via CLI)
        ├── slider.tsx             # Shadcn (add via CLI)
        └── select.tsx             # Shadcn (add via CLI)
```

### Pattern 1: Celery Task with Progress Tracking

**What:** Celery bound task that calls `self.update_state()` to emit custom PROGRESS states with metadata
**When to use:** Any long-running task requiring real-time progress visibility (collection, classification)

**Example:**

```python
# Source: https://docs.celeryq.dev/en/stable/userguide/tasks.html
from celery import shared_task

@shared_task(bind=True)
def collect_campaign_data(self, campaign_id: str):
    """
    Collects Reddit posts with real-time progress updates.
    """
    # Fetch campaign and subreddits
    campaign = get_campaign(campaign_id)
    subreddits = campaign.target_subreddits

    total_steps = len(subreddits)
    scraped_total = 0
    filtered_total = 0
    classified_total = 0

    for i, subreddit in enumerate(subreddits):
        # Update progress state
        if not self.request.called_directly:
            self.update_state(
                state='PROGRESS',
                meta={
                    'current_step': i + 1,
                    'total_steps': total_steps,
                    'current_subreddit': subreddit,
                    'scraped': scraped_total,
                    'filtered': filtered_total,
                    'classified': classified_total,
                }
            )

        # Execute scraping, filtering, classification
        posts = scrape_subreddit(subreddit)
        scraped_total += len(posts)

        filtered = apply_regex_filter(posts)
        filtered_total += len(filtered)

        classified = classify_top_posts(filtered)
        classified_total += len(classified)

    return {
        'status': 'complete',
        'scraped': scraped_total,
        'filtered': filtered_total,
        'classified': classified_total,
    }
```

### Pattern 2: FastAPI SSE Endpoint for Progress Streaming

**What:** FastAPI endpoint that streams Celery task state updates as Server-Sent Events
**When to use:** Real-time progress updates from backend to frontend

**Example:**

```python
# Source: https://fastapi.tiangolo.com/advanced/custom-response/
# Verified: https://medium.com/@inandelibas/real-time-notifications-in-python-using-sse-with-fastapi-1c8c54746eb7
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from celery.result import AsyncResult
import asyncio
import json

router = APIRouter()

async def progress_stream(task_id: str):
    """Generator that yields SSE-formatted progress updates."""
    result = AsyncResult(task_id)

    while not result.ready():
        state = result.state
        info = result.info or {}

        # SSE format: "data: {json}\n\n"
        data = json.dumps({
            'state': state,
            'meta': info,
        })
        yield f"data: {data}\n\n"

        await asyncio.sleep(0.5)  # Poll every 500ms

    # Final result
    final_data = json.dumps({
        'state': 'SUCCESS',
        'result': result.result,
    })
    yield f"data: {final_data}\n\n"

@router.get("/collection/{task_id}/progress")
async def stream_progress(task_id: str):
    """SSE endpoint for real-time collection progress."""
    return StreamingResponse(
        progress_stream(task_id),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',  # Prevent NGINX buffering
        }
    )
```

### Pattern 3: React SSE Client with EventSource

**What:** React component that connects to SSE endpoint, updates progress state, and cleans up on unmount
**When to use:** Frontend consumption of real-time server updates

**Example:**

```tsx
// Source: https://oneuptime.com/blog/post/2026-01-15-server-sent-events-sse-react/view
'use client'

import { useEffect, useState } from 'react'
import { Progress } from '@/components/ui/progress'

export function ProgressTracker({ taskId }: { taskId: string }) {
  const [progress, setProgress] = useState({
    scraped: 0,
    filtered: 0,
    classified: 0,
    currentStep: 0,
    totalSteps: 0,
  })
  const [complete, setComplete] = useState(false)

  useEffect(() => {
    const eventSource = new EventSource(`/api/collection/${taskId}/progress`)

    eventSource.addEventListener('message', (event) => {
      const data = JSON.parse(event.data)

      if (data.state === 'PROGRESS') {
        setProgress(data.meta)
      } else if (data.state === 'SUCCESS') {
        setComplete(true)
        eventSource.close()
      }
    })

    eventSource.addEventListener('error', (error) => {
      console.error('SSE error:', error)
      eventSource.close()
    })

    // Cleanup on unmount
    return () => {
      eventSource.close()
    }
  }, [taskId])

  const progressPercent = progress.totalSteps > 0
    ? (progress.currentStep / progress.totalSteps) * 100
    : 0

  return (
    <div>
      <Progress value={progressPercent} />
      <p className="text-sm text-muted-foreground mt-2">
        Scraped {progress.scraped} posts → {progress.filtered} passed regex → {progress.classified} classified
      </p>
      {complete && <p className="text-green-600">Collection complete!</p>}
    </div>
  )
}
```

### Pattern 4: Apify Actor Execution with Result Retrieval

**What:** Use Apify Python client to run Reddit scraper actors and retrieve datasets
**When to use:** Scraping Reddit posts from target subreddits

**Example:**

```python
# Source: https://docs.apify.com/api/client/python
from apify_client import ApifyClient

def scrape_subreddit(subreddit: str, keywords: list[str]) -> list[dict]:
    """
    Scrapes Reddit posts from a subreddit using Apify actor.

    Args:
        subreddit: Subreddit name (e.g., 'SaaS')
        keywords: List of keyword filters

    Returns:
        List of post dictionaries with title, text, url, score, etc.
    """
    client = ApifyClient(settings.APIFY_API_TOKEN)

    # Configure actor input
    actor_input = {
        'subreddits': [subreddit],
        'searchTerms': keywords,
        'maxPosts': 100,
        'sort': 'hot',
        'timeFilter': 'month',
    }

    # Run actor and wait for completion
    actor = client.actor('trudax/reddit-scraper')
    run = actor.call(run_input=actor_input)

    # Retrieve dataset results
    dataset = client.dataset(run['defaultDatasetId'])
    items = dataset.list_items().items

    return items
```

### Pattern 5: PostgreSQL Deduplication with INSERT ON CONFLICT

**What:** Use PostgreSQL's `INSERT ... ON CONFLICT DO NOTHING` for atomic deduplication during re-collection
**When to use:** Appending new posts without duplicating existing ones (user clicks "Collect More")

**Example:**

```python
# Source: https://neon.com/postgresql/postgresql-tutorial/postgresql-upsert
# Schema: raw_posts table has unique constraint on reddit_post_id

async def store_posts_with_dedup(posts: list[dict], campaign_id: str):
    """
    Stores posts with automatic deduplication using INSERT ON CONFLICT.

    Args:
        posts: List of Reddit post data
        campaign_id: Campaign UUID
    """
    query = """
        INSERT INTO raw_posts (
            id, campaign_id, user_id, reddit_post_id,
            raw_text, title, subreddit, archetype, success_score
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (reddit_post_id) DO NOTHING
        RETURNING id;
    """

    inserted_count = 0
    for post in posts:
        result = await db.fetchval(
            query,
            uuid4(), campaign_id, user_id, post['id'],
            post['selftext'], post['title'], post['subreddit'],
            post['archetype'], post['success_score']
        )
        if result:
            inserted_count += 1

    return inserted_count
```

### Pattern 6: URL State Management for Filters

**What:** Store filter state (archetype, subreddit, score range) in URL query parameters for shareable links
**When to use:** Interactive filtering UI where users expect shareable/bookmarkable states

**Example:**

```tsx
// Source: https://blog.logrocket.com/url-state-usesearchparams/
'use client'

import { useSearchParams, useRouter } from 'next/navigation'
import { Select } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'

export function PostFilters() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const archetype = searchParams.get('archetype') || 'all'
  const subreddit = searchParams.get('subreddit') || 'all'
  const minScore = parseInt(searchParams.get('minScore') || '0')

  const updateFilter = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams)
    if (value === 'all') {
      params.delete(key)
    } else {
      params.set(key, value)
    }
    router.push(`?${params.toString()}`)
  }

  return (
    <div className="flex gap-4">
      <Select
        value={archetype}
        onValueChange={(val) => updateFilter('archetype', val)}
      >
        <option value="all">All Archetypes</option>
        <option value="journey">Journey</option>
        <option value="problem-solution">Problem-Solution</option>
        <option value="feedback">Feedback</option>
      </Select>

      <Select
        value={subreddit}
        onValueChange={(val) => updateFilter('subreddit', val)}
      >
        <option value="all">All Subreddits</option>
        {/* Dynamic options from campaign */}
      </Select>

      <Slider
        value={[minScore]}
        onValueChange={([val]) => updateFilter('minScore', val.toString())}
        min={0}
        max={10}
        step={1}
      />
    </div>
  )
}
```

### Anti-Patterns to Avoid

- **Polling for progress instead of SSE:** Polling creates unnecessary server load and delay; SSE provides instant updates with less overhead
- **Storing EventSource in state instead of ref:** Causes re-creation on re-renders; use `useRef` to persist connection across renders
- **Missing EventSource cleanup:** Leads to connection leaks; always return cleanup function from `useEffect` that calls `eventSource.close()`
- **Application-level deduplication instead of DB constraint:** Race conditions can slip through; use `INSERT ON CONFLICT` for atomic guarantees
- **Exposing Celery task internals to frontend:** Tight coupling; use a service layer to abstract Celery implementation details
- **Hard-coding Apify actor IDs in business logic:** Makes testing difficult; inject actor IDs via config/environment variables

---

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Reddit scraping with auth/proxies | Custom Reddit API client with rate limit handling | Apify managed actors (`trudax/reddit-scraper`) | Reddit API has strict rate limits, blocks server IPs, requires OAuth for many endpoints. Apify actors handle proxy rotation, CAPTCHA solving, and rate limit backoff |
| Real-time progress updates | Custom WebSocket server with connection management | FastAPI SSE streaming + Celery `update_state()` | WebSockets require bidirectional protocol upgrade, connection pooling, reconnection logic. SSE works over HTTP, auto-reconnects, and browsers limit concurrent connections (typically 6) |
| Post deduplication logic | Application-level duplicate checking before insert | PostgreSQL `INSERT ON CONFLICT` with unique constraint | App-level checks have race conditions in concurrent scenarios. DB unique constraint is atomic and guaranteed even under high concurrency |
| Regex performance optimization | Custom regex engine or string matching | Python `re.compile()` with compiled patterns | Regex compilation is a solved problem. Pre-compile patterns once, reuse many times. For extremely high volume, consider `flashtext` for literal strings |
| Progress bar animation | Custom CSS transitions and update throttling | Shadcn Progress (Radix UI) with CSS transitions | Radix UI handles accessibility (ARIA roles, screen reader announcements), smooth transitions (200ms default), and edge cases (clamping invalid values) |
| Filter state persistence | Custom localStorage/sessionStorage logic | Next.js `useSearchParams` for URL state | URL state is shareable, bookmarkable, and SSR-compatible. Custom storage requires manual sync, serialization, and edge case handling |

**Key insight:** Managed services (Apify) and framework primitives (SSE, Celery state, PostgreSQL constraints) handle edge cases and concurrency issues that custom solutions often miss. The cost savings from avoiding hand-rolled solutions far exceed the subscription/compute costs of managed services.

---

## Common Pitfalls

### Pitfall 1: SSE Buffering in Production (NGINX)

**What goes wrong:** SSE stream works locally but buffers in production, delaying all updates until task completion

**Why it happens:** NGINX (common reverse proxy on Vercel/Railway) buffers responses by default to optimize throughput

**How to avoid:** Add `X-Accel-Buffering: no` header to SSE responses:

```python
return StreamingResponse(
    progress_stream(task_id),
    media_type="text/event-stream",
    headers={
        'X-Accel-Buffering': 'no',  # Critical for NGINX
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
    }
)
```

**Warning signs:** Progress updates arrive in batches after task completes, not incrementally

**Sources:**
- [Fixing Slow SSE in Next.js and Vercel (Medium, Jan 2026)](https://medium.com/@oyetoketoby80/fixing-slow-sse-server-sent-events-streaming-in-next-js-and-vercel-99f42fbdb996)

### Pitfall 2: EventSource Connection Leaks

**What goes wrong:** Frontend opens new SSE connections on every re-render, hitting browser's 6-connection limit and blocking other requests

**Why it happens:** Creating `EventSource` inside component body without cleanup causes re-creation on state changes

**How to avoid:** Always wrap EventSource in `useEffect` with cleanup function:

```tsx
useEffect(() => {
  const eventSource = new EventSource(url)

  eventSource.addEventListener('message', handler)
  eventSource.addEventListener('error', errorHandler)

  return () => {
    eventSource.close()  // Critical cleanup
  }
}, [url])  // Only recreate if URL changes
```

**Warning signs:** Other API requests hang after multiple navigation cycles, browser DevTools shows many pending EventSource connections

**Sources:**
- [React SSE Cleanup Best Practices (OneUpTime, Jan 2026)](https://oneuptime.com/blog/post/2026-01-15-server-sent-events-sse-react/view)

### Pitfall 3: Celery Task Not Updating Progress

**What goes wrong:** Task runs successfully but progress updates never appear in frontend

**Why it happens:** Forgot `bind=True` decorator or checking `self.request.called_directly` prevents updates during testing

**How to avoid:**

```python
@shared_task(bind=True)  # Must bind to access self
def my_task(self, data):
    if not self.request.called_directly:  # Skip during direct calls
        self.update_state(state='PROGRESS', meta={...})
```

**Warning signs:** Task completes but frontend progress bar stays at 0%, no intermediate states logged

**Sources:**
- [Celery Task Monitoring (Official Docs)](https://docs.celeryq.dev/en/stable/userguide/tasks.html)

### Pitfall 4: Apify Actor Cost Overruns

**What goes wrong:** Collection runs consume more compute units than expected, inflating costs

**Why it happens:** Apify charges based on memory × time. Scraping 1000 posts with 1024MB allocation for 10 minutes = ~0.17 CU (~$0.04), but setting maxPosts too high or scraping slow subreddits can balloon costs

**How to avoid:**
- Set reasonable `maxPosts` limits (100-200 per subreddit)
- Use `timeFilter: 'month'` to avoid scraping entire subreddit history
- Monitor actor run durations in Apify console
- Budget check before LLM calls (already in Phase 1 infrastructure)

**Warning signs:** Compute unit consumption > 1 CU per collection run, actor runs taking >5 minutes

**Sources:**
- [Apify Pricing Calculation (Use Apify Docs)](https://use-apify.com/docs/what-is-apify/apify-pricing)

### Pitfall 5: Race Conditions in Deduplication

**What goes wrong:** Duplicate posts inserted despite application-level duplicate checks

**Why it happens:** Two concurrent collection tasks check for existence, both see "not exists", both insert → duplicates

**How to avoid:** Use database-level unique constraint:

```sql
-- In migration
ALTER TABLE raw_posts
ADD CONSTRAINT unique_reddit_post_id UNIQUE (reddit_post_id);

-- In code
INSERT INTO raw_posts (...) VALUES (...)
ON CONFLICT (reddit_post_id) DO NOTHING;
```

**Warning signs:** Same Reddit post appears multiple times in results grid after re-collection

**Sources:**
- [PostgreSQL Deduplication Strategies (Alibaba Cloud)](https://www.alibabacloud.com/blog/postgresql-data-deduplication-methods_596032)

### Pitfall 6: Slow Regex on Large Datasets

**What goes wrong:** Regex pre-filtering takes minutes instead of seconds, blocking collection pipeline

**Why it happens:** Complex patterns cause excessive backtracking; compiling pattern inside loop instead of once

**How to avoid:**
- Compile patterns once at module level: `PATTERN = re.compile(r'...')`
- Avoid nested quantifiers: `.*.*` causes backtracking
- Use non-capturing groups: `(?:...)` instead of `(...)`
- For literal strings, use `flashtext` library instead of regex

**Warning signs:** Regex filtering taking >10ms per post, high CPU during filtering step

**Sources:**
- [Optimizing Regex Performance in Python (PeerDH)](https://peerdh.com/blogs/programming-insights/optimizing-regex-performance-for-large-datasets-in-python)

### Pitfall 7: Supabase RLS Performance with Filters

**What goes wrong:** Post grid query with filters becomes slow as data grows (>10k posts)

**Why it happens:** RLS policies evaluate on every query; filtering by archetype + subreddit + score without indexes causes table scans

**How to avoid:**
- Add indexes on filter columns: `CREATE INDEX idx_raw_posts_filters ON raw_posts(archetype, subreddit, success_score)`
- Include `user_id` in compound index since RLS always filters by user
- Keep RLS policies simple: just `user_id = auth.uid()`, not complex joins

**Warning signs:** Filter queries taking >500ms, EXPLAIN ANALYZE shows Seq Scan instead of Index Scan

**Sources:**
- [Supabase RLS Best Practices (Leanware)](https://www.leanware.co/insights/supabase-best-practices)

---

## Code Examples

Verified patterns from official sources:

### Celery Separate Queue Configuration

```python
# Source: https://docs.celeryq.dev/en/latest/userguide/routing.html
# app/workers/celery_app.py

from kombu import Exchange, Queue
from celery import Celery

app = Celery('bc-rao')

# Define separate queues for different task types
app.conf.task_queues = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('collection', Exchange('collection'), routing_key='collection.scrape'),
    Queue('classification', Exchange('classification'), routing_key='classification.llm'),
)

# Route tasks to specific queues
app.conf.task_routes = {
    'app.workers.collection_worker.collect_campaign_data': {
        'queue': 'collection',
        'routing_key': 'collection.scrape',
    },
    'app.workers.classification_worker.classify_posts': {
        'queue': 'classification',
        'routing_key': 'classification.llm',
    },
}

# Start workers for specific queues
# celery -A app.workers.celery_app worker -Q collection --concurrency=2
# celery -A app.workers.celery_app worker -Q classification --concurrency=4
```

### Shadcn Card Grid with Responsive Layout

```tsx
// Source: https://ui.shadcn.com/docs/components/radix/card
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function PostGrid({ posts }: { posts: Post[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {posts.map((post) => (
        <Card key={post.id} className="cursor-pointer hover:shadow-lg transition-shadow">
          <CardHeader>
            <CardTitle className="text-lg line-clamp-2">{post.title}</CardTitle>
            <div className="flex gap-2 mt-2">
              <Badge variant="secondary">{post.archetype}</Badge>
              <Badge variant="outline">r/{post.subreddit}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground line-clamp-3">
              {post.raw_text}
            </p>
            <div className="flex justify-between items-center mt-4">
              <span className="text-xs text-muted-foreground">
                Score: {post.success_score}/10
              </span>
              <span className="text-xs text-muted-foreground">
                {post.upvotes} upvotes
              </span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
```

### Shadcn Dialog for Post Detail Modal

```tsx
// Source: https://ui.shadcn.com/docs/components/radix/dialog
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

export function PostDetailModal({ post, open, onClose }: Props) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{post.title}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="flex gap-2">
            <Badge>{post.archetype}</Badge>
            <Badge variant="outline">r/{post.subreddit}</Badge>
            <Badge variant="secondary">Score: {post.success_score}/10</Badge>
          </div>

          <div className="prose max-w-none">
            <p className="whitespace-pre-wrap">{post.raw_text}</p>
          </div>

          <div className="grid grid-cols-2 gap-4 pt-4 border-t">
            <div>
              <p className="text-sm font-medium">Author</p>
              <p className="text-sm text-muted-foreground">{post.author}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Posted</p>
              <p className="text-sm text-muted-foreground">
                {new Date(post.created_at).toLocaleDateString()}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium">Upvotes</p>
              <p className="text-sm text-muted-foreground">{post.upvotes}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Comments</p>
              <p className="text-sm text-muted-foreground">{post.num_comments}</p>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| WebSockets for all real-time updates | SSE for one-way updates, WebSockets for bidirectional | ~2020-2022 | SSE is simpler, works over HTTP, auto-reconnects. Use WebSockets only when client needs to send frequent updates |
| Manual `AsyncResult.get()` polling | Celery `update_state()` with SSE streaming | Celery 4.0+ (2016) | Built-in progress tracking eliminates custom polling logic and reduces server load |
| Redis-only result backend | Redis for broker + PostgreSQL for results (optional) | Celery 5.0+ (2020) | PostgreSQL result backend enables SQL queries on task history, but Redis is still standard for simple cases |
| Application-level deduplication | PostgreSQL `INSERT ON CONFLICT` (upsert) | PostgreSQL 9.5+ (2015) | Atomic guarantees, eliminates race conditions, simplifies code |
| Custom Reddit API clients | Apify managed actors | ~2020+ | Apify handles proxy rotation, rate limits, CAPTCHA solving, and API changes |
| Prop drilling for filter state | URL query parameters with `useSearchParams` | React Router v6+ (2021) | Shareable, bookmarkable state without complex state management |

**Deprecated/outdated:**
- **Celery Flower for progress tracking:** Flower is a monitoring tool, not a user-facing progress UI. Use Celery `update_state()` + SSE for end-user progress visibility
- **Django Celery Progress:** Django-specific library; FastAPI projects should use vanilla Celery `update_state()` pattern
- **localStorage for filter state:** Not shareable or SSR-compatible; URL state is the modern standard for Next.js apps

---

## Open Questions

Things that couldn't be fully resolved:

1. **Apify Actor Selection**
   - What we know: Multiple Reddit scraper actors exist on Apify marketplace (`trudax/reddit-scraper`, `parseforge/reddit-posts-comments-scraper`, etc.)
   - What's unclear: Which actor has best cost/performance tradeoff for our use case (keywords + subreddit filtering, 100-200 posts per run)
   - Recommendation: Start with `trudax/reddit-scraper` (most popular, 4.5★ rating), test cost/performance, switch if needed. Actor ID should be configurable via environment variable for easy switching

2. **Success Score Display Format**
   - What we know: User decisions leave success score format to Claude's discretion (numeric + bar vs tier labels)
   - What's unclear: Which format better communicates post quality to users without requiring explanation
   - Recommendation: Use **numeric score + progress bar** (e.g., "7/10" with 70% filled bar). Rationale: Numeric anchors intuition ("7 is pretty good"), visual bar shows relative quality at a glance, no need to explain tier boundaries. Avoid tier labels like "High/Medium/Low" which feel arbitrary without context

3. **SSE Reconnection Strategy**
   - What we know: Browser `EventSource` auto-reconnects on connection drop, but task may complete during disconnection
   - What's unclear: Should we persist progress state in Redis to survive reconnections, or just show final result if reconnection happens post-completion?
   - Recommendation: For MVP, rely on `EventSource` auto-reconnect + Celery result backend. If reconnection happens after completion, SSE endpoint should immediately send final SUCCESS state. Add Redis-persisted progress only if users report frequent mid-collection disconnections

4. **Filter Performance Threshold**
   - What we know: Need indexes on filter columns (archetype, subreddit, success_score), RLS policies can impact performance
   - What's unclear: At what data volume (1k, 10k, 100k posts) do we need pagination vs infinite scroll vs virtualization?
   - Recommendation: Start with simple pagination (20 posts per page) at Phase 2 launch. Add infinite scroll if users complain about pagination UX. Virtualization (react-window) only needed if single-campaign post count exceeds 10k (unlikely in Trial/Starter plans)

---

## Sources

### Primary (HIGH confidence)

- **Celery Official Documentation** - [Tasks](https://docs.celeryq.dev/en/stable/userguide/tasks.html) - Progress tracking with `update_state()`
- **Celery Official Documentation** - [Routing](https://docs.celeryq.dev/en/latest/userguide/routing.html) - Queue configuration and task routing
- **FastAPI Official Documentation** - [WebSockets](https://fastapi.tiangolo.com/advanced/websockets/) - WebSocket endpoint patterns
- **Apify Official Documentation** - [Python Client](https://docs.apify.com/api/client/python) - Actor execution and dataset retrieval
- **Shadcn/UI Official Docs** - [Progress](https://ui.shadcn.com/docs/components/radix/progress) - Progress component usage
- **Shadcn/UI Official Docs** - [Card](https://ui.shadcn.com/docs/components/radix/card) - Card grid layout patterns
- **Shadcn/UI Official Docs** - [Dialog](https://ui.shadcn.com/docs/components/radix/dialog) - Accessible modal implementation
- **PostgreSQL Official Documentation** - [INSERT](https://www.postgresql.org/docs/current/sql-insert.html) - ON CONFLICT clause for upserts
- **Neon PostgreSQL Tutorial** - [PostgreSQL UPSERT](https://neon.com/postgresql/postgresql-tutorial/postgresql-upsert) - Deduplication patterns

### Secondary (MEDIUM confidence)

- **Real-Time Celery Progress Bars** - [Celery School](https://celery.school/celery-progress-bars-with-fastapi-htmx) - FastAPI + Celery progress implementation
- **Real-Time Notifications with SSE in FastAPI** - [Medium (İnan DELİBAŞ)](https://medium.com/@inandelibas/real-time-notifications-in-python-using-sse-with-fastapi-1c8c54746eb7) - SSE streaming pattern
- **WebSocket vs SSE vs Long Polling (2025)** - [Constantin Potapov](https://potapov.me/en/make/websocket-sse-longpolling-realtime) - Choosing real-time protocols
- **Implementing Server-Sent Events in React** - [OneUpTime Blog (Jan 2026)](https://oneuptime.com/blog/post/2026-01-15-server-sent-events-sse-react/view) - EventSource cleanup patterns
- **Fixing Slow SSE in Next.js and Vercel** - [Medium (Jan 2026)](https://medium.com/@oyetoketoby80/fixing-slow-sse-server-sent-events-streaming-in-next-js-and-vercel-99f42fbdb996) - NGINX buffering issue
- **Optimizing Regex Performance in Python** - [PeerDH](https://peerdh.com/blogs/programming-insights/optimizing-regex-performance-for-large-datasets-in-python) - Regex compilation best practices
- **Apify Pricing Explained** - [Use Apify Docs](https://use-apify.com/docs/what-is-apify/apify-pricing) - Compute unit calculation
- **PostgreSQL Deduplication Methods** - [Alibaba Cloud](https://www.alibabacloud.com/blog/postgresql-data-deduplication-methods_596032) - Unique constraint vs app logic
- **Supabase RLS Best Practices** - [Leanware](https://www.leanware.co/insights/supabase-best-practices) - RLS performance optimization
- **Multi-Tenant RLS on Supabase** - [AntStack Blog](https://www.antstack.com/blog/multi-tenant-applications-with-rls-on-supabase-postgress/) - Multi-tenancy patterns
- **React URL State Management** - [LogRocket](https://blog.logrocket.com/advanced-react-state-management-using-url-parameters/) - useSearchParams patterns
- **Shadcn Dialog Accessibility** - [NewLine (shadcn/ui Accessibility Guide)](https://www.newline.co/@eyalcohen/alt-text-and-beyond-making-your-website-accessible-with-shadcnui--0dd38704) - Accessible modal best practices

### Tertiary (LOW confidence)

- **Apify Reddit Scrapers** - [Apify Store](https://apify.com/trudax/reddit-scraper) - Available actors (need manual testing to validate)
- **OpenRouter Batch Processing** - [GitHub ValRCS](https://github.com/ValRCS/openrouter_batch_processor) - Community batch processor (not official)
- **React Progress Bar Components** - [TheLinuxCode (2026 Edition)](https://thelinuxcode.com/how-i-build-a-custom-progress-bar-component-in-react-2026-edition/) - Custom implementation patterns (marked for validation)

---

## Metadata

**Confidence breakdown:**
- **Standard stack:** HIGH - Celery, FastAPI SSE, Shadcn/UI, PostgreSQL upserts are all documented in official sources
- **Architecture patterns:** HIGH - Progress tracking, SSE streaming, and deduplication patterns verified with official docs and current (2026) Medium articles
- **Pitfalls:** MEDIUM - SSE buffering, EventSource cleanup, and RLS performance issues verified with multiple recent sources; Apify cost overruns based on docs but need real-world validation

**Research date:** 2026-02-10
**Valid until:** 2026-03-10 (30 days - stable ecosystem, Celery/FastAPI/PostgreSQL patterns unlikely to change)

**Note on Apify actors:** Multiple Reddit scraper actors exist on Apify marketplace. Specific actor selection should be validated during implementation with cost/performance testing. Actor ID must be configurable (environment variable) for easy switching without code changes.
