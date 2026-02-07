# Pitfalls Research

**Domain:** Social Intelligence Platform (Reddit Scraping + NLP + LLM Generation)
**Researched:** 2026-02-07
**Confidence:** MEDIUM-HIGH

## Critical Pitfalls

### Pitfall 1: Reddit Rate Limiting Escalation

**What goes wrong:**
Reddit enforces multi-tier rate limiting: 10 req/min unauthenticated, 60 req/min authenticated. Exceeding limits triggers HTTP 429 responses, which if ignored, escalate to temporary IP blocks lasting hours to days. For a scraping pipeline processing multiple subreddits, hitting rate limits can cascade into complete service outage.

**Why it happens:**
Developers underestimate the cumulative request volume when monitoring multiple subreddits simultaneously. Apify actors may not respect Reddit's rate limits properly, and retry logic without exponential backoff amplifies the problem.

**How to avoid:**
- Implement centralized rate limiting BEFORE Apify actors (track 60 req/min globally across all subreddits)
- Use batch endpoints (up to 100 items per request) instead of individual fetches
- Configure Apify actors with conservative request concurrency (max 1-2 concurrent requests)
- Implement circuit breaker pattern: stop all Reddit requests for 60 seconds after receiving HTTP 429
- Use OAuth authentication for all requests (never scrape unauthenticated)

**Warning signs:**
- HTTP 429 responses appearing in logs
- Increasing latency on Reddit API calls
- Apify actor runs completing with partial data
- "Connection reset by peer" errors

**Phase to address:**
Phase 1 (Core Scraping Infrastructure) - Build rate limiting as foundational infrastructure, not an afterthought.

**Sources:**
- [Reddit API Rate Limits Guide 2026](https://painonsocial.com/blog/reddit-api-rate-limits-guide)
- [Reddit API Rate Limits Workaround](https://painonsocial.com/blog/reddit-api-rate-limits-workaround)

---

### Pitfall 2: Prompt Injection via Scraped User Content

**What goes wrong:**
Reddit users can embed malicious instructions in post titles, body text, or comments designed to hijack LLM prompts. When scraped content is inserted into LLM context without sanitization, adversaries can override system instructions, extract sensitive data, or generate harmful content. Research shows 13% of web chatbots exposed scraped content directly to LLMs, creating attack venues.

**Why it happens:**
Developers treat scraped Reddit content as "data" rather than "untrusted user input." LLM prompts concatenate system instructions and user content in unstructured blobs, allowing injected instructions to override intended behavior. The pipeline prioritizes speed over security, skipping sanitization steps.

**How to avoid:**
- Isolate AI instructions from user data completely (structured prompts with separate instruction and content zones)
- Sanitize all scraped content BEFORE LLM processing:
  - Strip markdown formatting that could contain hidden instructions
  - Remove Unicode zero-width characters and homoglyphs
  - Detect and flag suspicious patterns ("Ignore previous instructions", "Disregard system prompt", etc.)
- Use LLM guardrails (input filtering layers) before main processing
- Never echo raw scraped content in LLM responses without validation
- Implement output validation to detect when LLM deviates from expected format

**Warning signs:**
- Generated content suddenly changes style or includes unexpected instructions
- LLM responses include verbatim quotes from scraped Reddit posts
- Generated content violates community guidelines despite system prompts
- Cost spikes from unusually long LLM responses

**Phase to address:**
Phase 2 (NLP + LLM Integration) - Build sanitization pipeline BEFORE connecting LLM. Treat all scraped content as hostile.

**Sources:**
- [LLM Security Risks in 2026](https://sombrainc.com/blog/llm-security-risks-2026)
- [OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- [IEEE 2026: AI Meets Web - Prompt Injection Risks](https://arxiv.org/html/2511.05797v1)

---

### Pitfall 3: LLM + Apify Cost Explosion

**What goes wrong:**
Apify credits ($0.25/compute hour + proxy costs) combined with OpenRouter LLM tokens ($3-15 per 1M tokens) create variable costs that can easily exceed $49 Starter plan revenue. Without hard caps, a single bug or viral subreddit can generate $500+ bills. Output tokens cost 3-10x more than input tokens, amplifying costs when generating long-form content.

**Why it happens:**
- No hard budget limits configured on Apify or OpenRouter accounts
- Processing ALL scraped posts instead of filtering to top 10%
- Generating verbose LLM outputs without length constraints
- Retrying failed LLM calls without exponential backoff
- Not monitoring costs in real-time (only discovering after monthly bill)

**How to avoid:**
- Set hard spending caps: Apify max $20/month, OpenRouter max $30/month
- Implement tiered filtering BEFORE LLM processing:
  1. Regex pre-filter (removes 80% of low-quality posts)
  2. SpaCy local analysis (fast, free scoring)
  3. Only top 10% get full LLM processing
- Configure LLM max_tokens to prevent runaway generation (e.g., max 500 tokens/response)
- Use cheaper models for classification tasks (e.g., GPT-4o-mini at $0.15/1M vs Claude Sonnet at $3/1M)
- Implement cost tracking middleware: log cost per request, alert at 80% daily budget
- Use Apify free tier (5,000 credits/month) for development, never production

**Warning signs:**
- Daily Apify usage exceeding 500 credits (should be ~150-200)
- OpenRouter dashboard showing >1M tokens/day
- Apify actors running longer than expected (>10 min/run)
- LLM responses frequently hitting max_tokens limit

**Phase to address:**
Phase 1 (Core Infrastructure) - Build cost monitoring and caps FIRST, before scaling scraping or LLM volume.

**Sources:**
- [OpenRouter API Pricing 2026](https://zenmux.ai/blog/openrouter-api-pricing-2026-full-breakdown-of-rates-tiers-and-usage-costs)
- [LLM API Cost Comparison 2026](https://zenvanriel.nl/ai-engineer-blog/llm-api-cost-comparison-2026/)
- [Apify Review 2026 - Pricing & ROI Data](https://hackceleration.com/apify-review/)
- [Web Scraping Proxies 2026: Higher Demand, Higher Spend](https://blog.apify.com/web-scraping-proxies/)

---

### Pitfall 4: Reddit ToS Violation and Legal Exposure

**What goes wrong:**
Reddit's updated Terms of Service explicitly prohibit commercial scraping that bypasses anti-bot protections. As of late 2025, Reddit filed lawsuits against Perplexity AI, SerpAPI, Oxylabs, and AWMProxy for "industrial-scale, unlawful" scraping. The lawsuits invoke DMCA Section 1201 (circumventing access controls), which applies even if the data is public. Using Apify with rotating proxies and fake user agents constitutes circumvention.

**Why it happens:**
Developers assume "publicly visible = legal to scrape." Using third-party scrapers (Apify) creates liability disconnect. The pipeline uses technical measures (proxies, user-agent spoofing) that courts interpret as circumvention, regardless of commercial use justification.

**How to avoid:**
- Use ONLY official Reddit API with OAuth authentication (never HTML scraping)
- Stay within API rate limits (60 req/min authenticated)
- Do NOT use Apify's proxy rotation or user-agent spoofing features
- Implement robots.txt compliance (even though API access bypasses it)
- For commercial scale (>10K posts/day), explore Reddit Data Partnership licensing
- Include clear Reddit attribution in generated content
- Store evidence of API-only usage (audit logs showing OAuth tokens, not HTML scraping)

**Warning signs:**
- Apify actors using "browser" mode instead of "API" mode
- Proxy rotation enabled in Apify configuration
- User-agent strings mimicking browsers instead of identifying your app
- Receiving cease-and-desist emails from Reddit
- IP blocks that don't resolve after OAuth authentication

**Phase to address:**
Phase 1 (Core Scraping Infrastructure) - Establish legal compliance patterns BEFORE launching. Legal debt is technical debt.

**Sources:**
- [What Happens If You Violate Reddit Scraping Rules 2026](https://painonsocial.com/blog/violate-reddit-scraping-rules)
- [How to Scrape Reddit Legally 2026](https://painonsocial.com/blog/how-to-scrape-reddit-legally)
- [Reddit Launches Legal Action Against AI Data Scrapers](https://www.socialmediatoday.com/news/reddit-launches-legal-action-against-ai-data-scrapers/803572/)

---

### Pitfall 5: Shadowban Detection False Positives

**What goes wrong:**
Shadowban detection tools cannot distinguish between shadowbanned accounts, permanently suspended accounts, and deleted accounts - all return identical signals to external observers. This creates false positive rates where legitimate posts are flagged as shadowbanned. When the platform bases post survival metrics on flawed detection, it reports misleading success rates to users.

**Why it happens:**
Reddit's shadowban system is intentionally opaque to prevent evasion. Third-party detection relies on heuristics (post visibility to logged-out users, /about.json endpoint checks) that conflate multiple account states. Apify shadowban checker actors inherit these limitations.

**How to avoid:**
- Do NOT market shadowban detection as "99% accurate" - be transparent about limitations
- Implement multi-signal detection:
  1. Check post visibility via Reddit API (authenticated vs unauthenticated)
  2. Monitor post score and comment count over time (shadowbanned posts stay at 1)
  3. Check author account status via /user/{username}/about.json
  4. Cross-reference with subreddit modlog (if accessible)
- Flag ambiguous cases as "uncertain" rather than "shadowbanned"
- Provide confidence scores instead of binary yes/no
- Warn users that recent posts (<24 hours) may be pending moderator approval, not shadowbanned

**Warning signs:**
- High variance in shadowban detection results for same post across runs
- Users reporting false positives ("my post wasn't shadowbanned")
- Detection rate significantly higher than Reddit's stated 2-5% shadowban rate
- All deleted accounts flagged as shadowbanned

**Phase to address:**
Phase 3 (Monitoring & Shadowban Detection) - Build confidence scoring and multi-signal detection from start. Single-signal detection is unreliable.

**Sources:**
- [Reddit Shadowbans 2025: How They Work](https://reddifier.com/blog/reddit-shadowbans-2025-how-they-work-how-to-detect-them-and-what-to-do-next)
- [Apify Reddit Shadowban Checker](https://apify.com/iskander/reddit-shadowban-checker)

---

### Pitfall 6: Apify Actor "Under Maintenance" Cascading Failures

**What goes wrong:**
Apify marks actors as "Under Maintenance" after 3 consecutive days of failures, and deprecates them after 28 days. For BC-RAO, this means Reddit scraping pipeline breaks silently, monitoring data goes stale, users see outdated insights, and churn increases before the team notices. Apify doesn't notify downstream users about actor maintenance status changes.

**Why it happens:**
- Reddit changes website layout (Apify HTML scrapers break)
- Reddit enables A/B testing (actor works in one region, fails in others)
- Apify actor maintainer abandons project (no updates for new Reddit features)
- Actor timeouts exceed 5-minute limit during prefill testing
- Proxy provider blocks Reddit (actor fails without clear error)

**How to avoid:**
- Use OFFICIAL Reddit API instead of Apify's community actors (avoid HTML scrapers)
- If using Apify actors, implement health checks:
  - Run test scrape daily in non-production environment
  - Alert if actor returns <50% expected data volume
  - Monitor actor's "last updated" timestamp (flag if >90 days old)
- Build fallback scraping logic (direct Reddit API calls) if Apify actor fails
- Pin actor versions (don't auto-update to latest)
- Monitor Apify's actor quality score (target >80%)
- Subscribe to actor GitHub repo for deprecation notices

**Warning signs:**
- Apify actor run duration increasing (approaching 5-min timeout)
- Partial data returns (e.g., only 20 posts instead of 100)
- Actor "last updated" timestamp >6 months old
- Actor quality score dropping below 70%
- Increased "website layout changed" errors in logs

**Phase to address:**
Phase 1 (Core Scraping Infrastructure) - Build monitoring and fallback logic from day 1. Apify is a vendor, not infrastructure.

**Sources:**
- [Apify Actor Under Maintenance Troubleshooting](https://help.apify.com/en/articles/10057123-troubleshooting-an-actor-marked-under-maintenance)
- [What to Do When Actor Comes Under Maintenance](https://help.apify.com/en/articles/9716923-what-to-do-when-your-actor-comes-under-maintenance)
- [Apify Review 2026 - Actor Reliability](https://hackceleration.com/apify-review/)

---

### Pitfall 7: Celery + Redis Memory Leak in Long-Running Workers

**What goes wrong:**
Celery workers exhibit memory leaks when using Redis as broker/backend, especially on Python 3.11+. Workers accumulate memory until OOM crashes occur, causing task failures, data loss, and service outages. Celery 5.5 and earlier had critical leaks where AsyncResult.get() never freed memory, and Redis becoming temporarily unavailable caused permanent memory retention.

**Why it happens:**
- AsyncResult subscriptions not cleaned up after results retrieved
- Workers fetching large numbers of ETA/countdown tasks without limits
- Redis connection pooling issues under high concurrency
- worker_max_tasks_per_child and worker_max_memory_per_child not configured

**How to avoid:**
- Use Celery 5.6+ (Recovery release with critical memory-leak fixes)
- Configure worker recycling to prevent unbounded memory growth:
  ```python
  worker_max_tasks_per_child = 1000  # Restart worker after 1000 tasks
  worker_max_memory_per_child = 250000  # 250MB limit per worker
  ```
- Set worker_eta_task_limit to prevent OOM when fetching scheduled tasks:
  ```python
  worker_eta_task_limit = 1000  # Max ETA tasks to fetch at once
  ```
- Monitor worker memory with Flower dashboard (alert at >200MB per worker)
- Implement task result expiration (don't store results forever):
  ```python
  result_expires = 3600  # Results expire after 1 hour
  ```
- Use task.forget() after retrieving results to free memory immediately
- Avoid long-running tasks (>5 minutes) - break into smaller subtasks

**Warning signs:**
- Worker memory usage growing linearly over time
- OOMKilled container restarts in logs
- Celery workers becoming unresponsive after 24+ hours
- Redis memory usage exceeding expected dataset size
- Tasks stuck in "pending" state despite active workers

**Phase to address:**
Phase 2 (Task Queue Infrastructure) - Configure worker recycling and result expiration from initial deployment. Memory leaks are progressive failures.

**Sources:**
- [Celery 2026: Python Distributed Task Queue Recovery](https://www.programming-helper.com/tech/celery-2026-python-distributed-task-queue-redis-rabbitmq)
- [Celery Memory Leak with Redis Broker](https://github.com/celery/celery/issues/3436)
- [Celery Optimizing Documentation](https://docs.celeryq.dev/en/stable/userguide/optimizing.html)

---

### Pitfall 8: Supabase RLS Performance Degradation at Scale

**What goes wrong:**
Row Level Security (RLS) policies with auth.uid() lookups cause query performance to degrade exponentially on large tables (>100K rows). Every query triggers full table scans unless specifically indexed. When combined with pgvector searches (already compute-intensive), queries timeout (>30 seconds), user dashboards become unusable, and connection pool exhaustion cascades into service outage.

**Why it happens:**
- RLS policies call auth.uid() function on every row evaluation
- No indexes created for user_id columns used in RLS policies
- pgvector similarity searches combined with RLS cause double-scan
- Query planner runs auth.uid() per row instead of caching result
- Default connection pool (15 connections on Free tier) exhausted by slow queries

**How to avoid:**
- Add indexes for ALL columns used in RLS policies:
  ```sql
  CREATE INDEX idx_posts_user_id ON posts(user_id);
  CREATE INDEX idx_communities_user_id ON communities(user_id);
  ```
- Wrap auth.uid() in subquery to enable caching (100x speedup on large tables):
  ```sql
  -- Bad: auth.uid() = user_id (called per row)
  -- Good: user_id IN (SELECT auth.uid()) (called once, cached)
  ```
- Use IN or ANY operators instead of direct equality for RLS:
  ```sql
  user_id = ANY(ARRAY[auth.uid()])  -- Forces initPlan optimization
  ```
- Separate pgvector searches from RLS-protected tables (use views or CTEs)
- Upgrade to at least Small compute ($25/month) for production (60 connections vs 15)
- Enable connection pooling via Supavisor (transaction mode for short queries)
- Monitor slow queries via Supabase Performance Advisors dashboard

**Warning signs:**
- Queries taking >2 seconds that should be <200ms
- Connection pool exhaustion errors ("remaining connection slots reserved")
- Supabase Performance Advisor showing RLS initPlan warnings
- pgvector queries timing out on <10K vectors
- CPU utilization spiking to 100% during dashboard loads

**Phase to address:**
Phase 2 (Database Schema & RLS Setup) - Design RLS policies with performance from day 1. Retrofitting indexes is painful.

**Sources:**
- [Supabase RLS Performance and Best Practices](https://supabase.com/docs/guides/troubleshooting/rls-performance-and-best-practices-Z5Jjwv)
- [Optimizing Vector Search: pgvector & Supabase Performance Tuning](https://medium.com/@dikhyantkrishnadalai/optimizing-vector-search-at-scale-lessons-from-pgvector-supabase-performance-tuning-ce4ada4ba2ed)
- [Supabase Performance and Security Advisors](https://supabase.com/docs/guides/database/database-advisors?lint=0003_auth_rls_initplan)

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip regex pre-filtering, send all scraped posts to LLM | Faster implementation (no filter logic) | 5x higher LLM costs, exceeds revenue within weeks | Never - filtering is business-critical |
| Use Apify community actors instead of official Reddit API | Easier setup (no OAuth flow) | Legal liability, actor maintenance breakage, ToS violations | Never for commercial use |
| Store all Celery task results indefinitely | Simpler debugging (full history) | Redis memory exhaustion, 10x higher hosting costs | Only in development/staging |
| No connection pooling limits on Supabase | Avoids configuration complexity | Connection exhaustion crashes, slow queries | Only for solo dev on Free tier |
| Single LLM provider (OpenRouter only) | Simpler integration code | Vendor lock-in, no fallback during outages | Acceptable for MVP, dangerous post-launch |
| Skip shadowban detection confidence scoring | Faster feature ship (binary yes/no) | User complaints about false positives, platform credibility loss | Never - transparency is core value prop |
| Hardcode Apify/OpenRouter API keys in codebase | Quick local development | Security breach risk, key rotation nightmare | Only in local .env (NEVER commit) |
| Use SpaCy's default English model for Reddit content | No model training required | Lower accuracy on Reddit slang/memes, misses domain nuances | Acceptable for MVP validation |

---

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Reddit OAuth | Storing access tokens indefinitely (expire after 1 hour) | Implement automatic refresh using refresh_token, handle expiration in middleware |
| Apify Actors | Not handling "Under Maintenance" status changes | Poll actor status before runs, implement fallback to direct Reddit API |
| OpenRouter | Sending entire scraped post content as LLM context | Truncate to relevant sections (title + first 500 chars), use token counting |
| Supabase pgvector | Querying vectors without HNSW index (slow full scans) | Create HNSW index: `CREATE INDEX ON posts USING hnsw (embedding vector_cosine_ops)` |
| Celery Redis | Using same Redis instance for broker + backend + caching | Separate Redis databases (db=0 broker, db=1 backend, db=2 cache) |
| SpaCy | Loading model on every request (slow cold starts) | Load model once at app startup, share across requests |
| Next.js + FastAPI | CORS errors when frontend calls backend directly | Use Next.js rewrites to proxy /api/py/* to FastAPI, avoid CORS entirely |
| Stripe Webhooks | Not verifying webhook signatures (security risk) | Validate stripe.webhook.construct_event() with secret before processing |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Synchronous Reddit scraping in API requests | Slow page loads (5-10s) | Use Celery background tasks, return task ID, poll for results | >10 concurrent users |
| Loading all community posts for analysis | Memory errors, OOM crashes | Paginate queries (LIMIT 100 OFFSET X), stream processing | >10K posts per community |
| Running SpaCy analysis on every scraped post | High CPU usage, slow ingestion | Pre-filter with regex (80% reduction), only analyze top candidates | >1K posts/day scraped |
| Storing full Reddit post HTML in database | Database bloat, slow queries | Store only extracted text + metadata, discard HTML | >50K posts stored |
| No caching on LLM-generated content | Regenerating same content repeatedly, high LLM costs | Cache by post_id + analysis_type, 24-hour TTL | >100 generation requests/day |
| Single Celery worker processing all tasks | Task queue backlog, 10+ minute delays | Scale workers horizontally (3-5 workers), use priority queues | >500 tasks/hour |
| pgvector searches without dimensionality reduction | Slow vector queries (>5s), high memory | Use lower-dimension embeddings (384 vs 1536), quantization | >100K vectors stored |
| No rate limiting on API endpoints | Easy to DDOS yourself during testing, exceeds provider limits | Implement per-user rate limits (10 req/min), global limits (100 req/min) | Public beta launch |

---

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing Reddit OAuth tokens in localStorage | XSS attacks can steal tokens, impersonate users | Use httpOnly cookies, server-side session storage |
| No input sanitization on scraped Reddit content | Prompt injection attacks, XSS if displayed in dashboard | Strip markdown, remove Unicode tricks, validate before LLM/display |
| Exposing Supabase anon key in client-side code | Anyone can query database directly, bypass API logic | Use RLS policies on ALL tables, never trust client |
| Hardcoded Apify/OpenRouter API keys | Keys leaked in git history, unauthorized usage | Use environment variables, rotate keys quarterly |
| No rate limiting on expensive endpoints (/analyze, /generate) | Users can drain LLM budget maliciously | Per-user quotas (10 analyses/day free tier), track costs per user |
| Displaying generated content without attribution | Copyright infringement, Reddit ToS violation | Always attribute to source subreddit, link to original post |
| No webhook signature validation (Stripe, Apify) | Attackers can fake payment success, trigger actions | Validate signatures using provider SDKs before processing |
| Storing PII from Reddit profiles | GDPR violations, data breach liability | Only store public usernames + aggregate stats, no emails/IPs |

---

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing "analyzing..." spinner for 30+ seconds | Users abandon, think app is broken | Show progress bar with stages (scraping → analyzing → generating), ETA |
| Displaying raw NLP confidence scores (0.7234) | Users don't understand what it means | Use visual indicators (High/Medium/Low confidence, color-coded) |
| No explanation for why post was flagged as risky | Users don't trust recommendations, ignore warnings | Show specific reasons (e.g., "Contains profanity: 'damn'", "Too promotional") |
| Shadowban detection results with no context | Users panic or dismiss incorrectly | Explain what shadowban means, confidence level, what to do next |
| Generating content without showing source analysis | Users can't improve prompts, feels like black box | Show archetype breakdown, rhythm score, sensitivity analysis first |
| Error message: "LLM API failed" | User doesn't know if temporary or permanent | "Content generation unavailable (trying again in 2 min)" + retry button |
| No cost visibility for users on paid plans | Bill shock when they exceed quotas | Real-time usage dashboard (X/100 analyses used this month), warnings at 80% |
| Showing stale data without timestamp | Users make decisions on outdated insights | Always show "Last updated X hours ago", offer manual refresh |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Reddit scraping:** Often missing OAuth token refresh logic - verify token expiration handling in logs
- [ ] **Apify integration:** Often missing "Under Maintenance" detection - test actor health check endpoint
- [ ] **LLM generation:** Often missing prompt injection sanitization - test with malicious Reddit post ("Ignore previous...")
- [ ] **Shadowban detection:** Often missing confidence scoring - verify multi-signal validation (not just single API check)
- [ ] **Cost tracking:** Often missing real-time alerts - verify budget threshold triggers email/Slack notifications
- [ ] **Celery tasks:** Often missing worker memory recycling - verify max_tasks_per_child and max_memory_per_child set
- [ ] **Supabase RLS:** Often missing indexes on user_id columns - verify EXPLAIN ANALYZE shows index usage, not seq scans
- [ ] **pgvector search:** Often missing HNSW index creation - verify index exists and query time <500ms
- [ ] **Error handling:** Often missing fallback for Apify actor failures - verify direct Reddit API fallback works
- [ ] **Rate limiting:** Often missing per-user quotas - verify free tier users can't exceed daily limits
- [ ] **Webhook validation:** Often missing signature verification - test with invalid signature (should reject)
- [ ] **Content attribution:** Often missing source links - verify every generated post includes Reddit attribution

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Reddit rate limit IP ban | MEDIUM | Wait 24-48 hours, switch to OAuth-only (no proxies), reduce request concurrency to 1 req/2s |
| Prompt injection attack in production | HIGH | Immediately deploy sanitization filters, audit all generated content from last 7 days, notify affected users |
| LLM cost explosion ($500+ bill) | HIGH | Set hard spending caps on providers, disable auto-scaling, audit top cost-generating users, implement quotas |
| Apify actor deprecated | LOW | Switch to official Reddit API (already built as fallback), update documentation, notify users of improved reliability |
| Celery worker OOM crash | MEDIUM | Restart workers, deploy worker_max_memory_per_child=250000, purge old task results from Redis |
| Supabase RLS slow queries | MEDIUM | Add missing indexes (`CREATE INDEX idx_user_id ON table(user_id)`), rewrite RLS policies with ANY() |
| Shadowban false positive complaints | LOW | Add confidence scores to UI, explain detection limitations, offer manual override option |
| Reddit ToS violation notice | CRITICAL | Immediately disable HTML scraping, switch to API-only, consult legal counsel, prepare compliance report |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Reddit rate limiting | Phase 1: Core Scraping | Load test with 100 subreddits, verify no HTTP 429 errors |
| Prompt injection | Phase 2: NLP + LLM Integration | Penetration test with malicious Reddit posts, verify sanitization blocks |
| Cost explosion | Phase 1: Infrastructure | Deploy with $50 monthly cap, run for 7 days, verify costs <$45 |
| Reddit ToS violation | Phase 1: Core Scraping | Audit all network traffic, verify 100% OAuth API usage (no HTML scraping) |
| Shadowban false positives | Phase 3: Monitoring | Test on 100 known-good posts, verify <5% false positive rate |
| Apify actor failures | Phase 1: Core Scraping | Simulate actor maintenance, verify fallback to direct Reddit API works |
| Celery memory leaks | Phase 2: Task Queue | Run workers for 48 hours under load, verify memory stays <300MB |
| Supabase RLS performance | Phase 2: Database Schema | Load 100K posts, query with RLS, verify <500ms response time |
| Next.js ↔ FastAPI coordination | Phase 1: API Foundation | Deploy auth flow, verify tokens persist across frontend/backend |
| SpaCy accuracy on Reddit content | Phase 2: NLP Pipeline | Test on 1K Reddit posts, verify >75% archetype classification accuracy |
| OAuth token expiration | Phase 1: Reddit Integration | Wait 61 minutes after login, make API call, verify auto-refresh works |
| pgvector slow searches | Phase 3: Content Recommendation | Load 50K vectors, run similarity search, verify <1s query time |

---

## Sources

**Reddit API & Scraping:**
- [How to Scrape Reddit Legally: Complete Guide 2026](https://painonsocial.com/blog/how-to-scrape-reddit-legally)
- [Reddit API Rate Limits Workaround: 7 Proven Strategies](https://painonsocial.com/blog/reddit-api-rate-limits-workaround)
- [What Happens If You Violate Reddit Scraping Rules](https://painonsocial.com/blog/violate-reddit-scraping-rules)
- [Reddit API Rate Limits 2026: Complete Guide](https://painonsocial.com/blog/reddit-api-rate-limits-guide)
- [Reddit OAuth2 Documentation](https://github.com/reddit-archive/reddit/wiki/oauth2)
- [Reddit Launches Legal Action Against AI Data Scrapers](https://www.socialmediatoday.com/news/reddit-launches-legal-action-against-ai-data-scrapers/803572/)

**Shadowban Detection:**
- [Reddit Shadowbans 2025: How They Work](https://reddifier.com/blog/reddit-shadowbans-2025-how-they-work-how-to-detect-them-and-what-to-do-next)
- [Apify Reddit Shadowban Checker](https://apify.com/iskander/reddit-shadowban-checker)

**Apify:**
- [Troubleshooting Actor Under Maintenance](https://help.apify.com/en/articles/10057123-troubleshooting-an-actor-marked-under-maintenance)
- [Apify Review 2026: Real Performance & Pricing Data](https://hackceleration.com/apify-review/)
- [How to Analyze and Fix Errors in Actors](https://help.apify.com/en/articles/3807823-how-to-analyze-and-fix-errors-in-your-actors)
- [Web Scraping Proxies 2026: Higher Demand, Higher Spend](https://blog.apify.com/web-scraping-proxies/)
- [State of Web Scraping Report 2026](https://blog.apify.com/web-scraping-report-2026/)

**LLM Security & Cost:**
- [LLM Security Risks in 2026: Prompt Injection, RAG, and Shadow AI](https://sombrainc.com/blog/llm-security-risks-2026)
- [IEEE 2026: When AI Meets the Web - Prompt Injection Risks](https://arxiv.org/html/2511.05797v1)
- [OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- [LLM Prompt Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
- [OpenRouter API Pricing 2026: Full Breakdown](https://zenmux.ai/blog/openrouter-api-pricing-2026-full-breakdown-of-rates-tiers-and-usage-costs)
- [LLM API Cost Comparison 2026](https://zenvanriel.nl/ai-engineer-blog/llm-api-cost-comparison-2026/)
- [LLM Model Collapse and Quality Degradation](https://levysoft.medium.com/a-reflection-on-the-phenomenon-of-llm-model-collapse-leading-to-the-decline-in-ai-quality-a6993f86866c)

**FastAPI + Celery + Redis:**
- [FastAPI Best Practices for Production: Complete 2026 Guide](https://fastlaunchapi.dev/blog/fastapi-best-practices-production-2026)
- [Celery + Redis + FastAPI: Ultimate 2025 Production Guide](https://medium.com/@dewasheesh.rana/celery-redis-fastapi-the-ultimate-2025-production-guide-broker-vs-backend-explained-5b84ef508fa7)
- [The Complete Guide to Background Processing with FastAPI × Celery/Redis](https://blog.greeden.me/en/2026/01/27/the-complete-guide-to-background-processing-with-fastapi-x-celery-redishow-to-separate-heavy-work-from-your-api-to-keep-services-stable/)
- [Celery 2026: Python Distributed Task Queue Recovery](https://www.programming-helper.com/tech/celery-2026-python-distributed-task-queue-redis-rabbitmq)
- [Celery Memory Leak with Redis Broker](https://github.com/celery/celery/issues/3436)
- [Celery Optimizing Documentation](https://docs.celeryq.dev/en/stable/userguide/optimizing.html)

**Supabase:**
- [Supabase RLS Performance and Best Practices](https://supabase.com/docs/guides/troubleshooting/rls-performance-and-best-practices-Z5Jjwv)
- [Optimizing Vector Search: pgvector & Supabase Performance Tuning](https://medium.com/@dikhyantkrishnadalai/optimizing-vector-search-at-scale-lessons-from-pgvector-supabase-performance-tuning-ce4ada4ba2ed)
- [Supabase Performance and Security Advisors](https://supabase.com/docs/guides/database/database-advisors?lint=0003_auth_rls_initplan)
- [Supabase Connection Management](https://supabase.com/docs/guides/database/connection-management)
- [How to Change Max Database Connections](https://supabase.com/docs/guides/troubleshooting/how-to-change-max-database-connections-_BQ8P5)

**SpaCy:**
- [SpaCy vs NLTK: Which NLP Library for Production](https://edana.ch/en/2026/01/04/spacy-vs-nltk-which-nlp-library-should-you-choose-for-data-and-ai-projects-in-production/)
- [SpaCy Models Documentation](https://spacy.io/models)
- [Comparing Production-Grade NLP Libraries](https://www.oreilly.com/content/comparing-production-grade-nlp-libraries-accuracy-performance-and-scalability/)

**Next.js + FastAPI:**
- [Managing Type Safety Challenges: FastAPI + Next.js](https://www.vintasoftware.com/blog/type-safety-fastapi-nextjs-architecture)
- [Combining Next.js and NextAuth with FastAPI Backend](https://tom.catshoek.dev/posts/nextauth-fastapi/)
- [Integrate FastAPI Framework with Next.js and Deploy 2026](https://codevoweb.com/integrate-fastapi-framework-with-nextjs-and-deploy/)

---
*Pitfalls research for: BC-RAO Social Intelligence Platform*
*Researched: 2026-02-07*
