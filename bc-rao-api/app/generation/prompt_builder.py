"""
Dynamic prompt construction from community profiles and blacklists.

Builds LLM prompts that inject community DNA (ISC, rhythm, formality) and
forbidden patterns to generate Reddit-native content.
"""

from typing import Optional, Dict, List


class PromptBuilder:
    """
    Build dynamic prompts from community intelligence.

    Constructs system + user prompts that include:
    - Community DNA (ISC score, formality, rhythm patterns)
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
            blacklist_patterns: Optional list of forbidden pattern dicts
            constraints: Optional list of ISC gating constraints

        Returns:
            Dict with "system" and "user" keys containing prompt text

        Examples:
            >>> builder = PromptBuilder()
            >>> prompts = builder.build_prompt("python", "Journey", "Building a web scraper")
            >>> prompts["system"]
            "You are an expert Reddit marketer..."
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

        # Format blacklist section
        blacklist_text = self._format_blacklist(blacklist_patterns or [])

        # Format ISC rules
        isc_rules = self._format_isc_rules(isc_score, archetype)

        # Format constraints from ISC gating
        constraints_text = "\n".join(f"- {c}" for c in (constraints or []))

        # Build system message
        system_msg = f"""You are an expert Reddit marketer who crafts authentic, community-native posts.

Your goal: Create a {archetype} post for r/{subreddit} that blends in naturally with the community.

## Community DNA
- ISC Score: {isc_score}/10 ({isc_tier})
- Formality level: {formality_level:.1f}/10
- Typical sentence length: {avg_sentence_length:.1f} words
- Dominant tone: {dominant_tone}

## Archetype Rules: {archetype}
{self._get_archetype_guidance(archetype, isc_score)}

## ISC Gating Constraints
{constraints_text if constraints_text else "Standard authenticity requirements apply"}

## Forbidden Patterns (NEVER use these)
{blacklist_text}

## ISC Rules
{isc_rules}

## Output Format
Return ONLY the post body text. No title, no metadata, no explanations. Write as if you are a genuine community member."""

        # Build user message
        user_msg = f"""Create a {archetype} post about: {user_context}

Match the community's natural rhythm, formality, and tone. Avoid ALL forbidden patterns."""

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

        system_msg = f"""You are an expert Reddit marketer who crafts authentic, community-native posts.

Your goal: Create a {archetype} post for r/{subreddit} that sounds genuine and helpful.

## Community DNA (Generic Defaults)
- ISC Score: {defaults["isc_score"]}/10 ({defaults["isc_tier"]})
- Formality: {defaults["formality"]}
- Rhythm: {defaults["rhythm"]}

WARNING: No community profile exists for r/{subreddit}. Using generic defaults.

## Archetype Rules: {archetype}
{self._get_archetype_guidance(archetype, defaults["isc_score"])}

## Constraints
{constraints_text}

## General Guidelines
- Be authentic and vulnerable
- Use personal pronouns (I, my, me)
- Ask questions to engage the community
- Avoid marketing jargon and excessive links
- Sound like a real person, not a brand

## Output Format
Return ONLY the post body text. No title, no metadata, no explanations. Write as if you are a genuine community member."""

        user_msg = f"""Create a {archetype} post about: {user_context}

Sound authentic and helpful. Avoid promotional language."""

        return {
            "system": system_msg,
            "user": user_msg
        }

    def _get_archetype_guidance(self, archetype: str, isc_score: float) -> str:
        """Get archetype-specific generation rules."""
        guidance = {
            "Journey": """Share a personal discovery story:
- Start with the problem you faced
- Describe your search for solutions (mention failed attempts)
- Reveal what you found (product mention emerges naturally)
- End with results or current status
- Use past tense for completed milestones, present for ongoing work
- Include specific numbers and dates""",

            "ProblemSolution": """Focus on the problem first (90% pain / 10% solution):
- NO greetings or pleasantries
- Dedicate first 2-3 paragraphs entirely to the problem
- Explain why existing solutions don't work
- Product mention ONLY in final 10% of post
- Keep solution description brief and factual
- Avoid all marketing language in problem section""",

            "Feedback": """Ask for genuine feedback (invert authority):
- Frame yourself as student, community as teacher
- Explain what you're building and why
- Share what you've tried or learned so far
- Ask specific questions about concerns or decisions
- Show vulnerability (mention uncertainties)
- Invite critique, not just praise"""
        }

        base_guidance = guidance.get(archetype, "")

        # High ISC = extra constraints
        if isc_score > 7.5 and archetype == "Feedback":
            base_guidance += "\n\nCRITICAL (High ISC):\n- ZERO links allowed\n- Maximum vulnerability (use personal pronouns extensively)\n- No marketing language whatsoever"

        return base_guidance

    def _format_blacklist(self, patterns: List[Dict]) -> str:
        """Format blacklist patterns grouped by category."""
        if not patterns:
            return "No specific forbidden patterns detected for this community"

        categories: Dict[str, List[str]] = {}

        for pattern in patterns:
            category = pattern.get("category", "Other")
            description = pattern.get("pattern_description", pattern.get("pattern", ""))

            if category not in categories:
                categories[category] = []

            categories[category].append(description)

        output = []
        for category, pattern_list in categories.items():
            output.append(f"\n{category}:")
            # Limit to 3 patterns per category to avoid token bloat
            for pattern_desc in pattern_list[:3]:
                output.append(f"  - Avoid: {pattern_desc}")

            if len(pattern_list) > 3:
                output.append(f"  - ...and {len(pattern_list) - 3} more {category} patterns")

        return "\n".join(output)

    def _format_isc_rules(self, isc_score: float, archetype: str) -> str:
        """Format ISC-based constraints."""
        if isc_score <= 3.0:
            return "Low sensitivity community. Standard promotional language acceptable."
        elif isc_score <= 5.0:
            return "Moderate sensitivity. Balance authenticity with helpful information."
        elif isc_score <= 7.5:
            return "High sensitivity. Maximize authenticity, minimize promotional language."
        else:
            rules = [
                "EXTREME sensitivity community (ISC > 7.5)",
                "Maximum vulnerability required (personal pronouns, emotions, questions)",
                "Zero promotional language allowed",
                "Focus entirely on authenticity over polish"
            ]

            if archetype == "Feedback":
                rules.append("ZERO links allowed (Feedback archetype + high ISC)")

            return "\n".join(f"- {r}" for r in rules)

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
