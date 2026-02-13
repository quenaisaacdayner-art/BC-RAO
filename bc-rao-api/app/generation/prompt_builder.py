"""
Dynamic prompt construction from community profiles and blacklists.

Uses few-shot imitation instead of instruction-heavy approach.
The LLM sees FULL real Reddit posts as examples and mimics their style,
rather than receiving pages of meta-instructions about how to write.

Key insight: LLMs learn by IMITATION, not by instruction.
Showing 2-3 real posts teaches style better than 100 lines of rules.
"""

import random
from typing import Optional, Dict, List


class PromptBuilder:
    """
    Build dynamic prompts from community intelligence.

    Uses few-shot learning: system prompt defines persona + shows real
    community posts as examples. The LLM mimics what it SEES rather
    than following abstract writing instructions.
    """

    # Generic defaults for subreddits without community profiles
    GENERIC_DEFAULTS = {
        "isc_score": 5.0,
        "isc_tier": "Moderate Sensitivity",
        "formality": "Casual but clear",
        "rhythm": "Mixed sentence lengths, conversational tone",
        "avg_sentence_length": 15.0,
    }

    # Curated real Reddit posts for few-shot learning when no community
    # examples are available. These teach the LLM Reddit voice by SHOWING
    # it, not by describing it. Each is a different archetype and style.
    FALLBACK_FEW_SHOT_EXAMPLES = [
        # Journey-style: messy, specific, trails off
        """been mass about this for like two weeks so figured id post. we were running our entire auth through a custom middleware stack that I wrote when we first started (bad idea in retrospect). worked fine for like 8 months but then we started hitting these random 401s in production that we couldn't reproduce locally.

spent probably 30 hours total debugging this. checked token expiry, checked the refresh logic, even rewrote the session store. nothing. turns out our load balancer was stripping a custom header on like 1 in 50 requests and the middleware was silently failing instead of throwing -- because I wrote the error handling at 2am apparently.

switched to using the framework's built-in auth module and the whole thing just... works now. lost two sprints to something I could've avoided by not rolling my own crypto (metaphorically). still kinda pissed about it tbh""",

        # ProblemSolution-style: frustrated, raw, specific
        """ok can someone explain why the postgres connection pooling in production just decides to stop working every ~72 hours. I've tried pgbouncer, I've tried the built-in pool, I've tried setting idle timeouts, max connections, everything in the docs.

the logs just show "connection refused" and then 5 minutes later everything's fine again. no crash, no OOM, no disk issues. our monitoring shows zero anomalies during these windows.

running pg 16.2 on a 4vcpu/16gb instance, ~200 concurrent connections peak, using transaction mode pooling. I know someone's gonna say "just restart pgbouncer" and yes that works but that's not a fix that's a bandaid

has anyone actually solved this or do we all just pretend it doesn't happen""",

        # Feedback-style: uncertain, vulnerable, asking
        """so I've been building this thing on weekends for the last 3 months and I honestly have no idea if I'm overcomplicating it or if this is the right approach.

basically it's a CLI tool that watches your test files and reruns only the affected tests when you save. I know pytest-watch exists but it reruns everything which is slow af when you have 2k+ tests. mine uses the AST to figure out which tests depend on the file you changed.

the part I'm unsure about is the dependency tracking. right now I'm walking the import graph at startup which takes like 4 seconds on our monorepo. I could cache it but then I need to invalidate the cache when imports change and that feels like I'm building a build system at that point

am I overthinking this or is there a simpler way to do selective test rerunning that I'm missing""",
    ]

    def build_prompt(
        self,
        subreddit: str,
        archetype: str,
        user_context: str,
        profile: Optional[Dict] = None,
        blacklist_patterns: Optional[List[Dict]] = None,
        constraints: Optional[List[str]] = None,
    ) -> Dict:
        """
        Build system + user prompts from community profile.

        Uses few-shot imitation: injects 2-3 real community posts as
        examples the LLM should match in voice and style.

        Args:
            subreddit: Target subreddit name
            archetype: Archetype type (Journey, ProblemSolution, Feedback)
            user_context: User's context/topic for the draft
            profile: Optional community profile dict
            blacklist_patterns: Optional list of forbidden pattern dicts
            constraints: Optional list of ISC gating constraints

        Returns:
            Dict with "system", "user", and "metadata" keys
        """
        if not profile:
            return self._build_generic_prompt(subreddit, archetype, user_context, constraints or [])

        # Extract profile data
        isc_score = profile.get("isc_score", 5.0)
        formality_level = profile.get("formality_level", 5.0)
        avg_sentence_length = profile.get("avg_sentence_length", 15.0)
        dominant_tone = profile.get("dominant_tone", "neutral")

        # Get community-specific examples (full posts or fallback)
        few_shot_block = self._build_few_shot_block(profile)

        # Get style guide (LLM-generated community voice description)
        style_guide_text = self._format_style_guide(profile.get("style_guide", {}))

        # Format blacklist
        blacklist_text = self._format_blacklist(blacklist_patterns or [])

        # ISC rules
        isc_rules = self._format_isc_rules(isc_score, archetype)

        # Constraints
        constraints_text = "\n".join(f"- {c}" for c in (constraints or []))

        # Formality and rhythm descriptions
        formality_desc = self._describe_formality(formality_level)

        # Build SIMPLE system prompt — persona + examples, minimal instructions
        system_msg = f"""You are a person who posts on r/{subreddit}. You have posted there many times. Write exactly like these example posts from the community:

{few_shot_block}

{style_guide_text}

Community profile: {formality_desc}. Mood: {dominant_tone}. Avg ~{avg_sentence_length:.0f} words per sentence.

{self._get_archetype_brief(archetype, isc_score)}

{blacklist_text}

{isc_rules}

{constraints_text}

Output the post body only. No title, no meta-commentary, no preamble."""

        # Build user message — keep it SHORT
        user_msg = f"""Topic for r/{subreddit}: {user_context}

Write it as a {archetype} post. Match the voice and style of the examples above exactly."""

        return {
            "system": system_msg,
            "user": user_msg,
            "metadata": {
                "approach": "few-shot-imitation",
            }
        }

    def _build_generic_prompt(
        self,
        subreddit: str,
        archetype: str,
        user_context: str,
        constraints: List[str],
    ) -> Dict:
        """Build prompt with generic defaults when no profile exists."""
        defaults = self.GENERIC_DEFAULTS
        constraints_text = "\n".join(f"- {c}" for c in constraints) if constraints else ""

        # Use fallback few-shot examples
        examples = random.sample(self.FALLBACK_FEW_SHOT_EXAMPLES, 2)
        few_shot_block = "\n\n---\n\n".join(
            f"EXAMPLE POST:\n{ex}" for ex in examples
        )

        system_msg = f"""You are a person who posts on r/{subreddit}. Write exactly like these example Reddit posts in tone, structure, and voice:

{few_shot_block}

---

Community style: {defaults["formality"]}. {defaults["rhythm"]}.

{self._get_archetype_brief(archetype, defaults["isc_score"])}

{constraints_text}

Output the post body only. No title, no meta-commentary, no preamble."""

        user_msg = f"""Topic for r/{subreddit}: {user_context}

Write it as a {archetype} post. Match the voice and style of the examples above exactly."""

        return {
            "system": system_msg,
            "user": user_msg,
            "metadata": {
                "approach": "few-shot-imitation-generic",
            }
        }

    def _build_few_shot_block(self, profile: Dict) -> str:
        """
        Build few-shot examples block from community data.

        Priority order:
        1. Full post bodies from top_success_hooks (if they contain full posts)
        2. Style guide example posts (if style_guide has examples)
        3. Fallback curated examples

        The LLM learns by SEEING real posts, not by reading rules.
        """
        # Try to use community hooks as examples
        hooks = profile.get("top_success_hooks", [])

        # Style metrics may have real post examples
        style_metrics = profile.get("style_metrics", {})
        community_posts = style_metrics.get("example_posts", [])

        examples = []

        # Use community posts if available (full text)
        if community_posts:
            for post in community_posts[:3]:
                if isinstance(post, str) and len(post) > 50:
                    examples.append(post)
                elif isinstance(post, dict) and post.get("text") and len(post["text"]) > 50:
                    examples.append(post["text"])

        # If we have hooks (even partial), show them as examples
        if hooks and len(examples) < 2:
            for hook in hooks[:3]:
                if hook and len(hook.strip()) > 30:
                    examples.append(hook.strip())

        # Pad with fallback examples if needed
        if len(examples) < 2:
            needed = 2 - len(examples)
            fallbacks = random.sample(self.FALLBACK_FEW_SHOT_EXAMPLES, min(needed, 3))
            examples.extend(fallbacks)

        # Format as few-shot block
        parts = []
        for i, ex in enumerate(examples[:3], 1):
            parts.append(f"EXAMPLE POST {i}:\n{ex}")

        return "\n\n---\n\n".join(parts)

    def _get_archetype_brief(self, archetype: str, isc_score: float) -> str:
        """
        Get brief archetype guidance.

        Much shorter than before — the few-shot examples carry most of
        the style information. This just nudges the content framing.
        """
        briefs = {
            "Journey": "Frame: You discovered something through struggle. Start in the middle of the problem, be specific about what failed, mention the solution casually near the end. No neat wrap-up.",

            "ProblemSolution": "Frame: You're frustrated about a problem. 90% raw pain (specifics, failed attempts, exact errors). The solution appears only at the very end, mentioned casually as 'ended up trying X and it worked'.",

            "Feedback": "Frame: You built something and genuinely don't know if you're doing it right. Be vulnerable. Ask specific questions. Position the community as experts and yourself as a learner.",
        }

        brief = briefs.get(archetype, "")

        if isc_score > 7.5 and archetype == "Feedback":
            brief += " CRITICAL: Zero links. Maximum vulnerability. This community will detect and reject anything promotional."

        return brief

    def _format_blacklist(self, patterns: List[Dict]) -> str:
        """Format blacklist patterns, kept minimal to avoid prompt bloat."""
        if not patterns:
            return ""

        descriptions = []
        for pattern in patterns[:8]:
            desc = pattern.get("pattern_description", pattern.get("pattern", ""))
            if desc:
                descriptions.append(desc)

        if not descriptions:
            return ""

        return "Avoid: " + ", ".join(descriptions)

    def _format_isc_rules(self, isc_score: float, archetype: str) -> str:
        """Format ISC-based constraints — kept brief."""
        if isc_score <= 5.0:
            return ""
        elif isc_score <= 7.5:
            return "This community is suspicious of marketing. Be authentic above all."
        else:
            text = "EXTREME sensitivity community. Zero promotional language. Maximum vulnerability and authenticity."
            if archetype == "Feedback":
                text += " Zero links allowed."
            return text

    def _format_style_guide(self, style_guide: Optional[Dict]) -> str:
        """
        Format LLM-generated style guide for injection into system prompt.

        This is the community's voice fingerprint — kept as natural language
        that the LLM can absorb, not structured data it needs to interpret.
        """
        if not style_guide:
            return ""

        parts = []

        if style_guide.get("voice_description"):
            parts.append(f"Community voice: {style_guide['voice_description']}")

        vocab = style_guide.get("vocabulary_guide", {})
        if vocab.get("use_these"):
            parts.append(f"Use naturally: {', '.join(vocab['use_these'][:10])}")
        if vocab.get("avoid_these"):
            parts.append(f"Never use: {', '.join(vocab['avoid_these'][:8])}")

        if style_guide.get("emotional_tone"):
            parts.append(f"Tone: {style_guide['emotional_tone']}")

        if style_guide.get("taboo_patterns"):
            parts.append(f"Taboo: {style_guide['taboo_patterns']}")

        # Community opinions add authentic flavor
        opinion = style_guide.get("opinion_landscape", {})
        if opinion.get("loved_tools"):
            parts.append(f"Community favorites: {', '.join(opinion['loved_tools'][:5])}")
        if opinion.get("tribal_knowledge"):
            parts.append(f"Insider refs: {', '.join(opinion['tribal_knowledge'][:5])}")

        if not parts:
            return ""

        return "\n".join(parts)

    def _describe_formality(self, formality_level: Optional[float]) -> str:
        """Convert formality score to natural language description."""
        if formality_level is None:
            return "Casual"

        if formality_level < 3.0:
            return "Very casual -- slang, abbreviations, fragments"
        elif formality_level < 5.0:
            return "Casual -- conversational, contractions, relaxed"
        elif formality_level < 7.0:
            return "Moderate -- clear but not stiff"
        elif formality_level < 9.0:
            return "Formal -- structured sentences"
        else:
            return "Very formal -- academic tone"

    def _get_isc_tier(self, isc_score: float) -> str:
        """Convert ISC score to tier description."""
        if isc_score < 3:
            return "Low Sensitivity"
        elif isc_score < 5:
            return "Moderate Sensitivity"
        elif isc_score < 7:
            return "High Sensitivity"
        else:
            return "Very High Sensitivity"
