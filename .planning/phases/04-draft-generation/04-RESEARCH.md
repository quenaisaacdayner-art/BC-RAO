# Phase 4: Draft Generation - Research

**Researched:** 2026-02-10
**Domain:** LLM integration for draft generation, form UX, prompt engineering, dashboard progression
**Confidence:** MEDIUM

## Summary

This phase implements draft generation powered by LLM APIs (OpenAI/Anthropic), with a single-form interface for selecting subreddit and archetype, ISC-based safety gating, and a full-page editor with scoring display. The standard approach uses FastAPI StreamingResponse with OpenAI/Anthropic streaming APIs, React Hook Form for form validation, shadcn/ui components for UI, and the existing ISCGauge pattern from Phase 3 for score visualization.

The generation pipeline constructs prompts dynamically from community profiles and syntax blacklists, enforces ISC gating rules (blocks risky archetypes when ISC > 7.5), and validates generated drafts against blacklist patterns. The editor displays vulnerability and rhythm match scores in a sidebar with read-only gauges, supports free-form editing without re-scoring, and provides four actions: Approve, Discard, Regenerate with feedback, and Copy to clipboard.

Dashboard journey stages use linear progression enforcement with auto-advance notifications (toast alerts when prerequisites complete), per-campaign stage indicators (not global), and simple UI for Stage 4 (Alchemical Transmutation) with a generate button and draft list.

**Primary recommendation:** Use OpenAI Python SDK with streaming for generation, FastAPI StreamingResponse for SSE delivery to frontend, React Hook Form for the single-page form, navigator.clipboard.writeText() for copy functionality, and Sonner toasts for stage progression notifications.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Generation flow:**
- Single form (not wizard): one page with subreddit dropdown, archetype selector, optional context textarea, and generate button
- Three inputs only: subreddit, archetype, optional context — no tone selector or length preference
- All campaign subreddits shown in dropdown, not just profiled ones — warn if no community profile exists and generate with generic defaults
- ISC gating UX: inline warning banner + auto-switch to Feedback archetype when ISC > 7.5 — other archetypes disabled for that subreddit with explanation

**Draft editor experience:**
- Full-page editor layout: draft text on left, scores/metadata on right sidebar
- Sidebar gauges for vulnerability and rhythm match scores — radial gauges consistent with community profile ISC gauge pattern
- No live re-scoring on manual edits — scores reflect the generated draft only, editing is free-form
- Four actions: Approve (saves as ready), Discard (deletes), Regenerate (new draft with optional feedback), Copy to clipboard (for pasting into Reddit)

**Dashboard journey stages:**
- Per-campaign stage indicator (not global dashboard) — each campaign shows its own 4-stage progress
- Enforced linear progression — must complete each stage before the next unlocks (can't generate before analysis is done)
- Stage 4 (Alchemical Transmutation): simple generate button on campaign page with draft list below, not a complex hub
- Auto-advance with toast notification when prerequisites are met ("Community Intelligence complete — you can now generate drafts")

### Claude's Discretion

- LLM prompt construction strategy and template design
- Blacklist enforcement implementation (pre-generation filter vs post-generation check)
- Draft text editor component choice (plain textarea vs rich editor)
- Stage indicator visual design (stepper, badges, progress dots)
- Error states and loading patterns during generation

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| OpenAI Python SDK | Latest (1.x) | LLM generation with streaming | Official SDK, native streaming support, well-documented |
| FastAPI StreamingResponse | 0.109+ | SSE delivery of LLM chunks | Built into FastAPI, used in Phase 2/3 for progress tracking |
| React Hook Form | 7.71.1+ | Form validation and state | Already in stack, schema-based validation with Zod |
| Zod | 4.3.6+ | Schema validation | Already in stack, TypeScript-native validation |
| Sonner | 2.0.7+ | Toast notifications | Already in stack (from package.json), modern toast component for shadcn/ui |
| shadcn/ui Form | Latest | Form field components | Consistent with existing UI patterns |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Anthropic Python SDK | Latest (0.x) | Alternative LLM provider | If using Claude models instead of OpenAI |
| use-debounce | Latest | Debounced regeneration feedback | If implementing autosave for feedback textarea |
| Recharts RadialBar | 3.7.0+ | Radial gauge for scores | Consistent with Phase 3 ISCGauge pattern |
| shadcn/ui Progress | Latest | Linear progress alternative | If not using radial gauges |
| shadcn/ui Textarea | Latest | Multi-line text input | For context input and draft editor |
| shadcn/ui Select | Latest | Dropdown components | For subreddit and archetype selectors |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| OpenAI streaming | LangChain streaming | LangChain adds abstraction layer; direct SDK is simpler for single-provider use case |
| Plain textarea | Lexical/Slate rich editor | User decision: free-form editing with no re-scoring means plain textarea sufficient |
| React Hook Form | Formik | RHF already in stack, better TypeScript support, smaller bundle |
| navigator.clipboard | react-copy-to-clipboard library | Native API simpler, no extra dependency, good browser support in 2026 |
| Sonner toasts | react-hot-toast | Sonner already in stack, designed for shadcn/ui, better animations |

**Installation:**
```bash
# Backend (Python)
pip install openai>=1.0.0  # or anthropic>=0.18.0

# Frontend (Next.js) - Already installed
# react-hook-form, zod, sonner, recharts already in package.json
```

## Architecture Patterns

### Recommended Backend Structure
```
api/
├── generation/
│   ├── prompt_builder.py       # Dynamic prompt construction from profiles
│   ├── llm_client.py           # OpenAI/Anthropic client wrapper
│   ├── blacklist_validator.py  # Pre/post-generation validation
│   ├── isc_gating.py           # ISC threshold logic for archetype blocking
│   └── tasks.py                # Draft generation tasks
├── routes/
│   └── drafts.py               # POST /drafts/generate (streaming), PATCH /drafts/:id
└── models/
    └── draft.py                # SQLAlchemy model for drafts table
```

### Recommended Frontend Structure
```
app/
├── campaigns/[id]/
│   ├── drafts/
│   │   ├── page.tsx            # Draft list + generate button (Stage 4)
│   │   ├── new/
│   │   │   └── page.tsx        # Single-form generation interface
│   │   └── [draftId]/
│   │       └── edit/
│   │           └── page.tsx    # Full-page editor with sidebar
│   └── page.tsx                # Campaign detail with stage indicator
└── components/
    ├── drafts/
    │   ├── GenerationForm.tsx  # Single-page form (subreddit, archetype, context)
    │   ├── DraftEditor.tsx     # Full-page editor with sidebar
    │   ├── ScoreSidebar.tsx    # Vulnerability + rhythm gauges
    │   ├── ISCGatingWarning.tsx # Inline warning banner
    │   └── DraftActions.tsx    # Approve/Discard/Regenerate/Copy buttons
    └── dashboard/
        └── StageIndicator.tsx  # Linear progression indicator
```

### Pattern 1: Dynamic Prompt Construction from Community Profile
**What:** Build LLM prompts dynamically by loading community profile (ISC, archetype patterns, rhythm data) and syntax blacklist, then injecting into prompt template
**When to use:** For all draft generation requests (user requirement)
**Example:**
```python
# Source: Research synthesis from OpenAI prompt engineering best practices
from typing import Dict, Optional
from models import CommunityProfile, SyntaxBlacklist

class PromptBuilder:
    """Build dynamic prompts from community intelligence"""

    SYSTEM_TEMPLATE = """You are an expert Reddit marketer who crafts authentic, community-native posts.

Your goal: Create a {archetype} post for r/{subreddit} that blends in naturally.

## Community DNA
- ISC Score: {isc_score}/10 ({isc_tier} sensitivity to promotional content)
- Preferred archetype patterns: {archetype_patterns}
- Typical sentence rhythm: {rhythm_pattern}
- Formality level: {formality_level}

## Forbidden Patterns (NEVER use these)
{blacklist_patterns}

## ISC Gating Rules
{isc_gating_rules}

## Output Format
Return ONLY the post body text. No metadata, no explanations."""

    USER_TEMPLATE = """Create a {archetype} post about: {user_context}

Requirements:
- Match the community's natural rhythm and formality
- Avoid ALL forbidden patterns
- Sound like a genuine community member
- {archetype_specific_guidance}"""

    def build_prompt(
        self,
        subreddit: str,
        archetype: str,
        user_context: str,
        profile: Optional[CommunityProfile] = None
    ) -> Dict[str, str]:
        """Build system + user prompts from community profile"""

        # Use generic defaults if no profile exists (user requirement)
        if not profile:
            return self._build_generic_prompt(archetype, user_context)

        # Load blacklist for this subreddit
        blacklist = self._load_blacklist(subreddit)

        # Format blacklist patterns by category
        blacklist_text = self._format_blacklist(blacklist)

        # Format ISC gating rules based on score
        isc_rules = self._format_isc_rules(profile.isc_score, archetype)

        # Build system message
        system_msg = self.SYSTEM_TEMPLATE.format(
            archetype=archetype,
            subreddit=subreddit,
            isc_score=profile.isc_score,
            isc_tier=profile.tier,
            archetype_patterns=profile.archetype_distribution.get(archetype, {}),
            rhythm_pattern=self._summarize_rhythm(profile.rhythm_metadata),
            formality_level=profile.avg_formality,
            blacklist_patterns=blacklist_text,
            isc_gating_rules=isc_rules
        )

        # Build user message with archetype-specific guidance
        user_msg = self.USER_TEMPLATE.format(
            archetype=archetype,
            user_context=user_context,
            archetype_specific_guidance=self._get_archetype_guidance(
                archetype, profile.isc_score
            )
        )

        return {
            "system": system_msg,
            "user": user_msg
        }

    def _get_archetype_guidance(self, archetype: str, isc_score: float) -> str:
        """Archetype-specific generation rules"""
        guidance = {
            "Journey": "Share a personal story about how you discovered a solution",
            "ProblemSolution": "Focus on the problem first, solution second",
            "Feedback": "Ask for feedback naturally, mention what you've tried"
        }

        # ISC gating: Feedback archetype with high ISC gets extra constraints
        if archetype == "Feedback" and isc_score > 7.5:
            return guidance[archetype] + " | CRITICAL: Zero links, maximum vulnerability"

        return guidance.get(archetype, "")

    def _format_isc_rules(self, isc_score: float, archetype: str) -> str:
        """Format ISC-based gating rules"""
        if isc_score <= 7.5:
            return "Standard authenticity requirements apply"

        # High ISC = strict rules
        rules = [
            "Community is EXTREMELY sensitive (ISC > 7.5)",
            "Maximize vulnerability (personal pronouns, emotions, questions)",
            "Minimize promotional language",
        ]

        if archetype == "Feedback":
            rules.append("ZERO links allowed (Feedback archetype + high ISC)")

        return "\n".join(f"- {r}" for r in rules)
```

### Pattern 2: FastAPI Streaming Response for LLM Generation
**What:** Stream LLM tokens via Server-Sent Events using FastAPI StreamingResponse and OpenAI streaming
**When to use:** For draft generation endpoint to provide real-time feedback to frontend
**Example:**
```python
# Source: Verified from multiple sources (Medium articles, GitHub examples)
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
import json

router = APIRouter()
client = AsyncOpenAI()

@router.post("/drafts/generate")
async def generate_draft(request: GenerateRequest):
    """Generate draft with streaming response"""

    # Build prompt from community profile
    prompt_builder = PromptBuilder()
    prompts = prompt_builder.build_prompt(
        subreddit=request.subreddit,
        archetype=request.archetype,
        user_context=request.context,
        profile=get_community_profile(request.subreddit)
    )

    # Stream generator
    async def stream_generator():
        try:
            # OpenAI streaming
            stream = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": prompts["system"]},
                    {"role": "user", "content": prompts["user"]}
                ],
                stream=True,
                temperature=0.7
            )

            full_text = ""

            # Yield chunks as SSE
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_text += content

                    yield f"data: {json.dumps({'type': 'chunk', 'content': content})}\n\n"

            # Final event with complete draft + metadata
            yield f"data: {json.dumps({
                'type': 'complete',
                'draft': full_text,
                'tokens': len(full_text.split()),  # Rough estimate
                'model': 'gpt-4'
            })}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

### Pattern 3: React Hook Form with Zod Validation
**What:** Single-page form with subreddit dropdown, archetype selector, and optional context textarea using React Hook Form + Zod
**When to use:** For the generation form (user requirement: single form, not wizard)
**Example:**
```tsx
// Source: shadcn/ui React Hook Form docs
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

const formSchema = z.object({
  subreddit: z.string().min(1, "Select a subreddit"),
  archetype: z.enum(["Journey", "ProblemSolution", "Feedback"], {
    required_error: "Select an archetype"
  }),
  context: z.string().optional()
});

interface GenerationFormProps {
  campaignSubreddits: string[];
  onSubmit: (values: z.infer<typeof formSchema>) => void;
  iscData: Record<string, { score: number; tier: string }>;
}

export function GenerationForm({ campaignSubreddits, onSubmit, iscData }: GenerationFormProps) {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      context: ""
    }
  });

  const selectedSubreddit = form.watch("subreddit");
  const selectedArchetype = form.watch("archetype");

  // Check ISC gating
  const isc = iscData[selectedSubreddit];
  const isHighISC = isc && isc.score > 7.5;
  const shouldGate = isHighISC && selectedArchetype !== "Feedback";

  // Auto-switch to Feedback when ISC > 7.5 (user requirement)
  useEffect(() => {
    if (shouldGate) {
      form.setValue("archetype", "Feedback");
    }
  }, [shouldGate, form]);

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {/* Subreddit Selector */}
        <FormField
          control={form.control}
          name="subreddit"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Subreddit</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select target subreddit" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {campaignSubreddits.map((sub) => (
                    <SelectItem key={sub} value={sub}>
                      r/{sub}
                      {!iscData[sub] && <span className="text-muted-foreground ml-2">(No profile)</span>}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedSubreddit && !iscData[selectedSubreddit] && (
                <p className="text-sm text-yellow-600">
                  Warning: No community profile exists. Will generate with generic defaults.
                </p>
              )}
              <FormMessage />
            </FormItem>
          )}
        />

        {/* ISC Gating Warning Banner */}
        {isHighISC && (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-600 mt-0.5" />
              <div className="flex-1">
                <h4 className="font-medium text-orange-900">High Sensitivity Community</h4>
                <p className="text-sm text-orange-700 mt-1">
                  r/{selectedSubreddit} has ISC {isc.score}/10 ({isc.tier}). Only Feedback archetype available with zero links.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Archetype Selector */}
        <FormField
          control={form.control}
          name="archetype"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Archetype</FormLabel>
              <Select onValueChange={field.onChange} value={field.value}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select archetype" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="Journey" disabled={isHighISC}>
                    Journey
                    {isHighISC && <span className="ml-2 text-xs">(Blocked: ISC > 7.5)</span>}
                  </SelectItem>
                  <SelectItem value="ProblemSolution" disabled={isHighISC}>
                    Problem/Solution
                    {isHighISC && <span className="ml-2 text-xs">(Blocked: ISC > 7.5)</span>}
                  </SelectItem>
                  <SelectItem value="Feedback">Feedback</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Optional Context */}
        <FormField
          control={form.control}
          name="context"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Context (Optional)</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="E.g., 'Launching a new project management SaaS for remote teams'"
                  className="min-h-[100px]"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit" size="lg" className="w-full">
          Generate Draft
        </Button>
      </form>
    </Form>
  );
}
```

### Pattern 4: Copy to Clipboard with Feedback
**What:** Use native navigator.clipboard.writeText() with state for copy confirmation
**When to use:** For "Copy to clipboard" action in draft editor (user requirement)
**Example:**
```tsx
// Source: Next.js Clipboard API best practices
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Check, Copy } from "lucide-react";

interface CopyButtonProps {
  text: string;
}

export function CopyButton({ text }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);

      // Reset after 2 seconds
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
      // Fallback for unsupported browsers (rare in 2026)
      const textArea = document.createElement("textarea");
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand("copy");
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <Button
      onClick={handleCopy}
      variant="outline"
      className="gap-2"
    >
      {copied ? (
        <>
          <Check className="h-4 w-4" />
          Copied!
        </>
      ) : (
        <>
          <Copy className="h-4 w-4" />
          Copy to Clipboard
        </>
      )}
    </Button>
  );
}
```

### Pattern 5: Stage Progression with Toast Notifications
**What:** Linear stage progression with auto-advance toast notifications using Sonner
**When to use:** For dashboard journey stages (user requirement: auto-advance with toast)
**Example:**
```tsx
// Source: shadcn/ui Sonner documentation
"use client";

import { useEffect } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";

interface StageIndicatorProps {
  currentStage: number;
  stages: Array<{ id: number; name: string; completed: boolean }>;
  campaignId: string;
}

export function StageIndicator({ currentStage, stages, campaignId }: StageIndicatorProps) {
  // Auto-advance notification when prerequisites complete
  useEffect(() => {
    const nextStage = stages.find(s => s.id === currentStage + 1);
    const currentStageData = stages.find(s => s.id === currentStage);

    if (currentStageData?.completed && nextStage) {
      // Show toast notification (user requirement)
      toast.success(`${currentStageData.name} complete — you can now ${nextStage.name}`, {
        action: {
          label: "Continue",
          onClick: () => {
            window.location.href = getStageUrl(nextStage.id, campaignId);
          }
        },
        duration: 5000
      });
    }
  }, [currentStage, stages, campaignId]);

  return (
    <div className="flex items-center gap-2">
      {stages.map((stage, idx) => (
        <div key={stage.id} className="flex items-center gap-2">
          {/* Stage badge */}
          <div
            className={cn(
              "flex items-center gap-2 px-3 py-2 rounded-lg border",
              stage.completed
                ? "bg-green-50 border-green-200 text-green-900"
                : stage.id === currentStage
                ? "bg-blue-50 border-blue-200 text-blue-900"
                : "bg-gray-50 border-gray-200 text-gray-500"
            )}
          >
            <span className="text-sm font-medium">{stage.name}</span>
            {stage.completed && <Check className="h-4 w-4" />}
          </div>

          {/* Arrow between stages */}
          {idx < stages.length - 1 && (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      ))}
    </div>
  );
}

function getStageUrl(stageId: number, campaignId: string): string {
  const stageUrls = {
    1: `/campaigns/${campaignId}`,           // Project Briefing
    2: `/campaigns/${campaignId}/collect`,   // Strategic Selection
    3: `/campaigns/${campaignId}/profiles`,  // Community Intelligence
    4: `/campaigns/${campaignId}/drafts`     // Alchemical Transmutation
  };
  return stageUrls[stageId] || `/campaigns/${campaignId}`;
}
```

### Anti-Patterns to Avoid
- **Multi-step wizard for generation form:** User decision is single-page form with three inputs
- **Live re-scoring on edits:** User decision is scores reflect generated draft only, editing is free-form
- **Global dashboard stage indicator:** User decision is per-campaign stage indicators
- **Complex Stage 4 hub:** User decision is simple generate button + draft list
- **Streaming without error handling:** Always wrap SSE generators in try/catch and yield error events
- **Hardcoded prompts:** Always build prompts dynamically from community profiles (user requirement)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM streaming | Custom SSE protocol | OpenAI SDK streaming + FastAPI StreamingResponse | OpenAI SDK handles reconnection, chunk parsing, token counting; FastAPI handles SSE spec compliance |
| Form validation | Manual input validation | React Hook Form + Zod | RHF handles form state, errors, submission; Zod provides type-safe schemas with TypeScript inference |
| Toast notifications | Custom toast component | Sonner (already in stack) | Handles stacking, animations, accessibility, promise-based toasts, action buttons |
| Clipboard API | document.execCommand("copy") | navigator.clipboard.writeText() | Modern Clipboard API is promise-based, more secure (HTTPS required), better error handling |
| Prompt templates | String concatenation | Template builder class | Easier to test, version, and maintain; supports conditional logic and escaping |

**Key insight:** LLM integration has significant edge cases (rate limits, token limits, streaming errors, timeout handling) that official SDKs solve. Custom solutions miss retry logic, backoff strategies, and token counting.

## Common Pitfalls

### Pitfall 1: Forgetting ISC Gating Enforcement
**What goes wrong:** User selects Journey/ProblemSolution archetype for high-ISC subreddit, system generates draft that violates community norms, post gets banned
**Why it happens:** Frontend validation alone is insufficient; backend must also enforce ISC gating rules
**How to avoid:**
- Implement ISC gating in both frontend (UX) and backend (enforcement)
- Backend should reject generation requests for blocked archetypes
- Include ISC gating rules in LLM system prompt as additional safeguard
- Log violations for monitoring
**Warning signs:** Generated drafts for high-ISC communities have links or promotional language; Journey archetypes created for ISC > 7.5

### Pitfall 2: SSE Connection Not Closed on Unmount
**What goes wrong:** User navigates away during generation, EventSource connection stays open, consuming server resources
**Why it happens:** React components don't automatically close EventSource; forgotten cleanup in useEffect
**How to avoid:**
```tsx
useEffect(() => {
  const eventSource = new EventSource(`/api/drafts/generate`);

  eventSource.addEventListener('chunk', handleChunk);
  eventSource.addEventListener('complete', handleComplete);

  // CRITICAL: Cleanup on unmount
  return () => {
    eventSource.close();
  };
}, []);
```
**Warning signs:** Server shows unclosed SSE connections; browser devtools show active EventSource after navigation

### Pitfall 3: Blacklist Validation Only in Prompt
**What goes wrong:** LLM sometimes ignores blacklist instructions, generated draft contains forbidden patterns, post violates subreddit rules
**Why it happens:** LLMs are non-deterministic; prompt instructions reduce but don't eliminate blacklist violations
**How to avoid:**
- Post-generation validation: check draft against regex blacklist before saving
- If violations found, either auto-regenerate or show warning to user
- Track violation rate per model/prompt template
- Consider hybrid approach: prompt instructions + post-generation validation
**Warning signs:** Generated drafts occasionally contain blacklisted phrases; violation rate > 5%

### Pitfall 4: No Token/Cost Tracking
**What goes wrong:** LLM API costs spiral out of control; no visibility into which users/campaigns generate most drafts
**Why it happens:** OpenAI/Anthropic charge per token; failing to track usage leads to budget surprises
**How to avoid:**
- Store token counts with each draft (input_tokens, output_tokens, model_used)
- Calculate costs using current pricing (track in DB or config)
- Add monthly limits per user tier (user requirement: GENR-09)
- Show usage dashboard for admins
- Log all generation requests with timestamps, user_id, campaign_id
**Warning signs:** Unexpected API bills; no visibility into usage patterns; users hitting rate limits

### Pitfall 5: Textarea Without Maxlength
**What goes wrong:** User pastes massive context (10k+ words), LLM API rejects request due to token limits, no error handling
**Why it happens:** Context textarea has no validation; combined with system prompt exceeds model context window
**How to avoid:**
- Set maxlength on context textarea (e.g., 2000 characters = ~500 tokens)
- Calculate token count before generation (rough estimate: 1 token ≈ 4 characters)
- Reserve token budget for system prompt + blacklist + output (e.g., 2000 input + 2000 output = 4000 total)
- Show character count to user: "450 / 2000 characters"
- Backend validation: reject if estimated tokens exceed safe threshold
**Warning signs:** Generation requests fail with "context too long" errors; no frontend validation on context length

### Pitfall 6: Ignoring Profile Absence
**What goes wrong:** User generates draft for subreddit with no community profile, system crashes trying to access profile.isc_score
**Why it happens:** User requirement allows generation for all campaign subreddits, even those without profiles
**How to avoid:**
- Check if profile exists before accessing fields
- Use generic defaults when profile is None (user requirement)
- Show warning in UI: "No community profile exists. Will generate with generic defaults."
- Consider creating minimal generic profile template (neutral ISC, no blacklist, average formality)
- Log generations without profiles for monitoring
**Warning signs:** Null pointer errors when accessing profile fields; crashes on generation for new campaigns

## Code Examples

### Complete Prompt Builder Implementation
```python
# Source: Synthesized from OpenAI/Anthropic best practices
from dataclasses import dataclass
from typing import Optional, List, Dict
import re

@dataclass
class PromptTemplate:
    system: str
    user: str

class PromptBuilder:
    """Build dynamic prompts from community profiles and blacklists"""

    # Generic defaults when no profile exists
    GENERIC_DEFAULTS = {
        "isc_score": 5.0,
        "isc_tier": "Moderate",
        "formality": "Casual but clear",
        "rhythm": "Mixed sentence lengths, conversational tone",
        "archetype_patterns": "Focus on authenticity and value"
    }

    def build_prompt(
        self,
        subreddit: str,
        archetype: str,
        user_context: str,
        profile: Optional[CommunityProfile] = None
    ) -> PromptTemplate:
        """Build system + user prompts"""

        # Use generic defaults if no profile
        if not profile:
            return self._build_generic(subreddit, archetype, user_context)

        # Enforce ISC gating
        if profile.isc_score > 7.5 and archetype != "Feedback":
            raise ValueError(f"ISC {profile.isc_score} > 7.5: only Feedback archetype allowed")

        # Load blacklist
        blacklist = self._load_blacklist(subreddit)

        # Build system message
        system = f"""You are an expert Reddit marketer crafting authentic posts.

## Target Community: r/{subreddit}
- Sensitivity: {profile.isc_score}/10 ({profile.tier})
- Typical formality: {profile.avg_formality:.1f}/10
- Rhythm: {self._describe_rhythm(profile.rhythm_metadata)}

## Archetype: {archetype}
{self._get_archetype_rules(archetype, profile.isc_score)}

## Forbidden Patterns
{self._format_blacklist(blacklist)}

## ISC Rules
{self._format_isc_rules(profile.isc_score, archetype)}

## Output Format
Return ONLY the post body. No metadata, no titles, no explanations."""

        # Build user message
        user = f"""Create a {archetype} post about: {user_context}

Match the community's natural tone and rhythm. Avoid forbidden patterns."""

        return PromptTemplate(system=system, user=user)

    def _get_archetype_rules(self, archetype: str, isc_score: float) -> str:
        """Archetype-specific generation rules"""
        rules = {
            "Journey": """Journey archetype: Share a personal discovery story.
- Start with the problem you faced
- Describe your search for solutions
- Reveal what you found (can mention your product naturally)
- End with results or current status""",

            "ProblemSolution": """Problem/Solution archetype: Focus on the problem first.
- Define the problem clearly (2-3 paragraphs)
- Explain why existing solutions don't work
- Introduce your solution briefly
- Show results or ask for feedback""",

            "Feedback": """Feedback archetype: Ask for genuine feedback.
- Explain what you're building and why
- Share what you've tried or learned
- Ask specific questions
- Be vulnerable and open to criticism"""
        }

        base_rule = rules.get(archetype, "")

        # High ISC = extra constraints
        if isc_score > 7.5 and archetype == "Feedback":
            base_rule += "\n\nCRITICAL (High ISC):\n- ZERO links\n- Maximum vulnerability (personal pronouns, emotions)\n- No marketing language"

        return base_rule

    def _format_blacklist(self, blacklist: List[Dict]) -> str:
        """Format blacklist patterns by category"""
        if not blacklist:
            return "No specific forbidden patterns detected"

        categories = {}
        for item in blacklist:
            cat = item.get("category", "Other")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item["pattern_description"])

        output = []
        for cat, patterns in categories.items():
            output.append(f"\n{cat}:")
            output.extend([f"  - Avoid {p}" for p in patterns[:3]])  # Limit to avoid token bloat

        return "\n".join(output)

    def _format_isc_rules(self, isc_score: float, archetype: str) -> str:
        """ISC-based constraints"""
        if isc_score <= 5.0:
            return "Standard authenticity. Moderate promotional language acceptable."
        elif isc_score <= 7.5:
            return "High authenticity required. Minimize promotional language."
        else:
            return "EXTREME authenticity required. Zero promotional language. Maximum vulnerability."
```

### Full-Page Draft Editor with Sidebar
```tsx
// Source: Synthesized from user requirements
"use client";

import { useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ISCGauge } from "@/components/analysis/ISCGauge";
import { CopyButton } from "@/components/drafts/CopyButton";

interface DraftEditorProps {
  draft: {
    id: string;
    body: string;
    vulnerability_score: number;
    rhythm_match_score: number;
    metadata: Record<string, any>;
  };
  onApprove: () => void;
  onDiscard: () => void;
  onRegenerate: (feedback?: string) => void;
}

export function DraftEditor({ draft, onApprove, onDiscard, onRegenerate }: DraftEditorProps) {
  const [editedBody, setEditedBody] = useState(draft.body);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState("");

  return (
    <div className="grid grid-cols-[1fr_320px] gap-6 h-screen">
      {/* Left: Draft editor */}
      <div className="flex flex-col p-6">
        <h1 className="text-2xl font-bold mb-4">Draft Editor</h1>

        <Textarea
          value={editedBody}
          onChange={(e) => setEditedBody(e.target.value)}
          className="flex-1 font-mono text-sm"
          placeholder="Draft content..."
        />

        <p className="text-xs text-muted-foreground mt-2">
          Note: Scores reflect the generated draft only. Editing is free-form with no re-scoring.
        </p>
      </div>

      {/* Right: Sidebar with scores and actions */}
      <div className="border-l bg-muted/30 p-6 flex flex-col gap-6">
        <div>
          <h2 className="text-lg font-semibold mb-4">Scores</h2>

          {/* Vulnerability Score Gauge */}
          <div className="mb-6">
            <h3 className="text-sm font-medium mb-2">Vulnerability</h3>
            <ISCGauge
              score={draft.vulnerability_score}
              tier={getVulnerabilityTier(draft.vulnerability_score)}
            />
          </div>

          {/* Rhythm Match Score Gauge */}
          <div>
            <h3 className="text-sm font-medium mb-2">Rhythm Match</h3>
            <ISCGauge
              score={draft.rhythm_match_score}
              tier={getRhythmTier(draft.rhythm_match_score)}
            />
          </div>
        </div>

        <Separator />

        {/* Metadata */}
        <div className="text-xs text-muted-foreground space-y-1">
          <div>Model: {draft.metadata.model_used}</div>
          <div>Tokens: ~{draft.metadata.token_cost}</div>
          <div>Generated: {new Date(draft.metadata.created_at).toLocaleString()}</div>
        </div>

        <Separator />

        {/* Actions */}
        <div className="flex flex-col gap-3">
          <Button onClick={onApprove} variant="default" size="lg">
            Approve
          </Button>

          <CopyButton text={editedBody} />

          <Button
            onClick={() => setShowFeedback(!showFeedback)}
            variant="outline"
          >
            Regenerate
          </Button>

          {showFeedback && (
            <div className="space-y-2">
              <Textarea
                placeholder="Optional: Provide feedback for regeneration..."
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                className="min-h-[80px]"
              />
              <Button
                onClick={() => {
                  onRegenerate(feedback);
                  setShowFeedback(false);
                  setFeedback("");
                }}
                size="sm"
                className="w-full"
              >
                Generate New Version
              </Button>
            </div>
          )}

          <Button onClick={onDiscard} variant="destructive" size="sm">
            Discard
          </Button>
        </div>
      </div>
    </div>
  );
}

function getVulnerabilityTier(score: number): string {
  if (score >= 8) return "Very High";
  if (score >= 6) return "High";
  if (score >= 4) return "Moderate";
  return "Low";
}

function getRhythmTier(score: number): string {
  if (score >= 8) return "Excellent Match";
  if (score >= 6) return "Good Match";
  if (score >= 4) return "Fair Match";
  return "Poor Match";
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| LangChain for all LLM tasks | Direct SDK for simple use cases | 2024-2025 | LangChain adds complexity for single-provider scenarios; direct SDK is simpler |
| react-hot-toast | Sonner for shadcn/ui | 2023-2024 | Sonner designed for shadcn/ui, better animations, promise-based API |
| document.execCommand("copy") | navigator.clipboard API | 2020-2022 | Modern API is async, more secure, better error handling |
| Multi-step wizards for forms | Single-page forms with progressive disclosure | 2023-2025 | Single-page forms have 14% higher completion rates for 3-5 fields |
| Client-side prompt templating | Server-side dynamic prompt building | 2024-2025 | Server-side allows profile data integration, blacklist enforcement, versioning |

**Deprecated/outdated:**
- **LangChain streaming for simple cases:** Adds abstraction overhead; direct OpenAI/Anthropic SDK is sufficient for single-provider use
- **react-copy-to-clipboard:** Native Clipboard API now has universal browser support
- **Formik for new projects:** React Hook Form has better TypeScript support, smaller bundle, better DX
- **Global state for form data:** React Hook Form's local state is sufficient for single-page forms

## Open Questions

1. **LLM Provider Choice (OpenAI vs Anthropic)**
   - What we know: Both have streaming APIs and Python SDKs; OpenAI has more market share, Anthropic has longer context windows
   - What's unclear: Which provider produces better Reddit-style drafts; cost comparison for typical use case; rate limit differences
   - Recommendation: Start with OpenAI GPT-4 (more documented, larger community); evaluate Anthropic Claude for comparison; allow provider switching in config

2. **Blacklist Enforcement Strategy**
   - What we know: Prompt instructions reduce violations but don't eliminate them; post-generation validation catches violations
   - What's unclear: Optimal balance between prompt instructions vs post-validation; whether to auto-regenerate or warn user; how to handle edge cases
   - Recommendation: Hybrid approach: include blacklist in prompt + post-validation check; if violations found, show warning with option to regenerate or edit manually

3. **Draft Text Editor Component**
   - What we know: User decision is free-form editing with no re-scoring; plain textarea is sufficient
   - What's unclear: Whether rich formatting (bold, italic, lists) improves UX; whether markdown preview adds value
   - Recommendation: Start with plain textarea (simpler, faster); monitor user feedback; consider rich editor only if users request formatting features

4. **Monthly Plan Limits Implementation**
   - What we know: GENR-09 requires monthly draft limits per tier; need to track usage
   - What's unclear: Exact limits per tier; whether to hard-block or soft-warn when approaching limit; how to handle limit resets
   - Recommendation: Store draft count per user per month; implement soft warning at 80% of limit, hard block at 100%; reset counters on first of month; show usage in dashboard

5. **Stage Indicator Visual Design**
   - What we know: Claude's discretion for visual design; user requirement is linear progression with per-campaign indicators
   - What's unclear: Best visual pattern (stepper, badges, progress dots); mobile responsiveness; accessibility
   - Recommendation: Use badge-style indicator with check icons for completed stages; horizontal layout on desktop, vertical on mobile; ensure keyboard navigation and screen reader support

## Sources

### Primary (HIGH confidence)
- [OpenAI API Prompt Engineering Guide](https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering-with-the-openai-api) - Official best practices
- [Anthropic Claude Prompt Engineering](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview) - Official Claude docs
- [OpenAI Python SDK Streaming](https://platform.openai.com/docs/api-reference/chat-streaming) - Official streaming API reference
- [React Hook Form Official Docs](https://react-hook-form.com/) - Form validation patterns
- [shadcn/ui React Hook Form](https://ui.shadcn.com/docs/forms/react-hook-form) - Integration guide
- [shadcn/ui Sonner](https://ui.shadcn.com/docs/components/radix/sonner) - Toast component
- [Navigator Clipboard API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/Clipboard/writeText) - Official browser API

### Secondary (MEDIUM confidence)
- [FastAPI OpenAI Streaming Guide (Medium)](https://medium.com/@shudongai/building-a-real-time-streaming-api-with-fastapi-and-openai-a-comprehensive-guide-cb65b3e686a5) - Implementation patterns
- [Scalable Streaming with FastAPI (Medium)](https://medium.com/@mayvic/scalable-streaming-of-openai-model-responses-with-fastapi-and-asyncio-714744b13dd) - AsyncIO patterns
- [Self-Refine: Iterative LLM Refinement](https://selfrefine.info/) - Research on feedback-based regeneration
- [Multi-Step vs Single Page Forms (WeWeb)](https://www.weweb.io/blog/multi-step-form-design) - UX research
- [Multi-Step Form UX Best Practices (Growform)](https://www.growform.co/must-follow-ux-best-practices-when-designing-a-multi-step-form/) - Conversion data
- [Next.js Clipboard Copy (Sniplates)](https://sniplates.nakobase.com/en/recipes/next-js/copy-to-clipboard) - Implementation examples

### Tertiary (LOW confidence)
- [LLM Security Risks 2026 (Sombra)](https://sombrainc.com/blog/llm-security-risks-2026) - Prompt injection, blacklist limitations
- [LLM Guardrails Best Practices (Datadog)](https://www.datadoghq.com/blog/llm-guardrails-best-practices/) - Content moderation patterns
- [React Autosave Form Examples (GitHub)](https://github.com/gayashan4lk/react-autosave-form) - Community implementations

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - OpenAI SDK, FastAPI StreamingResponse, React Hook Form, Sonner verified from official docs
- Architecture: MEDIUM - Patterns synthesized from official docs + community best practices; prompt building is custom domain logic
- Pitfalls: MEDIUM - SSE cleanup, ISC gating, blacklist validation verified from sources; token tracking and limits from experience

**Research date:** 2026-02-10
**Valid until:** 2026-03-12 (30 days - LLM APIs evolving but stable; React/Next.js patterns mature)

**Notes:**
- OpenAI/Anthropic pricing changes frequently; verify current rates before launch
- ISC gating logic is custom domain requirement; no existing patterns found (as expected)
- User constraints heavily shape architecture; research focused on HOW to implement locked decisions
- Prompt template design is art + science; will require iteration based on generated draft quality
- Monthly plan limits (GENR-09) implementation deferred to Phase 5 (billing) but tracked in drafts table from Phase 4
