# Pitfalls Research

**Domain:** Reddit Content Generation / Community Mimicry Tools
**Researched:** 2026-02-07
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Disabled Row Level Security (RLS) on Supabase

**What goes wrong:**
Database is publicly accessible, exposing user data, API keys, private messages, and all application data. This is the #1 cause of security breaches in Supabase applications.

**Why it happens:**
RLS is disabled by default in Supabase. Developers assume database security is enabled automatically, focus on feature development first, and plan to "add security later." The Moltbook incident in January 2026 exposed 1.5M API keys and 35K+ email addresses because of this.

**How to avoid:**
- Enable RLS immediately when creating tables: `ALTER TABLE table_name ENABLE ROW LEVEL SECURITY`
- Create policies BEFORE adding production data
- Never use service_role keys in client code (they bypass RLS)
- Do not rely on user_metadata JWT claims in RLS policies (users can modify these)
- Test RLS policies with different user roles before deployment

**Warning signs:**
- Direct database queries work in development without authentication
- API returns data for users who shouldn't have access
- Security scanners flag publicly accessible database endpoints
- Supabase dashboard shows tables without RLS enabled

**Phase to address:**
Phase 1 (Foundation) - RLS must be enabled before any user-facing features are built. This is non-negotiable.

---

### Pitfall 2: AI Content Detection Leading to Shadowbans

**What goes wrong:**
Reddit's sophisticated bot detection systems identify AI-generated content, leading to shadowbans where posts appear normal to the user but are invisible to everyone else. Moderators can detect AI content through time-consuming but effective heuristics looking for "tells" in content and behavior.

**Why it happens:**
LLM-generated content contains detectable patterns at the token level (statistical distribution of word choices, sentence structures, transitional patterns). Common mistakes include:
- Using AI for entire content pieces without adjustments
- Repetitive structures and lack of human-like phrasing
- Context errors and repetitive phrases
- Default "essay voice" that LLMs produce
- Chaining models or double-pass humanization (re-introduces AI fingerprints)

**How to avoid:**
- Never use raw LLM output without significant human editing
- Adopt varied sentence rhythm, informal structures, and distinctive voice
- Use creative, essayist-style approaches (84% bypass rate vs. 7% for standard fine-tuning)
- Avoid humanization tools (most don't deliver on promises)
- Build genuine engagement history before promotional posting
- Mix AI-assisted content with fully human-written responses
- Test content with AI detectors (GPTZero, ZeroGPT) before posting

**Warning signs:**
- Posts receive no engagement despite appearing "posted"
- Comments invisible when checked in incognito mode
- No upvotes/downvotes on recent posts
- Account profile shows "page not found" when logged out
- Reddit Shadowban Checker flags account

**Phase to address:**
Phase 2 (Content Generation) - Must implement detection avoidance strategies before any automated posting. Phase 4 (Safety & Quality) - Continuous monitoring and adjustment of generation patterns.

---

### Pitfall 3: Reddit API/TOS Violations Through Automated Posting

**What goes wrong:**
Account suspension, IP bans, legal action from Reddit. Reddit prohibits scraping without consent and has actively pursued legal action (see Reddit vs. Perplexity case). Automated posting that violates spam rules leads to permanent bans.

**Why it happens:**
Developers misunderstand what constitutes acceptable automation. Reddit's rules explicitly prohibit:
- Posting identical or substantially similar content across subreddits
- Automated posts, comments, or DMs that constitute spam
- Accessing/searching/collecting data by automated means without permission
- Creating new accounts to evade bans (leads to IP bans)

**How to avoid:**
- Use official Reddit API with proper OAuth authentication
- Respect rate limits: 60 requests/minute with 10-minute rolling window
- Unique content per subreddit (no copy-paste across communities)
- Follow the unofficial 10% self-promotion rule (90% non-promotional activity)
- Build organic karma and account age before promotional posts
- Never use service_role/admin keys in automation
- Implement proper error handling for rate limit responses
- Add human review before posting

**Warning signs:**
- Receiving 403 Forbidden errors from Reddit API
- Account temporarily suspended for "suspicious activity"
- Posts auto-removed immediately after posting
- Negative karma accumulation
- DMs from moderators warning about spam

**Phase to address:**
Phase 1 (Foundation) - Must establish compliant API usage patterns. Phase 3 (Attack Cards & Posting) - Implement strict posting rules and human review workflows.

---

### Pitfall 4: Unreliable Shadowban Detection

**What goes wrong:**
Unable to distinguish between shadowbans, permanent suspensions, and deleted accounts. All three look identical to outside observers, leading to false positives and inability to detect actual shadowbans until significant damage is done.

**Why it happens:**
Detection tools flag all three states as "shadowbanned." Reddit doesn't notify users of shadowbans. Community-level shadowbans (subreddit-specific) are even harder to detect than site-wide bans.

**How to avoid:**
- Implement multi-method detection:
  - Check profile accessibility when logged out (www.reddit.com/user/USERNAME)
  - Monitor engagement metrics (no votes/comments = possible shadowban)
  - Use Reddit Shadowban Checker tool
  - Check if posts appear in subreddit when logged out
- Set up automated alerts for zero-engagement posts
- Test new accounts in low-stakes subreddits first
- Maintain backup accounts for verification
- Track historical engagement rates to detect sudden drops

**Warning signs:**
- Posts receive zero engagement for 24+ hours
- Profile returns "page not found" when logged out
- Comments not visible in thread when checked anonymously
- Sudden drop in historical engagement rate
- Moderator actions showing "removed" despite not violating rules

**Phase to address:**
Phase 4 (Safety & Quality) - Must build reliable detection before scaling. Phase 5 (Monitoring) - Continuous monitoring of account health.

---

### Pitfall 5: Data Staleness in Community Profiles

**What goes wrong:**
NLP analysis based on outdated Reddit data produces content that doesn't match current community tone, leading to detection as "off" or inauthentic. Reddit content changes rapidly; linguistic patterns, memes, trending topics, and moderation policies shift weekly or daily.

**Why it happens:**
- One-time scraping during onboarding
- No refresh mechanism for community profiles
- Rate limit concerns preventing frequent re-scraping
- Assuming community culture is static
- Not tracking when data was last collected

**How to avoid:**
- Implement profile freshness tracking (timestamp on all scraped data)
- Re-scrape high-priority subreddits weekly
- Flag stale profiles (>30 days old) with warnings
- Prioritize recent posts (last 7-30 days) in analysis
- Monitor subreddit rule changes through API
- Detect community "mood shifts" through sentiment analysis
- Allow manual profile refresh before posting
- Set alerts for significant community changes (new moderators, rule updates)

**Warning signs:**
- Generated content uses outdated memes or references
- Tone mismatches current community sentiment
- Violates recently added rules
- Community calls out content as "not understanding the vibe"
- Engagement rates drop on previously successful subreddits

**Phase to address:**
Phase 2 (NLP Analysis) - Build freshness tracking from the start. Phase 5 (Monitoring) - Automated staleness detection and refresh triggers.

---

### Pitfall 6: Celery Worker Failures During Railway Deployments

**What goes wrong:**
Long-running scraping tasks (1-5 minutes) are interrupted during deployments, causing incomplete data collection, corrupted community profiles, and lost API quota. Tasks stuck in PENDING state, never completing.

**Why it happens:**
- Railway deploys new containers without waiting for tasks to complete
- Workers killed mid-task lose all progress
- No graceful shutdown mechanism
- Task retry logic not accounting for partial completion
- Redis task queue not persisting across deployments

**How to avoid:**
- Configure Railway environment variables:
  - `RAILWAY_DEPLOYMENT_OVERLAP_SECONDS` - allows new deployment to run alongside old
  - `RAILWAY_DEPLOYMENT_DRAINING_SECONDS` - time for old workers to finish tasks
- Implement idempotent tasks (safe to retry)
- Use task checkpointing for long-running scrapes
- Store partial results to avoid complete data loss
- Monitor task states (detect stuck PENDING tasks)
- Verify Celery workers connected to correct broker
- Use separate Redis instance for task queue (not ephemeral)
- Implement task timeout and retry logic

**Warning signs:**
- Tasks showing PENDING indefinitely after deployment
- Community profiles partially populated
- Redis connection errors in logs
- Increased task failure rate during deployment windows
- Workers not registering with broker after deploy

**Phase to address:**
Phase 1 (Foundation) - Configure graceful shutdown before first scraping implementation. Phase 6 (Infrastructure) - Monitor and optimize worker reliability.

---

### Pitfall 7: LLM Cost Explosion from Inefficient Prompts

**What goes wrong:**
Monthly LLM costs exceed revenue, making the business unsustainable. Programming workloads routinely exceed 20K input tokens; without optimization, costs scale linearly with usage while revenue is capped by subscription plans.

**Why it happens:**
- Including entire community profiles in every prompt
- No prompt compression or caching
- Using expensive models for simple tasks
- Not leveraging OpenRouter's cost-based routing
- Repeated prompts without caching (charged at 100% instead of 25%)

**How to avoid:**
- Implement prompt caching (0.25x cost for repeated prompts)
- Use prompt compression (LLMLingua: 20x compression while preserving semantics)
- Set max price limits in OpenRouter: `{"prompt": 1, "completion": 2}`
- Route simple tasks to cheaper models
- Use semantic summarization to condense community profiles
- Implement relevance filtering (only include truly relevant context)
- Monitor token usage per request
- Set per-user monthly token budgets aligned with plan limits
- Cache common community profile summaries

**Warning signs:**
- OpenRouter bills exceeding 50% of revenue
- Average prompt tokens >10K
- Using same model for all tasks
- No caching hit rate metrics
- Customer complaints about slow generation (inefficient prompts)

**Phase to address:**
Phase 2 (Content Generation) - Build cost controls from day one. Phase 7 (Optimization) - Continuous cost monitoring and optimization.

---

### Pitfall 8: Reddit Rate Limit Violations Leading to API Bans

**What goes wrong:**
Temporary or permanent API access suspension. Reddit's official API has strict rate limits (60 requests/minute, 10-minute rolling window). In 2026, Reddit's advanced bot detection systems flag unusual patterns regardless of proper OAuth authentication.

**Why it happens:**
- Burst scraping patterns (collecting hundreds of posts at once)
- Not implementing exponential backoff on errors
- Multiple users triggering simultaneous scrapes
- Mismatched browser configurations (timezone inconsistencies)
- Using same credentials across multiple IPs

**How to avoid:**
- Implement rate limiting client-side (stay under 60/min)
- Use exponential backoff on 429 errors
- Distribute scraping over time (batch processing)
- Queue scraping requests through Celery
- Monitor rate limit headers in responses
- Use proxy rotation for larger scraping needs (but risks TOS violation)
- Consider Apify Reddit Scraper (claims no API rate limits, uses alternative methods)
- Implement request throttling per user
- Cache frequently accessed data

**Warning signs:**
- Receiving 429 (Too Many Requests) responses
- 403 Forbidden errors on valid requests
- Temporary suspensions for "suspicious activity"
- API responses slower than normal
- Missing rate limit headers in responses

**Phase to address:**
Phase 1 (Foundation) - Rate limiting infrastructure must be in place before any scraping. Phase 5 (Monitoring) - Track rate limit usage and adjust dynamically.

---

### Pitfall 9: Blacklist Ineffectiveness Due to Incomplete Coverage

**What goes wrong:**
Users bypass content safety filters, resulting in posts that violate Reddit rules, get accounts banned, or damage brand reputation. Blacklist approach (blocking specific topics) fails because language is too flexible and context-dependent.

**Why it happens:**
- Relying solely on keyword matching
- Not accounting for euphemisms, coded language, or context
- Blacklist maintenance falling behind new slang
- No semantic understanding of content intent
- Users finding creative workarounds

**How to avoid:**
- Use LLM-based content moderation (semantic understanding, not just keywords)
- Implement multi-layer safety:
  1. Keyword blacklist (fast, catches obvious violations)
  2. LLM content review (catches nuanced violations)
  3. Human review for edge cases (final verification)
- Monitor Reddit's updated content policies
- Track banned account patterns to identify filter gaps
- Allow users to appeal/regenerate flagged content
- Log all filtered content for blacklist improvement
- Test filters with adversarial examples

**Warning signs:**
- Users reporting that "safe" content was posted and got banned
- Moderators removing BC-RAO generated content
- Blacklist bypassed through misspellings or code words
- Negative feedback about "the tool got me banned"

**Phase to address:**
Phase 4 (Safety & Quality) - Multi-layer safety before any production posting. Phase 5 (Monitoring) - Continuous blacklist improvement from user feedback.

---

### Pitfall 10: Karma/Account Age Filtering Preventing New User Success

**What goes wrong:**
New users cannot post in target subreddits because their fresh accounts are auto-filtered. Communities typically require 50-500 karma and 30+ day old accounts. Users frustrated by "it doesn't work" when the tool generates content but posts are auto-removed.

**Why it happens:**
- Tool promises "promote on Reddit" but doesn't communicate prerequisites
- No guidance on building account credibility first
- Users expect immediate results
- Reddit's aggressive spam filter targets new accounts
- Each subreddit has different thresholds (30, 90, even 180 days)

**How to avoid:**
- Account readiness checker in onboarding:
  - Check karma levels
  - Check account age
  - Flag subreddits likely to auto-filter
- Provide account warming guide:
  - Comment karma safer than post karma
  - Engage in casual subreddits first
  - Build 100-300 karma before promotional posting
- Suggest aged account marketplace (with warnings about TOS)
- Set expectations: "Build credibility first, promote second"
- Recommend starting with permissive subreddits
- Show estimated readiness per subreddit

**Warning signs:**
- High percentage of posts auto-removed
- Users churning within first week
- Support tickets about "posts not appearing"
- Negative reviews: "doesn't work, posts get removed"

**Phase to address:**
Phase 3 (Attack Cards & Posting) - Build account readiness checks before posting features. Phase 8 (User Experience) - Onboarding flow emphasizing account preparation.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Disabling RLS during development | Faster iteration, simpler queries | Data breach, complete rebuild of security layer | Never - enable from day 1 |
| Using single LLM model for all tasks | Simple implementation | 3-5x higher costs, slow generation | MVP only, must optimize by Phase 2 |
| One-time community scraping | Lower API usage, faster onboarding | Stale profiles, poor mimicry accuracy | Never - data freshness is core value prop |
| Skipping shadowban detection | Faster MVP launch | Users posting to void, high churn | Never - silent failures destroy trust |
| Manual content review instead of automated filtering | Perfect accuracy initially | Doesn't scale, becomes bottleneck | Acceptable for first 50 users in beta |
| Storing community profiles in app memory | Fast access, simple code | Lost on restart, no sharing across workers | Early prototype only |
| Using free-tier Apify for scraping | No cost | Rate limits, unreliable data | Acceptable for testing, not production |
| Hardcoded prompt templates | Quick iteration | Can't improve without deployment | Early phases, but parameterize by Phase 3 |

---

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Reddit API | Using scraping without authentication | Use OAuth, respect TOS, handle rate limits gracefully |
| Apify Reddit Scraper | Assuming real-time data | Understand data is fetched on-demand, may be minutes old |
| OpenRouter | Not setting max price limits | Configure price caps per model category to prevent cost spikes |
| Supabase Auth | Trusting user_metadata in RLS policies | Use only auth.uid() and verified claims in policies |
| Stripe Webhooks | Not verifying webhook signatures | Always verify signature before processing events |
| Celery + Redis | Using ephemeral Redis instance | Use persistent Redis for task queue, separate from cache |
| SpaCy NLP | Loading full model on every request | Load models at startup, reuse across requests |
| Railway Deployments | Not configuring overlap/draining | Set RAILWAY_DEPLOYMENT_OVERLAP_SECONDS and DRAINING_SECONDS |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Synchronous scraping in API handler | Request timeouts, 504 errors | Use Celery for all scraping, return task ID immediately | >10 concurrent users |
| Loading entire community profile into LLM prompt | Slow generation, high costs | Use summarization and relevance filtering | Profiles >5K tokens |
| Storing all user data in session | Memory leaks, slow login | Use proper database queries, cache judiciously | >100 active sessions |
| Re-scraping subreddit on every generation | Rate limit errors, slow UX | Cache profiles, refresh only when stale (>7 days) | >50 generations/day |
| Not using database indexes | Slow queries on user posts, profiles | Index foreign keys, frequently queried columns | >1000 users |
| Single Celery worker | Queue backlog, failed tasks | Scale workers horizontally based on queue length | >100 tasks/hour |
| Embedding full SpaCy model in each function | High memory, slow cold starts | Singleton pattern, load once at startup | First production deployment |
| No connection pooling for Supabase | Connection exhaustion, failed requests | Use connection pooling, limit max connections | >50 concurrent requests |

---

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing Reddit OAuth tokens in localStorage | XSS attacks can steal tokens, impersonate users | Use httpOnly cookies or secure backend storage |
| Exposing service_role key to frontend | Complete database access, RLS bypass, data breach | Never send to client, use anon key only |
| Not rate limiting content generation | API abuse, cost explosion, account bans | Enforce plan limits server-side, track usage in DB |
| Allowing arbitrary subreddit scraping | Users could scrape private/NSFW content, TOS violation | Whitelist approved subreddits or category restrictions |
| Not sanitizing generated content before posting | XSS, injection attacks through Reddit | Escape HTML entities, validate output format |
| Storing OpenRouter API keys in environment variables only | Key exposure in logs, error messages | Use secrets manager, rotate regularly |
| Trusting user-provided subreddit names | SQL injection through subreddit parameter | Validate against Reddit's allowed characters, parameterize queries |
| No audit trail for generated posts | Can't debug bans, no accountability | Log all generated content with timestamps, user IDs |

---

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Not explaining why content was filtered | Frustration, feels arbitrary | Show specific reason (blacklist match, policy violation) |
| Generating content without showing confidence score | Users post low-quality mimicry, get downvoted | Show CSI (Community Sensitivity Index), warn if <70% |
| Not warning about account requirements | Posts auto-removed, users blame tool | Pre-flight check: show karma, age, subreddit requirements |
| Auto-posting without preview | Users can't verify before it's public | Always show preview, require explicit confirmation |
| Hiding that content is AI-assisted | Violates Reddit transparency norms | Include subtle disclaimer or be prepared to acknowledge if asked |
| Generating same content for multiple subreddits | Obvious spam, bans across communities | Enforce unique content per subreddit, warn against cross-posting |
| No explanation of Attack Card selection | Users don't understand why certain approaches chosen | Show brief rationale for each recommended Attack Card |
| Long scraping with no progress indicator | Users think app is broken | Show "Analyzing 50 posts from r/subreddit... 45% complete" |
| Not explaining shadowban detection results | Confusion about account status | Clear explanation: "Likely shadowbanned - posts invisible to others" |
| Allowing unlimited regeneration | Users spam regenerate, blow through quota | Limit regenerations per post (3-5), explain why |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Content Generation:** Often missing diversity check - verify consecutive posts don't use same sentence structures/vocabulary
- [ ] **Shadowban Detection:** Often missing subreddit-level detection - verify both site-wide AND per-subreddit shadowban checks
- [ ] **RLS Policies:** Often missing UPDATE/DELETE policies - verify all CRUD operations have policies, not just SELECT
- [ ] **Rate Limiting:** Often missing Redis fallback - verify graceful degradation when Redis unavailable
- [ ] **Community Profiling:** Often missing moderator analysis - verify capturing moderation style, not just user content
- [ ] **Stripe Integration:** Often missing failed payment handling - verify retry logic and grace periods implemented
- [ ] **Attack Card Generation:** Often missing context freshness - verify using recent community events, not just historical data
- [ ] **Cost Tracking:** Often missing refund handling - verify credit system accounts for Stripe refunds/chargebacks
- [ ] **Celery Tasks:** Often missing timeout configuration - verify tasks have max runtime to prevent zombie workers
- [ ] **API Error Handling:** Often missing Reddit-specific errors - verify handling "subreddit private", "user banned", etc.

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| RLS disabled, data exposed | HIGH | 1. Enable RLS immediately, 2. Rotate all API keys, 3. Notify affected users, 4. Audit access logs, 5. Implement monitoring |
| Shadowbanned accounts | MEDIUM | 1. Stop posting immediately, 2. Create fresh accounts, 3. Build karma organically, 4. Adjust generation patterns, 5. Test in safe subreddits |
| API ban from Reddit | HIGH | 1. Contact Reddit API support, 2. Demonstrate TOS compliance changes, 3. Use backup credentials (if available), 4. Pivot to approved scraping methods |
| Cost explosion from LLM usage | MEDIUM | 1. Implement emergency rate limiting, 2. Enable prompt caching immediately, 3. Switch to cheaper models, 4. Audit high-cost users |
| Stale community profiles | LOW | 1. Flag affected profiles, 2. Priority re-scrape, 3. Notify users generation may be off, 4. Implement freshness monitoring |
| Worker failures losing tasks | LOW | 1. Implement task checkpointing, 2. Manual re-queue of failed tasks, 3. Add monitoring alerts, 4. Configure graceful shutdown |
| Blacklist bypass causing bans | MEDIUM | 1. Apologize to affected users, 2. Update filters immediately, 3. Review all recent generated content, 4. Offer account recovery guidance |
| Account age filtering blocking posts | LOW | 1. Add account readiness checker, 2. Update onboarding with requirements, 3. Recommend account warming strategy |
| Stripe plan limit not enforced | LOW | 1. Backfill usage tracking, 2. Implement hard limits, 3. Grandfather existing users or upgrade them, 4. Add quota monitoring |
| Detection as AI content | MEDIUM | 1. Analyze detection patterns, 2. Adjust generation style, 3. Add more human editing steps, 4. Reduce automation percentage |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Disabled RLS | Phase 1: Foundation | All tables show RLS enabled in Supabase dashboard |
| AI Content Detection | Phase 2: Content Generation | Generated content passes GPTZero with <30% AI score |
| Reddit API/TOS Violations | Phase 1: Foundation | OAuth flow complete, rate limiting verified |
| Unreliable Shadowban Detection | Phase 4: Safety & Quality | Detection tested on known shadowbanned accounts |
| Data Staleness | Phase 2: NLP Analysis | Freshness timestamps on all profiles, alerts for >30 day old data |
| Celery Worker Failures | Phase 1: Foundation | Deployments complete without task failures |
| LLM Cost Explosion | Phase 2: Content Generation | Cost per generation <$0.10, caching enabled |
| Rate Limit Violations | Phase 1: Foundation | Monitor shows 0 rate limit errors over 7 days |
| Blacklist Ineffectiveness | Phase 4: Safety & Quality | Manual testing with adversarial examples shows 95%+ catch rate |
| Karma/Age Filtering | Phase 3: Attack Cards & Posting | Account readiness checker shows accurate requirements |

---

## Sources

**Reddit API & Rate Limits:**
- [Reddit API Rate Limits 2026 Guide](https://painonsocial.com/blog/reddit-api-rate-limits-guide)
- [Reddit API Rate Limits Workaround Strategies](https://painonsocial.com/blog/reddit-api-rate-limits-workaround)
- [Reddit API Limits and Posting Restrictions](https://postiz.com/blog/reddit-api-limits-rules-and-posting-restrictions-explained)
- [What Happens If You Violate Reddit Scraping Rules](https://painonsocial.com/blog/violate-reddit-scraping-rules)

**Shadowban Detection:**
- [Reddit Shadowbans 2025: How They Work](https://reddifier.com/blog/reddit-shadowbans-2025-how-they-work-how-to-detect-them-and-what-to-do-next)
- [Reddit Shadowban Checker Tool](https://apify.com/iskander/reddit-shadowban-checker)

**AI Content Detection:**
- [AI Moderation Crisis Reddit Users Don't See](https://medium.com/@truthbit.ai/the-ai-moderation-crisis-reddits-110-million-users-don-t-see-2a92a8080372)
- [Moderating AI-Generated Content on Reddit](https://arxiv.org/html/2311.12702v7)
- [AI Content Triple Threat for Reddit Moderators](https://news.cornell.edu/stories/2025/10/ai-generated-content-triple-threat-reddit-moderators)
- [AI Rules: Reddit Community Policies Towards AI-Generated Content](https://arxiv.org/html/2410.11698v2)

**AI Humanization Failures:**
- [AI Detection vs AI Humanization Arms Race](https://todaynews.co.uk/2026/02/03/ai-detection-vs-ai-humanization-the-arms-race-reshaping-content-creation/)
- [I Tried 50+ AI Humanizers - Best 10 Tools](https://medium.com/@edgaramanalo/i-tried-50-ai-humanizers-here-are-the-best-10-tools-to-bypass-ai-detectors-in-2026-2ed44411ce39)
- [Best AI Detection Removers 2026](https://gowinston.ai/best-ai-detection-removers/)

**Reddit TOS & Spam:**
- [Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy)
- [How to Avoid Reddit Spam Rules 2026](https://painonsocial.com/blog/how-to-avoid-reddit-spam-rules)
- [How to Promote SaaS on Reddit Without Getting Banned](https://www.replyagent.ai/blog/how-promote-saas-reddit-without-getting-banned)

**Supabase RLS Security:**
- [Supabase Security Flaw: 170+ Apps Exposed](https://byteiota.com/supabase-security-flaw-170-apps-exposed-by-missing-rls/)
- [Moltbook Data Breach: Supabase RLS Lessons](https://bastion.tech/blog/moltbook-security-lessons-ai-agents)
- [Fixing RLS Misconfigurations in Supabase](https://prosperasoft.com/blog/database/supabase/supabase-rls-issues/)
- [Supabase Row Level Security Complete Guide 2026](https://vibeappscanner.com/supabase-row-level-security)

**Celery + FastAPI:**
- [Graceful Shutdown of Celery Workers on Railway](https://station.railway.com/questions/graceful-shutdown-of-celery-workers-duri-7445b567)
- [Complete Guide to FastAPI × Celery Background Processing](https://blog.greeden.me/en/2026/01/27/the-complete-guide-to-background-processing-with-fastapi-x-celery-redishow-to-separate-heavy-work-from-your-api-to-keep-services-stable/)
- [Asynchronous Tasks with FastAPI and Celery](https://testdriven.io/blog/fastapi-and-celery/)

**LLM Cost Optimization:**
- [Prompt Compression for LLM Cost Reduction](https://machinelearningmastery.com/prompt-compression-for-llm-generation-optimization-and-cost-reduction/)
- [LLM Cost Optimization: Reduce AI Expenses by 80%](https://ai.koombea.com/blog/llm-cost-optimization)
- [4 Techniques to Optimize LLM Prompts](https://towardsdatascience.com/4-techniques-to-optimize-your-llm-prompts-for-cost-latency-and-performance/)

**OpenRouter:**
- [Provider Routing - Smart Multi-Provider Management](https://openrouter.ai/docs/guides/routing/provider-selection)
- [Prompt Caching - Reduce Costs](https://openrouter.ai/docs/guides/best-practices/prompt-caching)
- [State of AI 2025: 100T Token LLM Usage Study](https://openrouter.ai/state-of-ai)

**Apify Reddit Scraper:**
- [Reddit Scraper Tools](https://apify.com/harshmaur/reddit-scraper)
- [Top 10 Reddit Scraper Tools 2026](https://www.browseract.com/blog/top-10-reddit-scraper-tools-for-data-extraction-in-2025)

**Reddit Account Requirements:**
- [Guide to Reddit Karma Requirements](https://postiz.com/blog/reddit-karma-requirements)
- [How Reddit Algorithms Treat Aged vs New Accounts](https://redkarmas.com/aged-vs-new-reddit-accounts/)
- [How to Warm Up a Reddit Account Safely 2025](https://dicloak.com/blog-detail/how-to-warm-up-a-reddit-account-safely-complete-guide-for-2025)

**NLP & Text Style Transfer:**
- [Deep Learning for Text Style Transfer Survey](https://arxiv.org/abs/2011.00416)
- [Discovering and Categorising Language Biases in Reddit](https://arxiv.org/abs/2008.02754)

---

*Pitfalls research for: Reddit Content Generation / Community Mimicry Tools*
*Researched: 2026-02-07*
