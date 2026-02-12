"""
Dynamic prompt construction from community profiles and blacklists.

Builds LLM prompts that inject community DNA (ISC, rhythm, formality),
real community writing examples, anti-AI writing rules, and
forbidden patterns to generate Reddit-native content.
"""

from typing import Optional, Dict, List


class PromptBuilder:
    """
    Build dynamic prompts from community intelligence.

    Constructs system + user prompts that include:
    - Community DNA (ISC score, formality, rhythm patterns)
    - Real community writing examples (top success hooks)
    - Anti-AI writing instructions to avoid detectable patterns
    - Archetype-specific rules
    - Forbidden patterns from syntax blacklist
    - ISC gating constraints
    """

    # Generic defaults for subreddits without community profiles
    GENERIC_DEFAULTS = {
        "isc_score": 5.0,
        "isc_tier": "Moderate Sensitivity",
        "formality": "Casual but clear",
        "rhythm": "Mixed sentence lengths, conversational tone",
        "avg_sentence_length": 15.0,
    }

    # Anti-AI writing rules injected into every generation prompt.
    # These counter the most common detectable patterns of LLM-generated text.
    ANTI_AI_RULES = """## CRITICAL: Anti-AI Writing Rules (MANDATORY)
You MUST follow ALL of these rules. Violating any of them makes the post detectable as AI-generated.

STRUCTURE:
- NEVER use bullet points or numbered lists in the post body
- NEVER use headers, bold, or markdown formatting (unless the subreddit commonly does)
- NEVER write in a 5-paragraph essay structure
- NEVER use a "hook, body, conclusion" structure
- Write in flowing paragraphs like a real person typing on Reddit

LANGUAGE:
- NEVER use these AI-telltale phrases: "I'd be happy to", "Great question", "It's worth noting",
  "In my experience", "game-changer", "I can't recommend enough", "needless to say",
  "at the end of the day", "without further ado", "in today's world", "it's important to note",
  "I've been on a journey", "to be honest", "Here's the thing", "Let me share"
- NEVER use formal transitions: "Furthermore", "Additionally", "Moreover", "In conclusion",
  "That being said", "With that in mind", "On the other hand", "It goes without saying"
- NEVER use corporate/marketing language: "leverage", "optimize", "streamline", "robust",
  "cutting-edge", "innovative", "revolutionary", "game-changing", "best-in-class", "scalable"
- NEVER start sentences with "So," as a discourse marker (AI signature)
- Use contractions naturally (don't, can't, wouldn't, I'm, it's)
- Use casual filler words occasionally (like, basically, honestly, idk, tbh, ngl)

TONE:
- Write like you're talking to a friend, not presenting to an audience
- Include imperfections: incomplete thoughts, self-corrections, tangents
- Show genuine emotion (frustration, excitement, confusion) not polished sentiment
- Vary your energy within the post (not consistently enthusiastic or analytical)
- End naturally, not with a neat bow. Real posts sometimes just... end.

REDDIT-SPECIFIC:
- Start mid-thought or with the problem, NOT with "Hey everyone!" or "Hi r/subreddit!"
- Don't over-explain context. Reddit users assume shared knowledge.
- Use the subreddit's natural vocabulary and abbreviations
- Match the post length typical for this subreddit (don't over-write)
- If asking a question, be specific, not generic"""

    def build_prompt(
        self,
        subreddit: str,
        archetype: str,
        user_context: str,
        profile: Optional[Dict] = None,
        blacklist_patterns: Optional[List[Dict]] = None,
        constraints: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Build system + user prompts from community profile.

        Args:
            subreddit: Target subreddit name
            archetype: Archetype type (Journey, ProblemSolution, Feedback)
            user_context: User's context/topic for the draft
            profile: Optional community profile dict with keys:
                - isc_score (float)
                - formality_level (float)
                - avg_sentence_length (float)
                - dominant_tone (str)
                - archetype_distribution (dict)
                - top_success_hooks (list[str])
            blacklist_patterns: Optional list of forbidden pattern dicts
            constraints: Optional list of ISC gating constraints

        Returns:
            Dict with "system" and "user" keys containing prompt text

        Examples:
            >>> builder = PromptBuilder()
            >>> prompts = builder.build_prompt("python", "Journey", "Building a web scraper")
            >>> prompts["system"]
            "You are a real Reddit user..."
        """
        # Use generic defaults if no profile exists
        if not profile:
            return self._build_generic_prompt(subreddit, archetype, user_context, constraints or [])

        # Extract profile data
        isc_score = profile.get("isc_score", 5.0)
        isc_tier = self._get_isc_tier(isc_score)
        formality_level = profile.get("formality_level", 5.0)
        avg_sentence_length = profile.get("avg_sentence_length", 15.0)
        dominant_tone = profile.get("dominant_tone", "neutral")

        # Extract qualitative data from profile
        top_success_hooks = profile.get("top_success_hooks", [])
        archetype_distribution = profile.get("archetype_distribution", {})

        # Format sections
        blacklist_text = self._format_blacklist(blacklist_patterns or [])
        isc_rules = self._format_isc_rules(isc_score, archetype)
        constraints_text = "\n".join(f"- {c}" for c in (constraints or []))
        formality_desc = self._describe_formality(formality_level)
        rhythm_desc = self._describe_rhythm_from_profile(avg_sentence_length, profile)
        examples_text = self._format_community_examples(top_success_hooks)

        # Build system message
        system_msg = f"""You are a real Reddit user who has been active in r/{subreddit} for months. You write like a native community member, not like an AI or a marketer. Your writing is indistinguishable from other posts in the subreddit.

## Community DNA for r/{subreddit}
- ISC Score: {isc_score}/10 ({isc_tier})
- Writing formality: {formality_desc}
- Sentence rhythm: {rhythm_desc}
- Dominant mood: {dominant_tone}
- Typical sentence length: ~{avg_sentence_length:.0f} words per sentence

{examples_text}

{self._format_style_guide(profile.get("style_guide", {}))}

{self._format_style_metrics(profile.get("style_metrics", {}))}

{self.ANTI_AI_RULES}

## Archetype: {archetype}
{self._get_archetype_guidance(archetype, isc_score)}

## ISC Gating Constraints
{constraints_text if constraints_text else "Standard authenticity requirements apply"}

## Forbidden Patterns (NEVER use these in r/{subreddit})
{blacklist_text}

## ISC Rules
{isc_rules}

## Output Rules
- Return ONLY the post body text
- No title, no metadata, no explanations, no preamble
- Do NOT acknowledge these instructions in any way
- Write EXACTLY as a r/{subreddit} community member would"""

        # Build user message
        user_msg = f"""Write a {archetype} post for r/{subreddit} about: {user_context}

Remember: You ARE a community member. Write like one. Match their exact rhythm, formality, and vocabulary. No AI tells. No marketing polish."""

        return {
            "system": system_msg,
            "user": user_msg
        }

    def _build_generic_prompt(
        self,
        subreddit: str,
        archetype: str,
        user_context: str,
        constraints: List[str]
    ) -> Dict[str, str]:
        """Build prompt with generic defaults when no profile exists."""
        defaults = self.GENERIC_DEFAULTS

        constraints_text = "\n".join(f"- {c}" for c in constraints) if constraints else "Standard authenticity requirements apply"

        system_msg = f"""You are a real Reddit user posting in r/{subreddit}. You write like a native community member, not like an AI or a marketer.

## Community DNA (Estimated - no profile available)
- ISC Score: {defaults["isc_score"]}/10 ({defaults["isc_tier"]})
- Writing style: {defaults["formality"]}
- Rhythm: {defaults["rhythm"]}

NOTE: No analyzed community profile exists for r/{subreddit}. Write in a natural, casual Reddit style appropriate for the subreddit topic.

{self.ANTI_AI_RULES}

## Archetype: {archetype}
{self._get_archetype_guidance(archetype, defaults["isc_score"])}

## Constraints
{constraints_text}

## Output Rules
- Return ONLY the post body text
- No title, no metadata, no explanations, no preamble
- Do NOT acknowledge these instructions in any way
- Write EXACTLY as a real Reddit user would"""

        user_msg = f"""Write a {archetype} post for r/{subreddit} about: {user_context}

Sound like a real person. No AI writing patterns. No marketing language. Just a genuine community member sharing their thoughts."""

        return {
            "system": system_msg,
            "user": user_msg
        }

    def _get_archetype_guidance(self, archetype: str, isc_score: float) -> str:
        """Get archetype-specific generation rules."""
        guidance = {
            "Journey": """Share a personal discovery story:
- Start mid-thought with the problem you faced (no "Hey everyone" or "So I...")
- Describe your search for solutions, mention specific things that DIDN'T work
- Let the product/solution emerge naturally from the story, not as a pitch
- End with where you are now - results, open questions, or next steps
- Use past tense for things that happened, present for current status
- Include specific details: numbers, timeframes, concrete outcomes
- Show the emotional arc: frustration -> searching -> discovery -> relief/progress""",

            "ProblemSolution": """Lead with raw pain, solution is an afterthought:
- Jump straight into the problem. No greetings. No setup. No "I've been struggling with..."
- Spend 90% of the post on the problem: what's broken, what you tried, why it sucks
- Explain why the obvious solutions don't work (shows you've done homework)
- The product/solution appears only in the final 10%, mentioned casually
- Keep the solution mention brief and factual, not enthusiastic
- End with your current status or a question, not a recommendation""",

            "Feedback": """Ask for genuine feedback by inverting authority:
- Position yourself as learning, the community as experts
- Explain what you're working on and WHY (the motivation, not the features)
- Share what you've tried or learned, including what confused you
- Ask SPECIFIC questions, not "what do you think?"
- Show real uncertainty: "I'm not sure if X or Y is the right approach"
- Mention what you're worried about or where you feel stuck
- Invite criticism openly: "tell me what I'm missing" or "where am I wrong here?"
- Do NOT list features. Describe the problem you're solving."""
        }

        base_guidance = guidance.get(archetype, "")

        # High ISC = extra constraints
        if isc_score > 7.5 and archetype == "Feedback":
            base_guidance += "\n\nCRITICAL (High ISC community):\n- ZERO links allowed in the post\n- Maximum vulnerability (personal pronouns, real emotions, open questions)\n- Absolutely no marketing language or product positioning"

        return base_guidance

    def _format_blacklist(self, patterns: List[Dict]) -> str:
        """Format blacklist patterns grouped by category."""
        if not patterns:
            return "No specific forbidden patterns detected for this community yet."

        categories: Dict[str, List[str]] = {}

        for pattern in patterns:
            category = pattern.get("category", "Other")
            description = pattern.get("pattern_description", pattern.get("pattern", ""))

            if category not in categories:
                categories[category] = []

            if description:
                categories[category].append(description)

        if not any(categories.values()):
            return "No specific forbidden patterns detected for this community yet."

        output = []
        for category, pattern_list in categories.items():
            if not pattern_list:
                continue
            output.append(f"\n{category}:")
            # Limit to 5 patterns per category (increased from 3 for better coverage)
            for pattern_desc in pattern_list[:5]:
                output.append(f"  - Avoid: {pattern_desc}")

            if len(pattern_list) > 5:
                output.append(f"  - ...and {len(pattern_list) - 5} more {category} patterns")

        return "\n".join(output)

    def _format_isc_rules(self, isc_score: float, archetype: str) -> str:
        """Format ISC-based constraints."""
        if isc_score <= 3.0:
            return "Low sensitivity community. You can be more direct about recommendations, but still sound like a real person."
        elif isc_score <= 5.0:
            return "Moderate sensitivity. Balance being helpful with being authentic. Don't sound like you're selling anything."
        elif isc_score <= 7.5:
            return "High sensitivity. This community is suspicious of marketing. Maximize authenticity, show vulnerability, minimize anything that sounds promotional."
        else:
            rules = [
                "EXTREME sensitivity community (ISC > 7.5) - they will detect and reject marketing",
                "Maximum vulnerability required: personal pronouns, real emotions, genuine questions",
                "Zero promotional language allowed - not even subtle product positioning",
                "Focus entirely on being a real community member, not on any agenda",
                "Show genuine uncertainty and ask for help"
            ]

            if archetype == "Feedback":
                rules.append("ZERO links allowed (high ISC + Feedback = pure text only)")

            return "\n".join(f"- {r}" for r in rules)

    def _format_community_examples(self, hooks: List[str]) -> str:
        """
        Format top success hooks as writing style examples.

        These are the opening lines from the highest-scoring posts in the
        community, giving the LLM concrete examples of how real community
        members write.
        """
        if not hooks:
            return ""

        examples = []
        for i, hook in enumerate(hooks[:5], 1):
            # Clean the hook text
            clean_hook = hook.strip()
            if clean_hook:
                examples.append(f'  {i}. "{clean_hook}"')

        if not examples:
            return ""

        examples_block = "\n".join(examples)
        return f"""## How This Community Actually Writes (Real Examples From Top Posts)
Study these opening lines from top-performing posts in this community. Match their style, tone, and energy level:
{examples_block}

These are NOT templates to copy. They show the VOICE of this community. Absorb the tone, formality, sentence structure, and vocabulary. Your post should sound like it belongs alongside these."""

    def _format_style_guide(self, style_guide: Optional[Dict]) -> str:
        """
        Format LLM-generated style guide for injection into system prompt.

        The style guide provides natural-language descriptions of the community's
        writing voice, vocabulary, formatting, and taboo patterns. This is the
        highest-impact section for humanization.
        """
        if not style_guide:
            return ""

        sections = []
        sections.append("## Community Writing Style Guide")

        if style_guide.get("voice_description"):
            sections.append(f"\nVOICE: {style_guide['voice_description']}")

        vocab = style_guide.get("vocabulary_guide", {})
        if vocab:
            sections.append("\nVOCABULARY:")
            if vocab.get("use_these"):
                sections.append(f"  Use naturally: {', '.join(vocab['use_these'])}")
            if vocab.get("avoid_these"):
                sections.append(f"  NEVER use: {', '.join(vocab['avoid_these'])}")
            if vocab.get("domain_terms"):
                sections.append(f"  Domain terms: {', '.join(vocab['domain_terms'])}")

        if style_guide.get("opening_guide"):
            sections.append(f"\nOPENINGS: {style_guide['opening_guide']}")

        if style_guide.get("closing_guide"):
            sections.append(f"\nCLOSINGS: {style_guide['closing_guide']}")

        if style_guide.get("formatting_rules"):
            sections.append(f"\nFORMATTING: {style_guide['formatting_rules']}")

        if style_guide.get("emotional_tone"):
            sections.append(f"\nEMOTIONAL REGISTER: {style_guide['emotional_tone']}")

        if style_guide.get("taboo_patterns"):
            sections.append(f"\nTABOO (instant detection as outsider): {style_guide['taboo_patterns']}")

        return "\n".join(sections)

    def _format_style_metrics(self, style_metrics: Optional[Dict]) -> str:
        """
        Format SpaCy-extracted style metrics for injection into system prompt.

        Provides concrete structural data: vocabulary frequency, punctuation habits,
        formatting conventions, and opening patterns. Supplements the LLM style guide
        with hard data.
        """
        if not style_metrics:
            return ""

        sections = []
        sections.append("## Community Style Metrics (Data-Driven)")

        vocab = style_metrics.get("vocabulary", {})
        if vocab:
            if vocab.get("top_terms"):
                terms = ", ".join(vocab["top_terms"][:15])
                sections.append(f"\nFrequent vocabulary: {terms}")
            if vocab.get("top_noun_phrases"):
                phrases = ", ".join(vocab["top_noun_phrases"][:10])
                sections.append(f"Common phrases: {phrases}")
            if vocab.get("oov_tokens"):
                slang = ", ".join(vocab["oov_tokens"][:10])
                sections.append(f"Community slang/jargon: {slang}")

        structure = style_metrics.get("structure", {})
        if structure:
            wc = structure.get("avg_post_word_count", 0)
            if wc:
                sections.append(f"\nTypical post length: ~{wc} words")
            q_ratio = structure.get("question_sentence_ratio", 0)
            if q_ratio > 0.05:
                sections.append(f"Question frequency: {q_ratio*100:.0f}% of sentences are questions")
            para = structure.get("avg_paragraph_count", 0)
            if para:
                sections.append(f"Paragraph style: ~{para:.0f} paragraphs per post")

        punct = style_metrics.get("punctuation", {})
        if punct:
            parts = []
            if punct.get("exclamation_per_post", 0) > 1.0:
                parts.append(f"exclamation marks (~{punct['exclamation_per_post']:.1f}/post)")
            if punct.get("ellipsis_per_post", 0) > 0.3:
                parts.append(f"ellipsis (~{punct['ellipsis_per_post']:.1f}/post)")
            if punct.get("emoji_per_post", 0) > 0.2:
                parts.append(f"emoji (~{punct['emoji_per_post']:.1f}/post)")
            if parts:
                sections.append(f"Punctuation habits: Uses {', '.join(parts)}")

        formatting = style_metrics.get("formatting", {})
        if formatting:
            parts = []
            if formatting.get("has_tldr_ratio", 0) > 0.1:
                sections.append(f"TL;DR usage: {formatting['has_tldr_ratio']*100:.0f}% of posts include TL;DR")
            if formatting.get("has_code_blocks_ratio", 0) > 0.05:
                parts.append("code blocks common")
            if formatting.get("has_edit_ratio", 0) > 0.05:
                parts.append("EDIT: updates common")
            if parts:
                sections.append(f"Formatting norms: {', '.join(parts)}")

        openings = style_metrics.get("openings", {})
        if openings and openings.get("top_opening_patterns"):
            patterns = openings["top_opening_patterns"][:5]
            pattern_strs = [f'"{p["pattern"]}"' for p in patterns]
            sections.append(f"\nCommon opening patterns: {', '.join(pattern_strs)}")

        # Only return if we have content beyond the header
        if len(sections) <= 1:
            return ""

        return "\n".join(sections)

    def _describe_formality(self, formality_level: Optional[float]) -> str:
        """Convert formality score to natural language description."""
        if formality_level is None:
            return "Unknown (write casually)"

        if formality_level < 3.0:
            return "Very casual - informal slang, abbreviations, sentence fragments are normal"
        elif formality_level < 5.0:
            return "Casual - conversational tone, contractions, relaxed grammar"
        elif formality_level < 7.0:
            return "Moderate - clear and readable but not stiff, some technical vocabulary"
        elif formality_level < 9.0:
            return "Formal - well-structured sentences, professional vocabulary"
        else:
            return "Very formal - academic or professional tone, complete sentences"

    def _describe_rhythm_from_profile(
        self,
        avg_sentence_length: Optional[float],
        profile: Optional[Dict] = None,
    ) -> str:
        """Describe the writing rhythm from profile metrics."""
        if avg_sentence_length is None:
            return "Mixed sentence lengths, conversational flow"

        # Determine rhythm type from sentence length
        if avg_sentence_length < 10:
            length_desc = "Short, punchy sentences"
        elif avg_sentence_length < 15:
            length_desc = "Medium-length sentences, conversational"
        elif avg_sentence_length < 20:
            length_desc = "Moderate to long sentences"
        else:
            length_desc = "Long, detailed sentences"

        return f"{length_desc} (avg ~{avg_sentence_length:.0f} words). Vary your sentence length naturally - mix short and long."

    def _describe_rhythm(self, rhythm_metadata: Optional[Dict]) -> str:
        """Summarize rhythm data from profile."""
        if not rhythm_metadata:
            return "Mixed sentence lengths, conversational tone"

        avg_length = rhythm_metadata.get("avg_sentence_length", 15.0)
        std = rhythm_metadata.get("sentence_length_std", 5.0)

        if std < 3.0:
            rhythm_type = "Consistent, uniform sentence lengths"
        elif std < 6.0:
            rhythm_type = "Moderate variation in sentence lengths"
        else:
            rhythm_type = "High variation, dynamic rhythm"

        return f"{rhythm_type} (avg: {avg_length:.1f} words)"

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
