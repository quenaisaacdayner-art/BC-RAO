"""
Deterministic post-processing transforms that make LLM output feel human.

Instead of asking the LLM to "write badly" (which fights its training),
we let it generate good content and then apply text transforms that
introduce human-like imperfections deterministically.

These transforms are based on patterns observed in real Reddit posts:
- Lowercase sentence starts (~30% of casual Reddit posts)
- Filler word injection at natural breakpoints
- Self-corrections mid-sentence
- Ellipsis and dash interruptions
- Removing overly formal punctuation
- Converting some sentences to fragments
"""

import random
import re
from typing import List, Optional


# Filler phrases that real Reddit users scatter in posts
FILLERS = [
    "honestly", "tbh", "ngl", "like", "basically", "idk",
    "imo", "fwiw", "I mean", "I guess", "lol", "lowkey",
]

# Self-correction phrases injected mid-thought
SELF_CORRECTIONS = [
    "wait actually",
    "well ok maybe not",
    "or maybe",
    "idk actually",
    "actually scratch that",
    "hmm actually",
    "-- ok well",
]

# Casual connectors that replace formal transitions
CASUAL_CONNECTORS = [
    "anyway",
    "so yeah",
    "but like",
    "and tbh",
    "oh and",
    "plus",
    "also",
    "btw",
]

# Trailing endings that real posts use instead of neat conclusions
TRAIL_OFFS = [
    "but yeah",
    "so there's that",
    "idk",
    "anyway",
    "but whatever",
    "just my 2 cents",
    "curious what others think",
    "...yeah",
]


def humanize_text(
    text: str,
    intensity: float = 0.5,
    seed: Optional[int] = None,
) -> str:
    """
    Apply deterministic human-like transforms to LLM-generated text.

    Works WITH the LLM's strengths (good content, clear thinking) and
    adds human imperfections ON TOP rather than asking the LLM to produce
    them (which fights its training).

    Args:
        text: LLM-generated post text
        intensity: How aggressively to humanize (0.0 = minimal, 1.0 = heavy)
            0.3 = light touch (formal communities)
            0.5 = moderate (default)
            0.7 = heavy (very casual communities)
        seed: Optional random seed for reproducibility in tests

    Returns:
        Humanized text with natural imperfections
    """
    if not text or not text.strip():
        return ""

    rng = random.Random(seed)

    # Apply transforms in order (each builds on previous)
    text = _strip_ai_artifacts(text)
    text = _lowercase_some_starts(text, intensity, rng)
    text = _inject_fillers(text, intensity, rng)
    text = _add_self_corrections(text, intensity, rng)
    text = _convert_formal_punctuation(text, intensity, rng)
    text = _add_casual_connectors(text, intensity, rng)
    text = _humanize_ending(text, intensity, rng)

    return text.strip()


def _strip_ai_artifacts(text: str) -> str:
    """Remove obvious AI writing artifacts that survived the prompt."""
    # Remove "In conclusion", "To summarize", etc. — both at line starts and mid-text
    # When mid-sentence (after period), remove everything from the phrase to end of sentence
    text = re.sub(
        r'[.\s]*\b(?:In conclusion|To summarize|In summary|To sum up|'
        r'All in all|The bottom line is|At the end of the day)[,:]?\s*[^.!?\n]*[.!?]?',
        '', text, flags=re.IGNORECASE
    )

    # Remove "Here's the thing:" / "Let me explain:" opener patterns
    text = re.sub(
        r'^(?:Here\'s the thing[:.!]?\s*|Let me (?:explain|share)[:.!]?\s*|'
        r'I\'d (?:like to|love to) share\s*)',
        '', text, flags=re.IGNORECASE
    )

    # Remove "Furthermore", "Moreover", "Additionally" transitions
    text = re.sub(
        r'\b(?:Furthermore|Moreover|Additionally|It\'s worth noting that|'
        r'Needless to say|That being said)\b[,]?\s*',
        '', text, flags=re.IGNORECASE
    )

    # Remove greeting openers
    text = re.sub(
        r'^(?:Hey everyone[!,.]?\s*|Hi everyone[!,.]?\s*|Hello everyone[!,.]?\s*|'
        r'Hey folks[!,.]?\s*|Hi folks[!,.]?\s*)',
        '', text, flags=re.IGNORECASE | re.MULTILINE
    )

    # Remove "I hope this helps!" / "Hope that helps!" closers
    text = re.sub(
        r'\s*(?:I )?[Hh]ope (?:this|that|it) helps[!.]?\s*$',
        '', text
    )

    return text.strip()


def _lowercase_some_starts(text: str, intensity: float, rng: random.Random) -> str:
    """Lowercase some sentence starts — real Reddit posts often skip capitalization."""
    sentences = text.split('. ')
    result = []

    for i, sentence in enumerate(sentences):
        # Never lowercase the first sentence, and apply based on intensity
        if i > 0 and sentence and sentence[0].isupper() and rng.random() < intensity * 0.4:
            sentence = sentence[0].lower() + sentence[1:]
        result.append(sentence)

    return '. '.join(result)


def _inject_fillers(text: str, intensity: float, rng: random.Random) -> str:
    """Inject casual filler words at sentence boundaries."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) < 3:
        return text

    # Pick 1-3 sentences to add fillers to, based on intensity
    num_fillers = max(1, int(len(sentences) * intensity * 0.2))
    # Don't modify first or last sentence
    candidates = list(range(1, len(sentences) - 1))

    if not candidates:
        return text

    chosen = rng.sample(candidates, min(num_fillers, len(candidates)))

    for idx in chosen:
        filler = rng.choice(FILLERS)
        sentence = sentences[idx]
        if sentence and sentence[0].islower():
            # Already lowercase, prepend filler
            sentences[idx] = f"{filler} {sentence}"
        elif sentence and sentence[0].isupper():
            # Lowercase the start and prepend filler
            sentences[idx] = f"{filler} {sentence[0].lower()}{sentence[1:]}"

    return ' '.join(sentences)


def _add_self_corrections(text: str, intensity: float, rng: random.Random) -> str:
    """Add self-correction phrases — 'wait actually', 'or maybe', etc."""
    if rng.random() > intensity * 0.6:
        return text  # Skip entirely based on intensity

    sentences = text.split('. ')
    if len(sentences) < 4:
        return text

    # Pick one sentence to add a self-correction after
    # Target the middle third of the post
    mid_start = len(sentences) // 3
    mid_end = 2 * len(sentences) // 3
    candidates = list(range(mid_start, mid_end))

    if not candidates:
        return text

    idx = rng.choice(candidates)
    correction = rng.choice(SELF_CORRECTIONS)

    # Strip trailing punctuation from the sentence before adding correction
    sent = sentences[idx].rstrip('.!?')
    sentences[idx] = f"{sent} -- {correction}"

    return '. '.join(sentences)


def _convert_formal_punctuation(text: str, intensity: float, rng: random.Random) -> str:
    """Convert some formal punctuation to casual style."""
    # Replace some semicolons with dashes or periods
    if rng.random() < intensity * 0.7:
        text = text.replace('; ', ' -- ', 1)

    # Replace some colons in non-code contexts with dashes
    # Only replace colons that aren't in code blocks or URLs
    if rng.random() < intensity * 0.5:
        text = re.sub(
            r'(?<!https)(?<!http):\s+(?![/\d])',
            ' -- ',
            text,
            count=1,
        )

    # Remove some periods at end of paragraphs (trail off)
    if rng.random() < intensity * 0.3:
        paragraphs = text.split('\n\n')
        if len(paragraphs) > 1:
            idx = rng.randint(0, len(paragraphs) - 2)
            paragraphs[idx] = paragraphs[idx].rstrip('.')
            text = '\n\n'.join(paragraphs)

    return text


def _add_casual_connectors(text: str, intensity: float, rng: random.Random) -> str:
    """Replace formal paragraph transitions with casual connectors."""
    paragraphs = text.split('\n\n')
    if len(paragraphs) < 2:
        return text

    # Only modify 1-2 paragraph starts
    num_to_modify = min(2, max(1, int(len(paragraphs) * intensity * 0.3)))
    candidates = list(range(1, len(paragraphs)))
    chosen = rng.sample(candidates, min(num_to_modify, len(candidates)))

    for idx in chosen:
        para = paragraphs[idx].strip()
        if not para:
            continue

        connector = rng.choice(CASUAL_CONNECTORS)

        # Remove formal starters if present
        para = re.sub(
            r'^(?:However|Nevertheless|Furthermore|In addition|On the other hand|'
            r'That said|Moving on|Another thing to consider is)\b[,]?\s*',
            '', para, flags=re.IGNORECASE
        )

        if para:
            # Lowercase first char and prepend connector
            para = f"{connector} {para[0].lower()}{para[1:]}"
            paragraphs[idx] = para

    return '\n\n'.join(paragraphs)


def _humanize_ending(text: str, intensity: float, rng: random.Random) -> str:
    """Make the ending feel natural — trail off, question, or abrupt stop."""
    if rng.random() > intensity * 0.5:
        return text  # Sometimes leave ending as-is

    text = text.rstrip()

    # Remove tidy conclusion sentences at the end
    tidy_endings = [
        r'\s*(?:In conclusion|Overall|To sum up|All in all|In summary)[^.]*\.\s*$',
        r'\s*(?:I hope this|Hope this|Hopefully this)[^.]*\.\s*$',
        r'\s*(?:Feel free to|Don\'t hesitate to)[^.]*\.\s*$',
    ]
    for pattern in tidy_endings:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    text = text.rstrip()

    # Add a trailing remark
    trail = rng.choice(TRAIL_OFFS)

    # Only add if text doesn't already end with a question or trail-off
    if not text.endswith('?') and not text.endswith('...'):
        if text.endswith('.'):
            text = text[:-1]  # Remove final period
        text = f"{text}\n\n{trail}"

    return text


def intensity_from_formality(formality_level: Optional[float]) -> float:
    """
    Map community formality level to humanization intensity.

    More casual communities get heavier humanization transforms.
    More formal communities get lighter touches.

    Args:
        formality_level: Community formality score (0-10, lower = more casual)

    Returns:
        Intensity float (0.3-0.7)
    """
    if formality_level is None:
        return 0.5  # Default moderate

    if formality_level < 3.0:
        return 0.7  # Very casual = heavy humanization
    elif formality_level < 5.0:
        return 0.6  # Casual
    elif formality_level < 7.0:
        return 0.45  # Moderate
    elif formality_level < 9.0:
        return 0.35  # Formal = light touch
    else:
        return 0.25  # Very formal = minimal
