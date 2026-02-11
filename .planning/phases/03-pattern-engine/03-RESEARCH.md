# Phase 3: Pattern Engine - Research

**Researched:** 2026-02-10
**Domain:** NLP text analysis with SpaCy, community intelligence scoring, data visualization
**Confidence:** HIGH

## Summary

This phase implements local NLP analysis using SpaCy to analyze Reddit posts, calculate ISC (community sensitivity) scores, build community profiles, and visualize patterns through a React dashboard. The system performs zero-cost local processing (no external API calls) using SpaCy for linguistic analysis, custom scoring algorithms for vulnerability/rhythm/penalties, and visualization components for charts and inline text highlighting.

The standard approach uses SpaCy 3.8+ with custom pipeline components for domain-specific metrics (formality, tone, sentence rhythm), textstat 0.7.12 for readability scoring, and vaderSentiment for sentiment analysis. The backend runs analysis as Celery tasks with SSE progress tracking using sse-starlette. The frontend uses Recharts for visualizations (pie/donut charts, gauges), shadcn/ui for tables and tabs, and react-highlight-words for inline penalty highlighting.

Key considerations: SpaCy memory management for batch processing, JSONB indexing for community profiles, proper GIN indexes for pattern queries, and Celery task design to avoid memory leaks in long-running NLP operations.

**Primary recommendation:** Use SpaCy with custom @Language.component decorators for domain metrics, batch process with nlp.pipe() for efficiency, reload models periodically to clear vocab growth, and use GIN indexes on JSONB columns for fast pattern queries.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Community Profile Display:**
- ISC score shown as number + tier label with color coding (e.g., "7.8 — High Sensitivity") with color gauge
- Archetype distribution (Journey/ProblemSolution/Feedback) shown as pie/donut chart
- Profile page uses tabbed sections: Summary tab with key metrics, then tabs for Archetypes, Rhythm, Blacklist, etc.
- Comparison table across all target subreddits as the entry point, click into individual subreddit profiles for detail

**Post Scoring Breakdown:**
- Show 3-4 key contributing factors per post (rhythm match, vulnerability, formality, penalties) — not full sub-detail breakdown
- Penalties highlighted inline in post text (problematic phrases highlighted in red/orange, like a linter)
- Dedicated "Analysis" page for viewing posts with scores and expandable breakdowns — separate from Phase 2's post browsing
- Sorting/filtering by scoring factors: Claude's discretion on appropriate filtering based on data complexity

**Analysis Trigger & Feedback:**
- Analysis runs automatically after collection completes — seamless pipeline, no manual trigger needed
- SSE-style progress tracking during analysis: "Analyzing post 47/230…" with rhythm analysis and scoring steps visible
- If insufficient data for a subreddit: block profile creation, show "Need more data" and suggest re-collecting with wider criteria
- After analysis completes: toast notification "Analysis complete" with link to profiles — user decides when to navigate

**Forbidden Patterns Surface:**
- Show pattern categories only (Promotional, Self-referential, Link patterns, etc.) with counts per category — not raw pattern strings
- Users can add custom forbidden patterns (e.g., competitor names) but cannot remove system-detected ones
- Separate dedicated blacklist page showing all forbidden patterns across all subreddits, filterable by subreddit
- No provenance tracking in display — just categories and counts, keep it simple

### Claude's Discretion

- SpaCy pipeline configuration and NLP analysis details
- ISC scoring algorithm and weight tuning
- Exact threshold for "insufficient data" blocking profile creation
- Community profile tab structure and content organization
- Scoring filter/sort implementation approach
- Rhythm pattern visualization within profile tabs

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| spaCy | 3.8+ | Local NLP pipeline for linguistic analysis | Industry standard for production NLP, zero external API cost, supports custom components |
| textstat | 0.7.12 | Readability and formality metrics | Established library for Flesch-Kincaid, Gunning FOG, Coleman-Liau scoring |
| vaderSentiment | 3.3.2+ | Sentiment/tone analysis | Rule-based, optimized for social media text like Reddit posts |
| sse-starlette | 2.1+ | Server-Sent Events for FastAPI | Official SSE implementation for Starlette/FastAPI, async native |
| Recharts | 2.x | React charts (pie/donut/gauge) | Declarative React components, D3-powered, 48k+ GitHub stars |
| react-highlight-words | 0.21.0 | Inline text highlighting | Lightweight, supports multi-color highlights, actively maintained (Jan 2025) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| en_core_web_md | 3.8.0 | SpaCy medium English model | Balance between accuracy and speed; use for 48MB footprint with better word vectors than sm |
| Celery | 5.6+ | Background task execution | Already in stack for collection; use for analysis tasks with proper memory management |
| shadcn/ui Tabs | Latest | Tabbed profile sections | User requirement for tabbed community profile structure |
| shadcn/ui Table | Latest | Comparison table & data display | User requirement for subreddit comparison entry point |
| TanStack Table | 8.x | Advanced table sorting/filtering | When implementing scoring factor filters (Claude's discretion) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SpaCy custom components | NLTK-based custom pipeline | NLTK slower, less production-ready; SpaCy has better batching and memory management |
| textstat | Hand-rolled formality scoring | Textstat handles 10+ established metrics (Flesch, SMOG, etc.); reinventing loses research validation |
| Recharts | Nivo, Victory, Visx | Recharts more declarative/React-native; others require more D3 knowledge or have steeper learning curves |
| react-highlight-words | react-text-annotate | react-text-annotate unmaintained (6 years old); react-highlight-words actively updated (Jan 2025) |

**Installation:**
```bash
# Backend (Python)
pip install spacy==3.8.0 textstat==0.7.12 vaderSentiment==3.3.2 sse-starlette==2.1.0
python -m spacy download en_core_web_md

# Frontend (Next.js)
npm install recharts react-highlight-words
```

## Architecture Patterns

### Recommended Backend Structure
```
api/
├── analysis/
│   ├── nlp_pipeline.py      # SpaCy custom components (@Language.component)
│   ├── scorers.py           # ISC scoring, vulnerability, rhythm calculators
│   ├── pattern_extractor.py # Forbidden pattern detection
│   └── tasks.py             # Celery task with SSE progress
├── routes/
│   └── analysis.py          # POST /campaigns/:id/analyze, GET endpoints
└── models/
    └── community_profile.py # SQLAlchemy model for community_profiles table
```

### Recommended Frontend Structure
```
app/
├── campaigns/[id]/
│   ├── analysis/            # Analysis page (separate from Phase 2 browsing)
│   │   ├── page.tsx
│   │   └── components/
│   │       ├── PostScoreBreakdown.tsx
│   │       └── PenaltyHighlighter.tsx  # Uses react-highlight-words
│   └── profiles/            # Community profiles
│       ├── page.tsx         # Comparison table entry point
│       └── [subreddit]/
│           └── page.tsx     # Tabbed profile detail
└── components/
    ├── charts/
    │   ├── ISCGauge.tsx     # Recharts-based color gauge
    │   ├── ArchetypePie.tsx # Pie/donut chart
    │   └── ComparisonTable.tsx
    └── sse/
        └── AnalysisProgress.tsx  # SSE client for progress tracking
```

### Pattern 1: SpaCy Custom Component for Domain Metrics
**What:** Register custom pipeline components with @Language.component decorator to calculate domain-specific metrics (formality, rhythm, vulnerability)
**When to use:** When SpaCy's built-in features (POS, dependency, NER) need augmentation with custom scoring
**Example:**
```python
# Source: https://spacy.io/usage/processing-pipelines
from spacy.language import Language
from textstat import flesch_kincaid_grade, gunning_fog

@Language.component("formality_scorer")
def add_formality_score(doc):
    """Calculate formality using readability metrics"""
    text = doc.text
    fk_grade = flesch_kincaid_grade(text)
    fog_index = gunning_fog(text)

    # Average readability scores as formality proxy
    doc._.formality_score = (fk_grade + fog_index) / 2
    return doc

# Register extension attribute
from spacy.tokens import Doc
Doc.set_extension("formality_score", default=None, force=True)

# Add to pipeline
nlp = spacy.load("en_core_web_md")
nlp.add_pipe("formality_scorer", last=True)

# Use with batching
docs = list(nlp.pipe(texts, batch_size=100))
for doc in docs:
    print(doc._.formality_score)
```

### Pattern 2: Celery Task with SSE Progress Tracking
**What:** Long-running analysis task that yields progress events via SSE while processing posts in batches
**When to use:** For the automatic analysis pipeline after collection completes (user requirement)
**Example:**
```python
# Source: https://medium.com/@nandagopal05/server-sent-events-with-python-fastapi-f1960e0c8e4b
from celery import shared_task
from sse_starlette.sse import EventSourceResponse
import asyncio

@shared_task(bind=True)
def analyze_campaign_posts(self, campaign_id: str):
    """Analyze posts with progress tracking"""
    posts = fetch_posts(campaign_id)
    total = len(posts)

    nlp = load_nlp_pipeline()

    for idx, batch in enumerate(batch_posts(posts, size=50)):
        # Process batch
        texts = [p.body for p in batch]
        docs = list(nlp.pipe(texts, batch_size=50))

        # Calculate scores
        for post, doc in zip(batch, docs):
            post.rhythm_metadata = calculate_rhythm(doc)
            post.vulnerability_score = calculate_vulnerability(doc)

        # Update progress (Celery state)
        progress = (idx + 1) * 50
        self.update_state(
            state='PROGRESS',
            meta={'current': min(progress, total), 'total': total, 'status': f'Analyzing post {progress}/{total}'}
        )

    # Build community profiles
    build_community_profiles(campaign_id)
    return {'status': 'complete'}

# SSE endpoint
@router.get("/campaigns/{campaign_id}/analysis/progress")
async def analysis_progress(campaign_id: str, task_id: str):
    async def event_generator():
        while True:
            task = AsyncResult(task_id)
            if task.state == 'PROGRESS':
                yield {
                    "event": "progress",
                    "data": json.dumps(task.info)
                }
            elif task.state == 'SUCCESS':
                yield {
                    "event": "complete",
                    "data": json.dumps({"status": "complete"})
                }
                break
            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())
```

### Pattern 3: JSONB GIN Indexing for Pattern Queries
**What:** Create GIN indexes on JSONB columns for fast containment and key existence queries
**When to use:** For community_profiles.forbidden_patterns, archetype_distribution, and rhythm_pattern queries
**Example:**
```sql
-- Source: https://www.crunchydata.com/blog/indexing-jsonb-in-postgres
-- GIN index for forbidden_patterns containment queries
CREATE INDEX idx_community_forbidden_patterns
ON community_profiles USING GIN (forbidden_patterns);

-- Expression index for specific pattern category counts
CREATE INDEX idx_community_promotional_count
ON community_profiles ((forbidden_patterns->'Promotional'));

-- Query optimization
-- Fast: Uses GIN index
SELECT subreddit, forbidden_patterns
FROM community_profiles
WHERE forbidden_patterns @> '{"category": "Promotional"}';

-- Fast: Uses expression index
SELECT subreddit
FROM community_profiles
WHERE (forbidden_patterns->'Promotional')::int > 5;
```

### Pattern 4: React Inline Penalty Highlighting
**What:** Use react-highlight-words to highlight problematic phrases in post text with color-coded severity
**When to use:** For post scoring breakdown "linter-style" inline highlighting (user requirement)
**Example:**
```tsx
// Source: https://github.com/bvaughn/react-highlight-words
import Highlighter from "react-highlight-words";

interface PenaltyHighlighterProps {
  text: string;
  penalties: Array<{phrase: string; severity: 'high' | 'medium' | 'low'}>;
}

export function PenaltyHighlighter({ text, penalties }: PenaltyHighlighterProps) {
  // Map penalties to search terms and class names
  const searchWords = penalties.map(p => p.phrase);
  const highlightClassMap = penalties.reduce((acc, p) => {
    acc[p.phrase] = `penalty-${p.severity}`;
    return acc;
  }, {} as Record<string, string>);

  return (
    <Highlighter
      searchWords={searchWords}
      textToHighlight={text}
      highlightClassName={highlightClassMap}
      autoEscape={true}
    />
  );
}

// Tailwind CSS classes
// penalty-high: bg-red-100 text-red-900 border-b-2 border-red-500
// penalty-medium: bg-orange-100 text-orange-900 border-b-2 border-orange-500
// penalty-low: bg-yellow-100 text-yellow-900 border-b-2 border-yellow-500
```

### Pattern 5: Recharts Client Component Wrapper
**What:** Create "use client" wrapper components for Recharts charts, fetch data server-side and pass as props
**When to use:** For ISC gauge, archetype pie chart, and comparison visualizations (user requirements)
**Example:**
```tsx
// Source: https://app-generator.dev/docs/technologies/nextjs/integrate-recharts.html
"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Legend } from 'recharts';

interface ArchetypePieProps {
  distribution: { archetype: string; count: number }[];
}

const COLORS = {
  Journey: '#0088FE',
  ProblemSolution: '#00C49F',
  Feedback: '#FFBB28'
};

export function ArchetypePie({ distribution }: ArchetypePieProps) {
  const data = distribution.map(d => ({
    name: d.archetype,
    value: d.count
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}  // Creates donut chart
          outerRadius={100}
          fill="#8884d8"
          dataKey="value"
          label
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[entry.name]} />
          ))}
        </Pie>
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}

// Server component usage (page.tsx)
export default async function ProfilePage({ params }) {
  const profile = await fetchCommunityProfile(params.subreddit);

  return (
    <div>
      <ArchetypePie distribution={profile.archetype_distribution} />
    </div>
  );
}
```

### Anti-Patterns to Avoid
- **Loading SpaCy model per request:** Load once at app startup, reuse across tasks (models are ~50MB, loading is expensive)
- **Processing posts one-by-one:** Always use nlp.pipe() with batching; single-doc processing is 3-10x slower
- **Storing Doc objects in DB:** SpaCy Doc objects are not serializable; extract metrics and store as primitives/JSONB
- **GZip + SSE together:** Starlette's GZipMiddleware breaks SSE streaming; disable GZip for SSE endpoints
- **Passing DB objects to Celery:** Serialize only IDs, fetch fresh objects in task to avoid stale data

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Readability metrics | Custom formality scoring with word lists | textstat library | Implements 10+ validated metrics (Flesch-Kincaid, SMOG, Gunning FOG, etc.) with peer-reviewed formulas |
| Sentiment analysis | Regex-based tone detection | vaderSentiment | Handles social media idioms, emojis, capitalization, punctuation intensity; trained on social text |
| SSE streaming | Manual EventSource protocol implementation | sse-starlette | Handles disconnect detection, reconnection, W3C spec compliance, async patterns |
| Chart rendering | Canvas drawing or SVG manipulation | Recharts | Handles responsiveness, accessibility, tooltips, legends, animations, edge cases |
| Text highlighting | Manual span injection with regex | react-highlight-words | Handles overlapping matches, escaping, word boundaries, performance optimization |

**Key insight:** NLP and data visualization have significant edge cases (Unicode handling, screen readers, mobile touch, browser compatibility) that mature libraries solve. Custom solutions miss these and create maintenance burden.

## Common Pitfalls

### Pitfall 1: SpaCy Vocabulary Growth Memory Leak
**What goes wrong:** Long-running SpaCy processes gradually consume more memory as new words are added to nlp.vocab, eventually causing OOM errors in Celery workers
**Why it happens:** SpaCy's vocabulary is not static; processing diverse Reddit posts adds new tokens to the vocab, which is never garbage collected
**How to avoid:**
- Monitor vocab size with `len(nlp.vocab)`
- Reload model when vocab exceeds threshold (e.g., 100k entries beyond initial size)
- Use Celery's `max_tasks_per_child` to restart workers after N tasks
- Use `nlp.vocab.reset_vectors()` if word vectors aren't needed
**Warning signs:** Worker memory usage grows linearly over time; `len(nlp.vocab)` increases with each batch

### Pitfall 2: Celery + SpaCy Multiprocessing Conflict
**What goes wrong:** Using SpaCy's `nlp.pipe(texts, n_process=4)` inside Celery workers spawns nested subprocesses, causing 10-20x slowdown or deadlocks
**Why it happens:** Celery workers already use multiprocessing; SpaCy's internal multiprocessing creates process-in-process overhead
**How to avoid:**
- Never use `n_process` parameter inside Celery tasks
- Scale horizontally with more Celery workers instead
- Use larger `batch_size` (500-2000) to compensate for single-process bottleneck
- Consider separate SpaCy-specific worker pool with higher concurrency
**Warning signs:** Task execution time increases instead of decreases; workers hang or become unresponsive

### Pitfall 3: JSONB Query Without Proper Indexing
**What goes wrong:** Queries on community_profiles.forbidden_patterns or archetype_distribution perform full table scans, causing 500ms+ latency as data grows
**Why it happens:** PostgreSQL defaults to sequential scans on JSONB columns without GIN indexes
**How to avoid:**
- Create GIN indexes on all JSONB columns used in WHERE clauses
- Use expression indexes for frequently accessed keys
- Use `EXPLAIN ANALYZE` to verify index usage
- Filter before extracting (WHERE with @> operator, then SELECT specific keys)
**Warning signs:** EXPLAIN shows "Seq Scan on community_profiles"; query time increases linearly with row count

### Pitfall 4: SSE Connection Leaks in Frontend
**What goes wrong:** EventSource connections remain open after component unmounts, consuming browser resources and backend connections
**Why it happens:** React components don't automatically close EventSource; forgotten cleanup in useEffect
**How to avoid:**
```tsx
useEffect(() => {
  const eventSource = new EventSource(`/api/analysis/progress?task_id=${taskId}`);

  eventSource.addEventListener('progress', handleProgress);
  eventSource.addEventListener('complete', handleComplete);

  // CRITICAL: Cleanup on unmount
  return () => {
    eventSource.close();
  };
}, [taskId]);
```
**Warning signs:** Browser shows increasing number of active connections; backend reports unclosed SSE streams

### Pitfall 5: Recharts Hydration Mismatch in Next.js App Router
**What goes wrong:** Recharts components cause "Hydration failed" errors because SVG rendering differs between server and client
**Why it happens:** Recharts uses browser-only APIs and generates random IDs that don't match server render
**How to avoid:**
- Mark all Recharts components with "use client" directive at top of file
- Fetch data server-side, pass as props to client component
- Use dynamic imports with `ssr: false` if needed: `const Chart = dynamic(() => import('./Chart'), { ssr: false })`
- Never render Recharts in Server Components
**Warning signs:** Console errors about hydration mismatch; charts flash or re-render on page load

### Pitfall 6: Textstat Language Assumptions
**What goes wrong:** Textstat defaults to English syllable counting with nltk.corpus.cmudict, producing incorrect scores for non-English text
**Why it happens:** Library assumes English unless explicitly configured; Reddit posts may contain mixed languages
**How to avoid:**
- Call `textstat.set_lang('en')` explicitly at startup
- Detect language before scoring (use SpaCy's language detector or langdetect library)
- Handle mixed-language posts by scoring only English portions or flagging as "unscored"
- Document language assumptions in ISC score display
**Warning signs:** Readability scores seem random for certain posts; scores don't correlate with perceived complexity

## Code Examples

### Complete SpaCy Pipeline Setup
```python
# Source: https://spacy.io/usage/processing-pipelines
import spacy
from spacy.language import Language
from spacy.tokens import Doc
from textstat import flesch_kincaid_grade, gunning_fog
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Initialize SpaCy model (do this once at app startup)
nlp = spacy.load("en_core_web_md", disable=["ner"])  # NER not needed, save memory

# Register custom extensions
Doc.set_extension("formality_score", default=None, force=True)
Doc.set_extension("tone", default=None, force=True)
Doc.set_extension("avg_sentence_length", default=None, force=True)

# Custom component: Formality scorer
@Language.component("formality_scorer")
def add_formality_score(doc):
    if len(doc.text) < 10:  # Skip very short texts
        return doc

    fk_grade = flesch_kincaid_grade(doc.text)
    fog_index = gunning_fog(doc.text)
    doc._.formality_score = (fk_grade + fog_index) / 2
    return doc

# Custom component: Tone classifier
vader_analyzer = SentimentIntensityAnalyzer()

@Language.component("tone_classifier")
def add_tone(doc):
    if len(doc.text) < 10:
        return doc

    scores = vader_analyzer.polarity_scores(doc.text)
    compound = scores['compound']

    # Classify based on compound score
    if compound >= 0.05:
        tone = "positive"
    elif compound <= -0.05:
        tone = "negative"
    else:
        tone = "neutral"

    doc._.tone = tone
    return doc

# Custom component: Sentence rhythm analyzer
@Language.component("rhythm_analyzer")
def add_rhythm_analysis(doc):
    if not doc.has_annotation("SENT_START"):
        return doc

    sentences = list(doc.sents)
    if len(sentences) == 0:
        return doc

    lengths = [len(sent) for sent in sentences]
    doc._.avg_sentence_length = sum(lengths) / len(lengths)
    return doc

# Add components to pipeline
nlp.add_pipe("formality_scorer", last=True)
nlp.add_pipe("tone_classifier", last=True)
nlp.add_pipe("rhythm_analyzer", last=True)

# Batch processing pattern
def analyze_posts_batch(posts: list, batch_size: int = 100):
    """Process posts in batches with SpaCy pipeline"""
    texts = [p.body for p in posts]

    # Use nlp.pipe for efficient batching
    docs = list(nlp.pipe(texts, batch_size=batch_size))

    results = []
    for post, doc in zip(posts, docs):
        results.append({
            'post_id': post.id,
            'formality': doc._.formality_score,
            'tone': doc._.tone,
            'avg_sentence_length': doc._.avg_sentence_length,
            'num_sentences': len(list(doc.sents)),
            'num_tokens': len(doc)
        })

    return results
```

### SSE Progress Tracking (Backend)
```python
# Source: https://medium.com/@nandagopal05/server-sent-events-with-python-fastapi-f1960e0c8e4b
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from celery.result import AsyncResult
import asyncio
import json

router = APIRouter()

@router.post("/campaigns/{campaign_id}/analyze")
async def trigger_analysis(campaign_id: str, force_refresh: bool = False):
    """Trigger analysis task, return job_id for SSE tracking"""
    # Check if analysis already exists
    existing = get_community_profiles(campaign_id)
    if existing and not force_refresh:
        return {"status": "exists", "message": "Analysis already complete"}

    # Trigger Celery task
    task = analyze_campaign_posts.delay(campaign_id)

    return {
        "status": "started",
        "job_id": task.id
    }

@router.get("/campaigns/{campaign_id}/analysis/progress")
async def analysis_progress(campaign_id: str, job_id: str):
    """SSE endpoint for progress tracking"""
    async def event_generator():
        task = AsyncResult(job_id)

        while True:
            # Check if client disconnected
            # (sse-starlette handles this automatically)

            if task.state == 'PENDING':
                yield {
                    "event": "status",
                    "data": json.dumps({"status": "pending"})
                }
            elif task.state == 'PROGRESS':
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "current": task.info.get('current', 0),
                        "total": task.info.get('total', 0),
                        "status": task.info.get('status', '')
                    })
                }
            elif task.state == 'SUCCESS':
                yield {
                    "event": "complete",
                    "data": json.dumps({
                        "status": "complete",
                        "result": task.info
                    })
                }
                break
            elif task.state == 'FAILURE':
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "status": "failed",
                        "error": str(task.info)
                    })
                }
                break

            await asyncio.sleep(0.5)  # Poll every 500ms

    return EventSourceResponse(event_generator())
```

### SSE Progress Tracking (Frontend)
```tsx
// Source: Phase 2 SSE pattern (established in prior phase)
"use client";

import { useEffect, useState } from 'react';
import { useToast } from '@/components/ui/use-toast';

interface AnalysisProgressProps {
  campaignId: string;
  jobId: string;
  onComplete: () => void;
}

export function AnalysisProgress({ campaignId, jobId, onComplete }: AnalysisProgressProps) {
  const [progress, setProgress] = useState({ current: 0, total: 0, status: '' });
  const { toast } = useToast();

  useEffect(() => {
    // Use Next.js API route proxy (not direct FastAPI URL)
    const eventSource = new EventSource(
      `/api/campaigns/${campaignId}/analysis/progress?job_id=${jobId}`
    );

    eventSource.addEventListener('progress', (e) => {
      const data = JSON.parse(e.data);
      setProgress(data);
    });

    eventSource.addEventListener('complete', (e) => {
      toast({
        title: "Analysis complete",
        description: "Community profiles are ready to view",
        action: <a href={`/campaigns/${campaignId}/profiles`}>View Profiles</a>
      });
      eventSource.close();
      onComplete();
    });

    eventSource.addEventListener('error', (e) => {
      const data = JSON.parse(e.data);
      toast({
        title: "Analysis failed",
        description: data.error,
        variant: "destructive"
      });
      eventSource.close();
    });

    // CRITICAL: Cleanup on unmount
    return () => {
      eventSource.close();
    };
  }, [campaignId, jobId, onComplete, toast]);

  return (
    <div className="space-y-2">
      <div className="text-sm text-muted-foreground">
        {progress.status}
      </div>
      <div className="w-full bg-secondary rounded-full h-2">
        <div
          className="bg-primary h-2 rounded-full transition-all"
          style={{ width: `${(progress.current / progress.total) * 100}%` }}
        />
      </div>
      <div className="text-xs text-muted-foreground">
        {progress.current} / {progress.total} posts analyzed
      </div>
    </div>
  );
}
```

### ISC Scoring Algorithm (Example Implementation)
```python
# Source: Custom implementation based on spec requirements
def calculate_isc_score(posts: list) -> float:
    """
    Calculate Intrinsic Sensitivity Coefficient (ISC) for a subreddit.

    ISC measures community sensitivity to marketing/promotional content.
    Scale: 1.0 (very tolerant) to 10.0 (extremely sensitive)

    Factors:
    - Marketing jargon penalty frequency
    - Link density penalty frequency
    - Successful post vulnerability levels
    - Thread depth correlation with authenticity
    """
    if len(posts) < 10:
        raise ValueError("Insufficient data: need at least 10 posts")

    # Weight factors
    JARGON_WEIGHT = 0.3
    LINK_WEIGHT = 0.2
    VULNERABILITY_WEIGHT = 0.3
    DEPTH_WEIGHT = 0.2

    # Calculate component scores
    jargon_sensitivity = calculate_jargon_sensitivity(posts)  # 0-10
    link_sensitivity = calculate_link_sensitivity(posts)      # 0-10
    vulnerability_preference = calculate_vulnerability_pref(posts)  # 0-10
    depth_correlation = calculate_depth_correlation(posts)    # 0-10

    # Weighted average
    isc = (
        jargon_sensitivity * JARGON_WEIGHT +
        link_sensitivity * LINK_WEIGHT +
        vulnerability_preference * VULNERABILITY_WEIGHT +
        depth_correlation * DEPTH_WEIGHT
    )

    return round(isc, 1)

def calculate_jargon_sensitivity(posts: list) -> float:
    """Higher score = community more sensitive to marketing jargon"""
    jargon_patterns = [
        r'\b(synerg|leverage|paradigm|disrupt|innovate)\w*\b',
        r'\b(game.?changer|thought leader|best.?in.?class)\b',
        r'\b(reach out|circle back|touch base)\b'
    ]

    low_score_with_jargon = 0
    high_score_with_jargon = 0

    for post in posts:
        has_jargon = any(re.search(p, post.body, re.I) for p in jargon_patterns)
        if has_jargon:
            if post.score < 5:
                low_score_with_jargon += 1
            else:
                high_score_with_jargon += 1

    # If jargon posts score low, community is sensitive
    if low_score_with_jargon + high_score_with_jargon == 0:
        return 5.0  # Neutral

    ratio = low_score_with_jargon / (low_score_with_jargon + high_score_with_jargon)
    return ratio * 10  # 0-10 scale
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| NLTK for production NLP | SpaCy with custom components | 2018-2020 | SpaCy 3x faster, better batching, production-ready pipelines |
| External sentiment APIs | Local VADER sentiment | 2019-2021 | Zero API cost, no rate limits, optimized for social media |
| Chart.js for React | Recharts declarative components | 2020-2022 | Recharts more React-native, better TypeScript support |
| Manual SSE implementation | sse-starlette library | 2021-2023 | W3C spec compliance, auto-reconnect, disconnect detection |
| Client-side CSV download | Server streaming responses | 2023-2024 | Better memory efficiency, progressive rendering |

**Deprecated/outdated:**
- **spaCy < 3.0:** Version 2.x used different config system; v3+ uses config.cfg and @Language decorators
- **textblob for sentiment:** Superseded by VADER for social media; textblob better for formal text
- **react-vis (Uber):** Unmaintained since 2020; use Recharts, Nivo, or Victory instead
- **EventSource polyfills:** Modern browsers (2023+) support SSE natively; polyfills only for IE11 (out of support)

## Open Questions

1. **ISC Scoring Weight Tuning**
   - What we know: Spec defines factors (vulnerability, thread depth, rhythm, penalties) but not exact weights
   - What's unclear: Optimal weight distribution across factors; whether weights should vary by subreddit category
   - Recommendation: Start with equal weights (0.25 each), tune based on validation against known high/low sensitivity subreddits

2. **Insufficient Data Threshold**
   - What we know: Need to block profile creation if data insufficient; user decision to show "Need more data"
   - What's unclear: Exact minimum post count, minimum timespan, minimum upvote distribution
   - Recommendation: Start with 10 posts minimum (statistical significance), consider expanding to 30+ for production; validate that posts span multiple authors and dates

3. **Rhythm Pattern Visualization**
   - What we know: Claude's discretion to design rhythm pattern visualization in profile tabs
   - What's unclear: Best way to visualize sentence length distribution, rhythm consistency, pattern matching
   - Recommendation: Histogram of sentence lengths + line chart showing rhythm over time; use Recharts BarChart and LineChart

4. **Forbidden Pattern Categories**
   - What we know: Show categories (Promotional, Self-referential, Link patterns) with counts, not raw patterns
   - What's unclear: Complete taxonomy of categories; how granular to make categorization
   - Recommendation: Start with 5-7 broad categories (Promotional, Self-referential, Link patterns, Competitor mentions, Low-effort, Off-topic, Spam indicators); refine based on actual detected patterns

## Sources

### Primary (HIGH confidence)
- [spaCy Official Documentation - Processing Pipelines](https://spacy.io/usage/processing-pipelines) - Pipeline configuration, batching, custom components
- [spaCy Official Documentation - Linguistic Features](https://spacy.io/usage/linguistic-features) - Built-in features and capabilities
- [spaCy Official Documentation - Models](https://spacy.io/models/en) - English model comparison (sm/md/lg)
- [textstat PyPI](https://pypi.org/project/textstat/) - Version 0.7.12, readability metrics
- [vaderSentiment GitHub](https://github.com/cjhutto/vaderSentiment) - Official repo with usage patterns
- [sse-starlette GitHub](https://github.com/sysid/sse-starlette) - Official repo for FastAPI SSE
- [react-highlight-words GitHub](https://github.com/bvaughn/react-highlight-words) - v0.21.0 (Jan 2025), actively maintained
- [PostgreSQL JSONB Indexing - Crunchy Data](https://www.crunchydata.com/blog/indexing-jsonb-in-postgres) - GIN index best practices

### Secondary (MEDIUM confidence)
- [Technostacks: React Chart Libraries 2026](https://technostacks.com/blog/react-chart-libraries/) - Recharts ecosystem position
- [Syncfusion: Top 5 React Chart Libraries 2026](https://www.syncfusion.com/blogs/post/top-5-react-chart-libraries) - Recharts vs alternatives
- [Next.js Charts with Recharts Guide](https://app-generator.dev/docs/technologies/nextjs/integrate-recharts.html) - Next.js App Router + Recharts patterns
- [Medium: SSE with FastAPI](https://medium.com/@nandagopal05/server-sent-events-with-python-fastapi-f1960e0c8e4b) - Implementation examples
- [Celery Best Practices - Deni Bertović](https://denibertovic.com/posts/celery-best-practices/) - Task design patterns
- [Programming Helper: Celery 2026](https://www.programming-helper.com/tech/celery-2026-python-distributed-task-queue-redis-rabbitmq) - Current state overview

### Tertiary (LOW confidence)
- [SpaCy Memory Issues - GitHub Discussions](https://github.com/explosion/spaCy/discussions/10015) - Community-reported memory leak patterns
- [SpaCy High Memory Consumption - GitHub](https://github.com/explosion/spaCy/discussions/13194) - Vocab growth issues
- [VADER Sentiment Analysis - Hex Template](https://hex.tech/templates/sentiment-analysis/vader-sentiment-analysis/) - Usage examples (not official docs)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - SpaCy, textstat, vaderSentiment are established industry standards with official docs verified
- Architecture: HIGH - Patterns verified with official SpaCy, FastAPI, Next.js documentation; SSE pattern established in Phase 2
- Pitfalls: MEDIUM - Memory issues verified via GitHub issues; JSONB indexing from authoritative sources; some pitfalls from experience-based sources

**Research date:** 2026-02-10
**Valid until:** 2026-03-12 (30 days - stable technologies with infrequent breaking changes)

**Notes:**
- SpaCy 3.8 released May 2025; stable release, no major breaking changes expected soon
- Recharts version number not confirmed (npm access blocked); latest known 2.x series
- ISC scoring algorithm is custom domain logic; no existing library found (as expected)
- User constraints from CONTEXT.md heavily shape implementation decisions; research focused on HOW to implement locked choices, not WHETHER to implement them
