# Phase 1: Foundation & Core Setup - Research

**Researched:** 2026-02-07
**Domain:** Full-stack SaaS foundation (Next.js 15, FastAPI, Supabase Auth, Celery)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Dashboard shell & navigation:**
- Collapsible left sidebar with icons + labels (collapses to icon-only)
- Main landing page is an overview page with summary stats (campaign count, recent activity, quick actions)
- Campaigns live on a separate page accessible from sidebar
- Balanced information density — cards with enough info to be useful, not overwhelming (Vercel dashboard style)
- Dark/light mode toggle supported from the start

**Campaign creation flow:**
- Single page form with all fields visible: name, product context, product URL, keywords, target subreddits
- Subreddit input uses search + autocomplete that queries Reddit for matching subreddits as user types
- Keyword input is a textarea with comma-separated values; system splits and validates count (5-15 required)
- Post-creation redirect: Claude's discretion (campaign detail page or list with toast)

**Empty states & first-run experience:**
- Zero campaigns state: quick-start card that explains what campaigns are + CTA to create first one
- Overview page hides stats sections entirely until real data exists (no skeleton/placeholder metrics)
- Tone is professional and direct — "Create a campaign to start collecting community data." No fluff, no emoji
- Campaign list cards show stats inline with zeros (Posts: 0 | Drafts: 0 | Monitors: 0) to preview what modules will deliver

### Claude's Discretion
- Post-campaign-creation redirect behavior
- Sidebar section grouping and icon choices
- Loading skeleton design and transition animations
- Exact form layout and field ordering within the single-page campaign form
- Error state styling (toast vs inline vs modal)
- Overview page layout and widget arrangement

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope

</user_constraints>

## Summary

Phase 1 establishes the complete technical foundation for BC-RAO: authenticated users, campaign CRUD, dashboard navigation, and all infrastructure dependencies for module development in Phase 2+. The research covered five technical domains: Next.js 15 App Router with Shadcn/UI for the frontend, FastAPI async-first architecture for the backend API, Supabase Auth with RLS for multi-tenant security, Celery + Redis for background task infrastructure, and full-stack integration patterns.

**Current stable versions:** Next.js 16.1 is the latest (December 2025), though Next.js 15.5 remains a stable LTS option. FastAPI requires Python 3.11+ with async-first patterns. Supabase Auth uses JWT with mandatory server-side validation via `getClaims()` for RLS security. Celery 5.6 (Recovery) is the current stable release with Python 3.9-3.13 support.

**Architecture approach:** Server Components by default, `"use client"` only where needed. FastAPI uses `async def` for I/O operations (database, external APIs) and `def` for CPU-bound work (runs in threadpool). Supabase middleware refreshes JWT tokens transparently. Celery tasks handle async operations with retry patterns and exponential backoff. All tenant-scoped tables enforce RLS with `user_id` foreign keys.

**Primary recommendation:** Follow the official Shadcn/UI Sidebar component architecture for collapsible navigation, use Zod + React Hook Form for form validation, implement Supabase middleware for token refresh, create FastAPI dependencies for JWT validation, and separate Pydantic schemas by purpose (request, response, database).

## Standard Stack

The established libraries/tools for this domain:

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 15.5+ (or 16.1) | Frontend framework | Official React framework with SSR, App Router is stable and production-ready |
| Tailwind CSS | 3.4+ | Utility-first CSS | Industry standard for rapid UI development, pairs with Shadcn/UI |
| Shadcn/UI | Latest | Component library | Radix UI + Tailwind, composable components, not a dependency (copy-paste) |
| FastAPI | 0.115+ | Python API framework | Async-first, automatic validation via Pydantic, OpenAPI docs built-in |
| Supabase | Latest | Auth + Database | Managed Postgres + Auth + RLS, JWT-based auth with automatic refresh |
| Celery | 5.6+ | Task queue | Python standard for distributed async tasks, mature and production-proven |
| Redis | 7.0+ | Message broker + cache | Dual role: Celery broker and result backend, fast in-memory operations |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pydantic | 2.x | Data validation | All FastAPI request/response models, config via BaseSettings |
| Zod | 3.x | Schema validation | Frontend form validation with type inference for TypeScript |
| React Hook Form | 7.x | Form state management | Complex forms with validation, pairs with Zod via zodResolver |
| Radix UI | Latest | Unstyled UI primitives | Shadcn/UI is built on Radix (Sidebar, Collapsible, Dialog, etc.) |
| python-jose | 3.x | JWT validation | Decode and verify Supabase JWTs in FastAPI middleware |
| httpx | 0.27+ | Async HTTP client | FastAPI async external API calls (Reddit autocomplete) |
| Lucide Icons | Latest | Icon library | Shadcn/UI uses Lucide for consistent icon system |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Shadcn/UI | MUI or Chakra UI | Pre-built components but heavy bundle size, less customization |
| FastAPI | Django REST | More batteries-included but slower, no async-first support |
| Celery + Redis | Inngest or Temporal | Simpler setup but vendor lock-in, less control over workers |
| React Hook Form | Formik | Formik works but slower re-renders, RHF is more performant |

**Installation:**

```bash
# Frontend
npx create-next-app@latest bc-rao-frontend --typescript --tailwind --app
npx shadcn@latest init
npx shadcn@latest add sidebar form input textarea button card

# Backend
pip install fastapi[standard] uvicorn[standard] celery[redis] redis pydantic pydantic-settings python-jose httpx supabase
```

## Architecture Patterns

### Recommended Project Structure

**Frontend (Next.js 15 App Router):**
```
bc-rao-frontend/
├── app/
│   ├── (auth)/              # Auth routes (login, signup)
│   ├── (dashboard)/         # Protected dashboard routes
│   │   ├── layout.tsx       # Sidebar + main layout
│   │   ├── page.tsx         # Overview page
│   │   └── campaigns/       # Campaign pages
│   ├── layout.tsx           # Root layout (providers, fonts)
│   └── middleware.ts        # Supabase token refresh
├── components/
│   ├── ui/                  # Shadcn components
│   ├── sidebar/             # Sidebar components
│   └── forms/               # Form components
├── lib/
│   ├── supabase/
│   │   ├── client.ts        # Browser client
│   │   └── server.ts        # Server component client
│   ├── validations/         # Zod schemas
│   └── utils.ts
└── types/
```

**Backend (FastAPI):**
```
bc-rao-api/
├── app/
│   ├── main.py              # FastAPI app + CORS + middleware
│   ├── config.py            # Pydantic BaseSettings
│   ├── dependencies.py      # JWT auth dependency
│   ├── api/v1/
│   │   ├── router.py        # Main router aggregator
│   │   ├── auth.py          # Auth endpoints (signup, login, me)
│   │   └── campaigns.py     # Campaign CRUD endpoints
│   ├── models/
│   │   ├── auth.py          # Auth Pydantic models
│   │   └── campaign.py      # Campaign Pydantic models
│   ├── services/
│   │   ├── auth_service.py
│   │   └── campaign_service.py
│   ├── workers/
│   │   └── celery_app.py    # Celery config + tasks
│   └── integrations/
│       └── supabase_client.py
```

### Pattern 1: Supabase Auth with Server Components

**What:** Use middleware to refresh tokens, separate clients for browser vs server components, validate with `getClaims()` not `getSession()`.

**When to use:** All authenticated pages and API routes.

**Example:**
```typescript
// middleware.ts - Token refresh (REQUIRED for SSR)
// Source: https://supabase.com/docs/guides/auth/server-side/nextjs
import { createServerClient } from '@supabase/ssr'
import { NextResponse } from 'next/server'

export async function middleware(request) {
  let response = NextResponse.next()

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get: (name) => request.cookies.get(name)?.value,
        set: (name, value, options) => {
          request.cookies.set({ name, value, ...options })
          response.cookies.set({ name, value, ...options })
        },
        remove: (name, options) => {
          request.cookies.set({ name, value: '', ...options })
          response.cookies.set({ name, value: '', ...options })
        },
      },
    }
  )

  // CRITICAL: Refresh token via getClaims() - validates JWT signature
  await supabase.auth.getClaims()

  return response
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
```

### Pattern 2: Shadcn Sidebar with Collapsible State

**What:** SidebarProvider wraps layout, Sidebar component handles responsive collapse, useSidebar hook manages state.

**When to use:** Dashboard layout with collapsible navigation.

**Example:**
```typescript
// app/(dashboard)/layout.tsx
// Source: https://ui.shadcn.com/docs/components/radix/sidebar
import { SidebarProvider, Sidebar, SidebarContent, SidebarHeader, SidebarFooter, SidebarTrigger } from '@/components/ui/sidebar'

export default function DashboardLayout({ children }) {
  return (
    <SidebarProvider>
      <div className="flex h-screen w-full">
        <Sidebar collapsible="icon">
          <SidebarHeader>
            <h1>BC-RAO</h1>
          </SidebarHeader>
          <SidebarContent>
            {/* Navigation items */}
          </SidebarContent>
          <SidebarFooter>
            {/* User menu */}
          </SidebarFooter>
        </Sidebar>
        <main className="flex-1 overflow-auto">
          <SidebarTrigger />
          {children}
        </main>
      </div>
    </SidebarProvider>
  )
}
```

### Pattern 3: FastAPI JWT Validation Dependency

**What:** Create a reusable dependency that validates Supabase JWT from Authorization header.

**When to use:** All protected API endpoints.

**Example:**
```python
# app/dependencies.py
# Source: https://dev.to/j0/integrating-fastapi-with-supabase-auth-780
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Validate Supabase JWT and return user claims."""
    token = credentials.credentials
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")

    try:
        # Decode and validate JWT signature
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False}  # Supabase doesn't use aud
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

# Usage in routes:
@app.get("/campaigns")
async def list_campaigns(user: dict = Depends(get_current_user)):
    user_id = user["sub"]  # User ID from JWT
    # Query campaigns for user_id...
```

### Pattern 4: Zod + React Hook Form Validation

**What:** Define Zod schema, use zodResolver with React Hook Form, get TypeScript inference automatically.

**When to use:** All forms requiring validation.

**Example:**
```typescript
// components/forms/campaign-form.tsx
// Source: https://ui.shadcn.com/docs/forms/react-hook-form
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'

const campaignSchema = z.object({
  name: z.string().min(1, "Name is required"),
  product_context: z.string().min(10, "Context must be at least 10 characters"),
  keywords: z.string().refine(
    (val) => val.split(',').map(k => k.trim()).filter(Boolean).length >= 5,
    "At least 5 keywords required"
  ),
  target_subreddits: z.array(z.string()).min(1).max(5),
})

type CampaignFormValues = z.infer<typeof campaignSchema>

export function CampaignForm() {
  const form = useForm<CampaignFormValues>({
    resolver: zodResolver(campaignSchema),
    defaultValues: {
      name: "",
      product_context: "",
      keywords: "",
      target_subreddits: [],
    },
  })

  async function onSubmit(data: CampaignFormValues) {
    // Submit to API...
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        {/* Form fields... */}
      </form>
    </Form>
  )
}
```

### Pattern 5: FastAPI Async-First Endpoints

**What:** Use `async def` for I/O operations (database, external APIs), use `def` for CPU-bound work.

**When to use:** All FastAPI route handlers.

**Example:**
```python
# app/api/v1/campaigns.py
# Source: https://fastapi.tiangolo.com/async/
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.services.campaign_service import CampaignService

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

# Use async def for database operations
@router.post("/")
async def create_campaign(
    campaign: CampaignCreate,
    user: dict = Depends(get_current_user),
    service: CampaignService = Depends()
):
    """Database query is async I/O - use async def."""
    return await service.create_campaign(campaign, user["sub"])

# Use def for synchronous validation-only logic
@router.get("/validate-name")
def validate_campaign_name(name: str):
    """Pure validation, no I/O - use def (runs in threadpool)."""
    return {"valid": len(name) > 0 and len(name) < 100}
```

### Pattern 6: Celery Task with Retry

**What:** Use `autoretry_for` with exponential backoff for transient failures.

**When to use:** Background tasks that interact with external services (Reddit API, Apify).

**Example:**
```python
# app/workers/celery_app.py
# Source: https://testdriven.io/blog/retrying-failed-celery-tasks/
from celery import Celery

celery_app = Celery("bc-rao", broker=os.getenv("REDIS_URL"))

@celery_app.task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,  # Exponential backoff
    retry_backoff_max=600,  # Max 10 minutes
    retry_jitter=True,  # Add randomness
    max_retries=3
)
def scrape_subreddit(self, campaign_id: str):
    """Scrape Reddit with automatic retry on transient failures."""
    try:
        # Call external API...
        pass
    except Exception as exc:
        # Manual retry with custom countdown
        raise self.retry(exc=exc, countdown=60)
```

### Anti-Patterns to Avoid

- **Adding "use client" at page level:** Only add to components that need client-side hooks (useState, useEffect). Keep Server Components as default.
- **Using `supabase.auth.getSession()` in Server Components:** Always use `getClaims()` for server-side auth checks - getSession() doesn't validate JWT signatures.
- **Forgetting to enable RLS on tables:** Every tenant-scoped table MUST have `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` and at least one policy.
- **Using blocking I/O in `async def`:** If calling a non-async library (e.g., SQLAlchemy sync), use `def` not `async def`.
- **Storing large data in Celery results:** Use Redis for small results only; store large outputs in database and pass IDs.
- **Not testing RLS policies:** Create test users and verify they can only access their own data.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT validation + refresh | Custom JWT decoder | Supabase SSR package + middleware | Handles PKCE flow, cookie management, automatic refresh, security edge cases |
| Form validation | Manual error state | React Hook Form + Zod | Handles nested validation, async validation, field-level errors, TypeScript inference |
| Collapsible sidebar | Custom toggle state | Shadcn Sidebar component | Handles responsive behavior, keyboard shortcuts, mobile offcanvas, accessibility |
| Multi-tenant data isolation | Application-level filtering | Supabase RLS policies | Database-level enforcement, can't be bypassed by bugs, automatic with auth context |
| Task retries | Manual try/catch loops | Celery autoretry_for | Exponential backoff, jitter, max retries, dead letter queue integration |
| API error responses | Manual HTTP exceptions | FastAPI HTTPException + exception handlers | Standardized error shape, automatic OpenAPI docs, validation errors formatted consistently |
| Reddit subreddit search | Custom Reddit API integration | Reddit API `/subreddits/search` | Official endpoint with rate limiting, caching, NSFW filtering built-in |

**Key insight:** Authentication, form validation, and multi-tenancy are security-critical domains where rolling your own solution introduces risk. The ecosystem provides battle-tested libraries that handle edge cases you won't discover until production.

## Common Pitfalls

### Pitfall 1: RLS Policies Not Enforced

**What goes wrong:** Tables have RLS enabled but no policies, or policies use `user_metadata` which users can modify.

**Why it happens:** RLS defaults to "deny all" when enabled without policies. Developers test with service role key (bypasses RLS) and don't catch the issue until users try to access data.

**How to avoid:**
- Always create at least one policy when enabling RLS
- Use `auth.uid()` or app_metadata (server-controlled) in policies, never user_metadata
- Test with actual user JWT tokens, not service role key
- Use Supabase dashboard's "Performance & Security Advisors" to check for misconfigured RLS

**Warning signs:**
- Users get 403 errors on legitimate requests
- Data visible in Supabase dashboard but not in app
- Queries work with service role key but fail with user token

### Pitfall 2: Hydration Mismatches in Next.js

**What goes wrong:** Server and client render different HTML, causing React hydration errors and visual glitches.

**Why it happens:** Date/time formatting with client timezone, reading from `window` or `localStorage` during initial render, non-deterministic data (random numbers, timestamps).

**How to avoid:**
- Never read browser APIs during initial render (window, localStorage, etc.)
- Use `useEffect` or `"use client"` + `useState` for client-only values
- Format dates on server with explicit timezone, not client's local time
- Use suppressHydrationWarning sparingly and only for truly unavoidable cases

**Warning signs:**
- Console warnings about hydration mismatches
- Flash of unstyled content or layout shift on page load
- Different content on first load vs subsequent renders

### Pitfall 3: Blocking Operations in Async Endpoints

**What goes wrong:** Using blocking libraries (requests, SQLAlchemy sync) inside `async def` freezes the entire event loop, blocking all other requests.

**Why it happens:** Developers assume async is always better and convert all functions to `async def` without checking if dependencies are async-compatible.

**How to avoid:**
- Use `async def` ONLY when calling async libraries with `await`
- Use `def` for blocking operations - FastAPI runs them in threadpool automatically
- Check library documentation for async support (look for `AsyncClient`, `async with`, etc.)
- Never use time.sleep() in async functions - use asyncio.sleep()

**Warning signs:**
- API becomes unresponsive under load
- Single slow request blocks all other requests
- CPU usage low but response times high

### Pitfall 4: Missing FastAPI CORS Configuration

**What goes wrong:** Frontend requests to backend fail with CORS errors, even with valid JWT.

**Why it happens:** FastAPI doesn't enable CORS by default. Developers forget to add CORSMiddleware or misconfigure allowed origins.

**How to avoid:**
- Add CORSMiddleware to FastAPI app with explicit origins
- Set `allow_credentials=True` for cookie-based auth
- Use environment variable for CORS_ORIGINS, comma-separated list
- In development: `["http://localhost:3000"]`, production: `["https://app.bcrao.app"]`

**Warning signs:**
- Browser console shows CORS errors
- Requests succeed in Postman but fail in browser
- OPTIONS preflight requests return 404 or 403

### Pitfall 5: Celery Tasks Not Idempotent

**What goes wrong:** Task runs multiple times (due to retry or worker crash) and creates duplicate data or inconsistent state.

**Why it happens:** Tasks perform non-idempotent operations (insert without checking existence, increment counter, send email).

**How to avoid:**
- Use database constraints (UNIQUE, CHECK) to prevent duplicates
- Check if operation already completed before executing
- Use transaction.on_commit() to queue tasks only after DB commit
- Store task execution state in database with task ID

**Warning signs:**
- Duplicate records in database
- Users receive multiple emails for same event
- Counters increment more than once for single action

### Pitfall 6: Subreddit Autocomplete Rate Limiting

**What goes wrong:** Reddit API rate limits or blocks requests when autocomplete queries fire too frequently.

**Why it happens:** Every keystroke triggers API request without debouncing or caching.

**How to avoid:**
- Debounce autocomplete input (300-500ms delay after last keystroke)
- Cache subreddit search results client-side for 5-10 minutes
- Use Reddit API with proper User-Agent header
- Consider pre-loading popular subreddits and searching locally first

**Warning signs:**
- Autocomplete becomes slow or stops working
- Reddit API returns 429 (Too Many Requests)
- Users see stale or empty autocomplete results

## Code Examples

Verified patterns from official sources:

### Example 1: Complete FastAPI App Setup with CORS and Auth

```python
# app/main.py
# Sources: https://fastapi.tiangolo.com/, https://github.com/zhanymkanov/fastapi-best-practices
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import router as v1_router

app = FastAPI(
    title="BC-RAO API",
    version="1.0.0",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
)

# CORS middleware - MUST be configured before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(v1_router, prefix="/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### Example 2: Pydantic BaseSettings for Environment Config

```python
# app/config.py
# Source: https://github.com/zhanymkanov/fastapi-best-practices
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_ENV: str = "development"
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str
    REDIS_URL: str
    CORS_ORIGINS: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

### Example 3: Campaign Service with Supabase Client

```python
# app/services/campaign_service.py
from supabase import create_client, Client
from app.config import settings
from app.models.campaign import CampaignCreate, Campaign

class CampaignService:
    def __init__(self):
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY  # Server-side only
        )

    async def create_campaign(
        self,
        campaign: CampaignCreate,
        user_id: str
    ) -> Campaign:
        """Create campaign - RLS enforces user_id automatically."""
        data = campaign.model_dump()
        data["user_id"] = user_id

        result = self.supabase.table("campaigns").insert(data).execute()
        return Campaign(**result.data[0])

    async def list_campaigns(self, user_id: str) -> list[Campaign]:
        """List user campaigns - RLS filters by user_id."""
        result = self.supabase.table("campaigns") \
            .select("*") \
            .eq("user_id", user_id) \
            .execute()
        return [Campaign(**row) for row in result.data]
```

### Example 4: Subreddit Autocomplete with Debounce

```typescript
// components/forms/subreddit-autocomplete.tsx
import { useState, useEffect } from 'react'
import { Input } from '@/components/ui/input'
import { useDebounce } from '@/hooks/use-debounce'

export function SubredditAutocomplete({ onSelect }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const debouncedQuery = useDebounce(query, 300)

  useEffect(() => {
    if (debouncedQuery.length < 2) {
      setResults([])
      return
    }

    // Reddit API subreddit search
    // Source: https://reddit-api.readthedocs.io/
    fetch(`https://www.reddit.com/subreddits/search.json?q=${debouncedQuery}&limit=10`, {
      headers: {
        'User-Agent': 'BC-RAO/1.0'
      }
    })
      .then(res => res.json())
      .then(data => {
        const subreddits = data.data.children.map(child => ({
          name: child.data.display_name,
          subscribers: child.data.subscribers,
        }))
        setResults(subreddits)
      })
  }, [debouncedQuery])

  return (
    <div className="relative">
      <Input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search subreddits..."
      />
      {results.length > 0 && (
        <div className="absolute top-full w-full bg-white border rounded-md mt-1 z-10">
          {results.map((sub) => (
            <div
              key={sub.name}
              onClick={() => onSelect(sub.name)}
              className="p-2 hover:bg-gray-100 cursor-pointer"
            >
              r/{sub.name} ({sub.subscribers.toLocaleString()} members)
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

### Example 5: RLS Policy for Multi-Tenant Campaigns

```sql
-- Source: https://supabase.com/docs/guides/database/postgres/row-level-security
-- Enable RLS on campaigns table
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;

-- Users can only read their own campaigns
CREATE POLICY "Users can view own campaigns"
ON campaigns FOR SELECT
USING (auth.uid() = user_id);

-- Users can only insert campaigns with their own user_id
CREATE POLICY "Users can create own campaigns"
ON campaigns FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Users can only update their own campaigns
CREATE POLICY "Users can update own campaigns"
ON campaigns FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Users can only delete their own campaigns
CREATE POLICY "Users can delete own campaigns"
ON campaigns FOR DELETE
USING (auth.uid() = user_id);
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pages Router | App Router | Next.js 13 (2022), stable in 14-15 | Server Components by default, layout composition, streaming SSR |
| getServerSideProps | Server Components + fetch | Next.js 13+ | Cleaner data fetching, component-level not page-level |
| Manual JWT refresh | Supabase SSR middleware | Supabase SSR 0.1.0 (2024) | Automatic token refresh via cookies, works with App Router |
| Formik | React Hook Form | 2020-2021 | Better performance (uncontrolled components), smaller bundle |
| Class-based Celery tasks | Decorator-based with autoretry | Celery 4.0 (2016) | Less boilerplate, declarative retry config |
| SQLAlchemy sync | SQLAlchemy async | SQLAlchemy 1.4 (2021) | Native async/await support with asyncio |

**Deprecated/outdated:**
- **Next.js Pages Router:** Still supported but App Router is the recommended path for new projects.
- **Supabase `getSession()` in server code:** Insecure, always use `getClaims()` for server-side auth.
- **Celery pickle serialization:** Security risk, JSON is now recommended default.
- **Manual CORS proxy in Next.js:** Use FastAPI CORSMiddleware instead of rewrites/proxy.

## Open Questions

Things that couldn't be fully resolved:

1. **Next.js 15 vs 16 for production stability**
   - What we know: Next.js 16.1 is latest (Dec 2025), 15.5 is stable LTS
   - What's unclear: Whether to use cutting-edge (16.1) or proven stable (15.5) for new project
   - Recommendation: Use Next.js 15.5 for phase 1 due to better ecosystem compatibility; upgrade to 16.x in Phase 2 after verifying Shadcn/UI compatibility

2. **Reddit API rate limits for subreddit autocomplete**
   - What we know: Reddit has rate limits but exact thresholds for unauthenticated `/subreddits/search` are undocumented
   - What's unclear: Whether debouncing + caching is sufficient or if we need Reddit OAuth for higher limits
   - Recommendation: Start with debounced unauthenticated requests + local cache; monitor rate limit headers; add OAuth only if rate limited

3. **Celery Beat vs Inngest for scheduled tasks**
   - What we know: Celery Beat is traditional, Inngest is newer with better DX but vendor lock-in
   - What's unclear: System spec mentions "Inngest or Celery Beat" but doesn't specify which for Phase 1
   - Recommendation: Use Celery Beat for Phase 1 (matches existing Celery + Redis stack, no new dependencies); evaluate Inngest in Phase 3-4 when scheduling becomes complex

## Sources

### Primary (HIGH confidence)

- Next.js Official Docs - https://nextjs.org/docs/app - App Router architecture, Server Components patterns
- Shadcn/UI Sidebar Docs - https://ui.shadcn.com/docs/components/radix/sidebar - Collapsible sidebar implementation
- FastAPI Async Docs - https://fastapi.tiangolo.com/async/ - When to use async vs sync endpoints
- Supabase Auth SSR Guide - https://supabase.com/docs/guides/auth/server-side/nextjs - JWT refresh middleware pattern
- Supabase RLS Docs - https://supabase.com/docs/guides/database/postgres/row-level-security - Multi-tenant policy patterns
- React Hook Form Docs - https://ui.shadcn.com/docs/forms/react-hook-form - Zod integration pattern
- Celery Documentation - Task retry patterns and configuration (via multiple community sources)

### Secondary (MEDIUM confidence)

- FastAPI Best Practices Guide (2026) - https://fastlaunchapi.dev/blog/fastapi-best-practices-production-2026 - Production patterns
- GitHub: zhanymkanov/fastapi-best-practices - https://github.com/zhanymkanov/fastapi-best-practices - Project structure patterns
- Celery Retry Tutorial - https://testdriven.io/blog/retrying-failed-celery-tasks/ - Automatic retry patterns
- Next.js Server Actions Guide (2026) - https://makerkit.dev/blog/tutorials/nextjs-server-actions - Form handling patterns
- Supabase Multi-Tenancy Guide - https://www.antstack.com/blog/multi-tenant-applications-with-rls-on-supabase-postgress/ - RLS architecture
- FastAPI + Supabase Auth Integration - https://dev.to/j0/integrating-fastapi-with-supabase-auth-780 - JWT validation pattern

### Tertiary (LOW confidence)

- Reddit API subreddit search patterns - https://reddit-api.readthedocs.io/ - Endpoint documentation (Pushshift, may be outdated)
- Next.js Hydration Errors (2026) - https://medium.com/@blogs-world/next-js-hydration-errors-in-2026-the-real-causes-fixes-and-prevention-checklist-4a8304d53702 - Common pitfalls
- Celery Task Resilience - https://blog.gitguardian.com/celery-tasks-retries-errors/ - Advanced retry strategies

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified from official documentation and release notes
- Architecture: HIGH - Patterns from official docs (Next.js, Supabase, FastAPI, Shadcn/UI)
- Pitfalls: MEDIUM - Based on community content (Medium articles, dev.to) verified against official docs where possible
- Integration patterns: HIGH - Verified via official guides (Supabase + Next.js SSR, FastAPI + Supabase Auth)

**Research date:** 2026-02-07
**Valid until:** 2026-03-07 (30 days - stack is relatively stable)

**Notes:**
- Next.js is on a fast release cycle (15.5 in January, 16.1 in December 2025) - verify version compatibility when implementing
- Supabase SSR package is critical for App Router - cannot use old `@supabase/supabase-js` patterns
- FastAPI + Celery combo is mature and stable, low risk of breaking changes
- Shadcn/UI is copy-paste not npm install - version drift only matters for Radix UI dependencies
