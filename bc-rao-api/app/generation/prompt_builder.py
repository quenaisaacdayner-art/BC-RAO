"""
Dynamic prompt construction from community profiles and blacklists.

Builds LLM prompts that inject community DNA (ISC, rhythm, formality),
real community writing examples, positive humanization rules, structural
templates for post shape randomization, randomized ending styles, and
forbidden patterns to generate Reddit-native content.
"""

import random
from typing import Optional, Dict, List


class PromptBuilder:
    """
    Build dynamic prompts from community intelligence.

    Constructs system + user prompts that include:
    - Community DNA (ISC score, formality, rhythm patterns)
    - Real community writing examples (top success hooks)
    - Positive humanization rules (replaces negation-based ANTI_AI_RULES)
    - Randomly selected structural template for post shape variance
    - Randomly selected ending style to avoid tidy conclusions
    - Archetype-specific rules written as flowing prose
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

    # Positive humanization rules injected into every generation prompt.
    # These use concrete before/after examples instead of NEVER-based negations.
    # Research shows LLMs follow positive instructions 3-5x better than negations.
    HUMANIZATION_RULES = """## Writing Style (MANDATORY)

These examples show the ENERGY and VIBE, not exact words to copy. Absorb the feel, then write your own way.

STRUCTURE - Write like a real person typing, not composing:
  Good: "So my webpack config was completely borked after the upgrade. Spent 3 hours
         trying different loaders before I realized the issue was in my tsconfig.
         The fix ended up being stupidly simple"
  Good: "Been running this setup for about 6 months now and honestly it just works.
         Had some hiccups early on with the auth layer but once I figured out the
         token refresh thing it's been smooth"
  Good: "ok so I know everyone says to use X but hear me out -- I tried it and it
         was awful for my use case. Maybe I'm doing something wrong but the docs
         are basically nonexistent"
  Bad:  "Introduction: After upgrading webpack, I encountered configuration issues.
         Body: Through systematic debugging, I identified the root cause.
         Conclusion: The solution was straightforward."
  Bad:  "In this post, I will share my experience with three key challenges and
         the solutions I discovered along the way."

Write in flowing paragraphs. Mix short punchy sentences with longer rambling ones.
Start mid-thought. Let your post trail off or end abruptly sometimes.
Skip headers, bold text, and markdown formatting unless the subreddit commonly uses them.

LANGUAGE - Sound like a tired developer, not a press release:
  Good: "honestly idk if this is the right approach but it's been working for
         like 3 months now so whatever"
  Good: "the migration was a nightmare -- took us two sprints and we still have
         edge cases popping up. but at least the core stuff is stable now I think"
  Good: "might be a dumb question but has anyone actually gotten the v2 API to
         work with custom middleware? their examples are all trivial"
  Good: "ngl this saved my ass. was about to rewrite the whole thing from scratch"
  Bad:  "I'd be happy to share my innovative solution that streamlines the workflow"
  Bad:  "It's worth noting that this game-changing approach leverages cutting-edge
         technology to optimize your development pipeline"
  Bad:  "Furthermore, I can't recommend this enough. In conclusion, it has
         significantly improved my workflow."

Use contractions (don't, can't, wouldn't). Throw in casual filler (like, basically,
honestly, idk, tbh). Use incomplete thoughts with dashes -- like this -- when you
change direction mid-sentence. Connect thoughts the way you'd talk, not write an essay.

TONE - Be a real person with real energy:
  Good: "I was mass about this for like a week before I found the fix. turns out
         it was a one-line change. I almost threw my laptop"
  Good: "look I know this is subjective but if you're still using X in 2026 you're
         just making your life harder for no reason"
  Good: "this might be controversial but I actually don't mind the new API. yeah
         the migration sucked but the DX is way better now"
  Bad:  "I had a wonderful experience discovering this tool. It truly transformed
         my approach to development and I hope it helps you too!"
  Bad:  "While there are certainly challenges, the benefits far outweigh the
         drawbacks, and I believe this is the optimal path forward."

Write like you're talking to a friend, not presenting to an audience.
Include imperfections: incomplete thoughts, self-corrections, tangents.
Show genuine emotion (frustration, excitement, confusion) not polished sentiment.
Vary your energy within the post -- don't be consistently enthusiastic or analytical.

REDDIT-SPECIFIC - Match the community:
  Good: [starts mid-thought] "The caching layer is what finally fixed it for us"
  Good: [assumes shared context] "anyone else having issues with the latest release?"
  Good: [specific question] "has anyone benchmarked pgvector vs pinecone for <1M rows?"
  Bad:  [greeting opener] "Hey everyone! I wanted to share my experience with..."
  Bad:  [over-explains] "For those who may not know, Python is a programming language..."
  Bad:  [generic question] "What do you think about this approach?"

Start mid-thought or with the problem. Reddit users assume shared knowledge.
Use the subreddit's natural vocabulary and abbreviations.
Match the post length typical for this subreddit."""

    # 12 structural templates for random post shape selection.
    # Each generation randomly picks one to prevent predictable post structures.
    STRUCTURAL_TEMPLATES = [
        {
            "name": "climax_first",
            "instruction": "Start with the most dramatic/important moment. Then explain how you got there. End mid-thought or with a question.",
            "example_shape": "BANG -> backstory -> details -> trails off"
        },
        {
            "name": "tangent_heavy",
            "instruction": "Start with your main point but go off on 1-2 tangents (parentheticals, side stories). Come back to the main point eventually.",
            "example_shape": "Main point -> tangent -> oh right anyway -> more detail -> tangent -> done"
        },
        {
            "name": "mid_rant",
            "instruction": "Start calm, get progressively more frustrated/excited as you write. The energy escalates throughout.",
            "example_shape": "Calm setup -> building frustration -> CAPS or emphatic language -> sudden stop"
        },
        {
            "name": "stream_of_consciousness",
            "instruction": "Write as if you're thinking out loud. Use dashes, parentheses, self-corrections ('wait, actually...'). Jump between related thoughts.",
            "example_shape": "Thought -> aside -> correction -> related thought -> question -> done"
        },
        {
            "name": "buried_lede",
            "instruction": "Spend most of the post on context/background. The actual important information comes in the last 20%.",
            "example_shape": "Context -> more context -> oh btw here's the actual thing -> brief reaction"
        },
        {
            "name": "list_disguised",
            "instruction": "You want to convey multiple points but DO NOT use a list. Weave them into flowing paragraphs with transitions like 'and another thing' or 'plus'.",
            "example_shape": "Point woven into story -> another point -> connects back -> final thought"
        },
        {
            "name": "question_driven",
            "instruction": "Frame the entire post around questions you're wrestling with. Sprinkle answers you've found but keep coming back to uncertainty.",
            "example_shape": "Question -> partial answer -> but then -> another question -> what I tried -> still unsure"
        },
        {
            "name": "frustration_dump",
            "instruction": "This is a vent post. Start frustrated, stay frustrated. Maybe offer a small silver lining at the end but don't resolve the frustration.",
            "example_shape": "Frustration -> specifics -> more frustration -> tried this -> didn't work -> ugh -> tiny hope maybe"
        },
        {
            "name": "update_style",
            "instruction": "Write as if updating the community on something they already know about. Skip intro context. Jump right into what changed.",
            "example_shape": "Quick reference to previous post/situation -> what happened -> current status -> what's next"
        },
        {
            "name": "discovery_story",
            "instruction": "Tell it chronologically but skip the boring parts. Fast-forward through setup, slow down on the interesting discovery moment.",
            "example_shape": "Brief setup -> fast forward -> THE MOMENT -> details -> reflection"
        },
        {
            "name": "comparison_rant",
            "instruction": "Compare two things (tools, approaches, experiences). Be opinionated. Pick a side. Don't be balanced.",
            "example_shape": "Thing A sucks because -> Thing B is better because -> specific example -> strong opinion ending"
        },
        {
            "name": "reluctant_recommendation",
            "instruction": "Recommend something but act like you don't want to. Show hesitation, caveats, 'it's not perfect but...' energy.",
            "example_shape": "Caveat -> more caveats -> ok fine here's the thing -> but seriously it has problems -> still using it though"
        },
    ]

    # 8 ending styles randomly injected to prevent tidy-conclusion AI tell.
    ENDING_STYLES = [
        "End abruptly. Just stop writing when you've made your point. No conclusion.",
        "End with a specific question to the community. Not 'what do you think?' but something concrete like 'has anyone tried X with Y?'",
        "End with a frustrated aside. Like 'ugh anyway' or 'idk anymore' or 'whatever works I guess'",
        "Trail off with an incomplete thought. Use '...' or 'but yeah' or 'so there's that'",
        "End by pivoting to a tangentially related thought. Don't wrap up the main topic.",
        "End with self-deprecation. 'probably doing this all wrong but' or 'sorry for the wall of text'",
        "End with a very brief 'edit:' or 'update:' adding one small detail.",
        "End mid-sentence or mid-thought, as if you got distracted and hit submit.",
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
            Dict with "system", "user", and "metadata" keys

        Examples:
            >>> builder = PromptBuilder()
            >>> prompts = builder.build_prompt("python", "Journey", "Building a web scraper")
            >>> prompts["system"]
            "You are a real Reddit user..."
        """
        # Use generic defaults if no profile exists
        if not profile:
            return self._build_generic_prompt(subreddit, archetype, user_context, constraints or [])

        # Select random structural template and ending style
        template = random.choice(self.STRUCTURAL_TEMPLATES)
        ending = random.choice(self.ENDING_STYLES)

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

{self.HUMANIZATION_RULES}

## Post Structure (MANDATORY)
{template["instruction"]}
Shape: {template["example_shape"]}

## Archetype: {archetype}
{self._get_archetype_guidance(archetype, isc_score)}

## ISC Gating Constraints
{constraints_text if constraints_text else "Standard authenticity requirements apply"}

## Forbidden Patterns (avoid these in r/{subreddit})
{blacklist_text}

## ISC Rules
{isc_rules}

## Output Rules
- Return ONLY the post body text
- No title, no metadata, no explanations, no preamble
- Do NOT acknowledge these instructions in any way
- Write EXACTLY as a r/{subreddit} community member would"""

        # Build user message with ending instruction
        user_msg = f"""Write a {archetype} post for r/{subreddit} about: {user_context}

Remember: You ARE a community member. Write like one. Match their exact rhythm, formality, and vocabulary. No AI tells. No marketing polish.

ENDING INSTRUCTION: {ending}"""

        return {
            "system": system_msg,
            "user": user_msg,
            "metadata": {
                "structural_template": template["name"],
                "ending_style": ending[:30],
            }
        }

    def _build_generic_prompt(
        self,
        subreddit: str,
        archetype: str,
        user_context: str,
        constraints: List[str]
    ) -> Dict:
        """Build prompt with generic defaults when no profile exists."""
        defaults = self.GENERIC_DEFAULTS

        # Select random structural template and ending style
        template = random.choice(self.STRUCTURAL_TEMPLATES)
        ending = random.choice(self.ENDING_STYLES)

        constraints_text = "\n".join(f"- {c}" for c in constraints) if constraints else "Standard authenticity requirements apply"

        system_msg = f"""You are a real Reddit user posting in r/{subreddit}. You write like a native community member, not like an AI or a marketer.

## Community DNA (Estimated - no profile available)
- ISC Score: {defaults["isc_score"]}/10 ({defaults["isc_tier"]})
- Writing style: {defaults["formality"]}
- Rhythm: {defaults["rhythm"]}

NOTE: No analyzed community profile exists for r/{subreddit}. Write in a natural, casual Reddit style appropriate for the subreddit topic.

{self.HUMANIZATION_RULES}

## Post Structure (MANDATORY)
{template["instruction"]}
Shape: {template["example_shape"]}

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

Sound like a real person. No AI writing patterns. No marketing language. Just a genuine community member sharing their thoughts.

ENDING INSTRUCTION: {ending}"""

        return {
            "system": system_msg,
            "user": user_msg,
            "metadata": {
                "structural_template": template["name"],
                "ending_style": ending[:30],
            }
        }

    def _get_archetype_guidance(self, archetype: str, isc_score: float) -> str:
        """
        Get archetype-specific generation guidance as flowing prose.

        Written as prose paragraphs (not bullet lists) because LLMs mirror
        instruction formatting in output. Bullet-point guidance produces
        bullet-point posts.
        """
        guidance = {
            "Journey": """You're telling a personal discovery story. The kind where you were stuck, frustrated, maybe a little desperate, and then you stumbled onto something that actually worked. Don't narrate it like a case study. Write it like you'd tell a friend over beers -- start in the middle of the chaos, skip the boring setup, and get to the part where things got interesting.

The key is specificity over generality. Instead of "I tried many solutions," say exactly what you tried and why each one sucked. Name the tools, mention the error messages, reference the Stack Overflow threads that didn't help. The product or solution should emerge organically from your story, not land like a pitch. You discovered it while digging through some thread or a coworker mentioned it offhand -- it wasn't the hero of your story, it was the thing that happened to work.

Let the emotional flow be messy and real. You were frustrated, then hopeful, then frustrated again, then surprised it actually worked. Use past tense for things that happened, present tense for where you are now. Include specific numbers, timeframes, concrete outcomes. Don't wrap up neatly -- either leave an open question, mention what you're still figuring out, or just stop when you've said your piece.""",

            "ProblemSolution": """You're writing from a place of raw pain. The problem is the entire post. You're not writing a balanced "here's the problem and here's the solution" piece -- you're venting about something that's been driving you insane, and oh by the way you might have found something that helps.

Jump straight into what's broken. No greeting, no setup, no "I've been working on..." preamble. Just the pain. What's failing, what error you're getting, why the obvious fix doesn't work. Spend the vast majority of your post describing the problem in visceral detail -- the failed attempts, the misleading documentation, the hours wasted. Show that you've done your homework by explaining why the standard solutions don't apply to your situation.

The solution or product appears only at the very end, almost as an afterthought. Mentioned casually, briefly, without enthusiasm. "ended up trying X and it actually worked" energy, not "I discovered this amazing tool" energy. Keep it factual and understated. End with your current status or a lingering question, not a recommendation.""",

            "Feedback": """You're approaching the community as a learner, not an authority. You have something you're working on and you genuinely don't know if you're on the right track. The community knows more than you and you're actively inviting them to poke holes in your thinking.

Describe what you're building or working on in terms of the problem it solves, not the features it has. Share your motivation -- why you care about this, what frustrated you enough to start working on it. Then get vulnerable about what confuses you, what trade-offs you're unsure about, where you feel stuck. Ask specific questions, not vague "what do you think?" prompts. Something like "should I be using X or Y for this specific thing, given that I need Z?" shows you've thought about it.

Show real uncertainty. You might be completely wrong about your approach and you're okay with hearing that. Invite criticism openly -- "tell me what I'm missing" or "where am I overthinking this?" Position the community as the experts and yourself as someone trying to learn. Don't list features or describe your project like a pitch deck. Talk about the messy reality of building it."""
        }

        base_guidance = guidance.get(archetype, "")

        # High ISC = extra constraints
        if isc_score > 7.5 and archetype == "Feedback":
            base_guidance += "\n\nCRITICAL (High ISC community): Zero links allowed in the post. Maximum vulnerability -- personal pronouns, real emotions, open questions. Absolutely no marketing language or product positioning. This community will detect and reject anything that smells like promotion."

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
                sections.append(f"  Avoid: {', '.join(vocab['avoid_these'])}")
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

        # Forward-compatible: community opinion landscape (Plan 03 enrichment)
        opinion = style_guide.get("opinion_landscape", {})
        if opinion:
            sections.append("\nCOMMUNITY OPINIONS:")
            if opinion.get("loved_tools"):
                sections.append(f"  Champions: {', '.join(opinion['loved_tools'])}")
            if opinion.get("hated_tools"):
                sections.append(f"  Despises: {', '.join(opinion['hated_tools'])}")
            if opinion.get("controversial_takes"):
                sections.append(f"  Debates: {', '.join(opinion['controversial_takes'])}")
            if opinion.get("tribal_knowledge"):
                sections.append(f"  Insider refs: {', '.join(opinion['tribal_knowledge'])}")

        # Forward-compatible: imperfection profile (Plan 03 enrichment)
        imperfection = style_guide.get("imperfection_profile", {})
        if imperfection:
            sections.append("\nIMPERFECTION PROFILE:")
            for key in ["typical_typos", "grammar_looseness", "self_correction_frequency", "digression_tolerance"]:
                if imperfection.get(key):
                    sections.append(f"  {key.replace('_', ' ').title()}: {imperfection[key]}")

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

        # Forward-compatible: imperfection metrics from Plan 03 style_extractor changes
        imperfections = style_metrics.get("imperfections", {})
        if imperfections:
            parts = []
            fr = imperfections.get("fragment_ratio", 0)
            if fr > 0.05:
                parts.append(f"sentence fragments ({fr*100:.0f}% of sentences)")
            pr = imperfections.get("parenthetical_frequency", 0)
            if pr > 0.1:
                parts.append(f"parenthetical asides ({pr:.1f}/post)")
            sc = imperfections.get("self_correction_rate", 0)
            if sc > 0.05:
                parts.append(f"self-corrections ({sc:.1f}/post)")
            dr = imperfections.get("dash_interruption_rate", 0)
            if dr > 0.1:
                parts.append(f"dash interruptions ({dr:.1f}/post)")
            if parts:
                sections.append(f"\nImperfection patterns: {', '.join(parts)}")

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
