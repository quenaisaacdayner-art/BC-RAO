"""
SpaCy-based qualitative style extraction for community fingerprinting.

Extracts vocabulary frequency, noun phrases, slang/jargon (OOV tokens),
punctuation habits, formatting conventions, and opening patterns using
SpaCy capabilities already loaded but previously unused.

Zero API cost - all processing is local using the existing en_core_web_md model.
"""

import re
import statistics
from collections import Counter
from typing import List, Dict, Any, Optional

from app.analysis.nlp_pipeline import nlp


def extract_community_style(
    texts: List[str],
    top_texts: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Extract qualitative style fingerprint from community posts.

    Uses SpaCy's POS tagging, noun chunks, OOV detection, and token
    analysis to build a structural style profile. This data grounds
    the LLM style guide generator and prevents hallucinated patterns.

    Args:
        texts: ALL post texts for the subreddit (typically 50-100)
        top_texts: Top 10-20 posts by success_score for emphasis on
                   successful patterns. Falls back to texts if not provided.

    Returns:
        Dict with vocabulary, structure, punctuation, formatting, and openings data.
    """
    if not texts:
        return _empty_style()

    top_texts = top_texts or texts[:20]

    # Process all texts through SpaCy
    docs = list(nlp.pipe(texts, batch_size=50))
    top_docs = list(nlp.pipe(top_texts, batch_size=50))

    vocabulary = _extract_vocabulary(docs, top_docs)
    structure = _extract_structure(docs, texts)
    punctuation = _extract_punctuation(docs, texts)
    formatting = _extract_formatting(texts)
    openings = _extract_openings(top_texts)
    imperfections = _extract_imperfections(docs, texts)

    return {
        "vocabulary": vocabulary,
        "structure": structure,
        "punctuation": punctuation,
        "formatting": formatting,
        "openings": openings,
        "imperfections": imperfections,
    }


def _extract_vocabulary(docs, top_docs) -> Dict[str, Any]:
    """Extract vocabulary patterns using SpaCy token analysis."""
    # All-posts lemma frequency (non-stop, alphabetic tokens)
    lemma_counter = Counter()
    oov_counter = Counter()
    word_lengths = []

    for doc in docs:
        for token in doc:
            if token.is_alpha and not token.is_stop and len(token.text) > 2:
                lemma_counter[token.lemma_.lower()] += 1
                word_lengths.append(len(token.text))
            # OOV tokens = likely slang, jargon, abbreviations
            if token.is_oov and token.is_alpha and len(token.text) > 1:
                oov_counter[token.text.lower()] += 1

    # Top-posts noun phrases (what the community talks about)
    noun_phrase_counter = Counter()
    for doc in top_docs:
        for chunk in doc.noun_chunks:
            # Skip very short or very long phrases
            phrase = chunk.text.lower().strip()
            if 2 < len(phrase) < 60 and len(phrase.split()) <= 5:
                noun_phrase_counter[phrase] += 1

    # Filter OOV to those appearing 2+ times (reduces noise)
    filtered_oov = {k: v for k, v in oov_counter.items() if v >= 2}

    # Calculate stop word ratio (higher = more casual)
    total_tokens = sum(1 for doc in docs for token in doc if token.is_alpha)
    stop_tokens = sum(1 for doc in docs for token in doc if token.is_stop)
    stop_ratio = stop_tokens / total_tokens if total_tokens > 0 else 0.0

    return {
        "top_terms": [t for t, _ in lemma_counter.most_common(30)],
        "top_noun_phrases": [p for p, _ in noun_phrase_counter.most_common(20)],
        "oov_tokens": [t for t, _ in sorted(filtered_oov.items(), key=lambda x: -x[1])[:20]],
        "avg_word_length": round(statistics.mean(word_lengths), 1) if word_lengths else 0.0,
        "stop_word_ratio": round(stop_ratio, 3),
    }


def _extract_structure(docs, texts: List[str]) -> Dict[str, Any]:
    """Extract structural patterns using SpaCy sentence analysis."""
    paragraph_counts = []
    paragraph_lengths = []  # sentences per paragraph
    word_counts = []
    question_sentences = 0
    imperative_sentences = 0
    total_sentences = 0

    for doc, text in zip(docs, texts):
        # Paragraph analysis (from raw text)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        paragraph_counts.append(len(paragraphs))

        # Word count per post
        words = [t for t in doc if t.is_alpha]
        word_counts.append(len(words))

        # Sentence-level analysis
        sentences = list(doc.sents)
        total_sentences += len(sentences)

        # Sentences per paragraph (approximate)
        if paragraphs:
            paragraph_lengths.append(len(sentences) / len(paragraphs))

        for sent in sentences:
            sent_text = sent.text.strip()
            # Question detection
            if sent_text.endswith("?"):
                question_sentences += 1
            # Imperative detection (starts with verb)
            tokens = [t for t in sent if t.is_alpha]
            if tokens and tokens[0].pos_ == "VERB":
                imperative_sentences += 1

    return {
        "avg_paragraph_count": round(statistics.mean(paragraph_counts), 1) if paragraph_counts else 0.0,
        "avg_paragraph_length_sentences": round(statistics.mean(paragraph_lengths), 1) if paragraph_lengths else 0.0,
        "avg_post_word_count": round(statistics.mean(word_counts)) if word_counts else 0,
        "post_word_count_std": round(statistics.stdev(word_counts)) if len(word_counts) > 1 else 0,
        "question_sentence_ratio": round(question_sentences / total_sentences, 3) if total_sentences > 0 else 0.0,
        "imperative_ratio": round(imperative_sentences / total_sentences, 3) if total_sentences > 0 else 0.0,
    }


def _extract_punctuation(docs, texts: List[str]) -> Dict[str, Any]:
    """Extract punctuation and special character patterns."""
    exclamation_counts = []
    question_counts = []
    ellipsis_counts = []
    parenthetical_counts = []
    emoji_counts = []

    # Emoji regex (common Unicode emoji ranges)
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U0000FE00-\U0000FE0F"  # variation selectors
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "]+", flags=re.UNICODE
    )

    for text in texts:
        exclamation_counts.append(text.count("!"))
        question_counts.append(text.count("?"))
        ellipsis_counts.append(text.count("...") + text.count("\u2026"))
        parenthetical_counts.append(text.count("("))
        emoji_counts.append(len(emoji_pattern.findall(text)))

    n = len(texts)
    return {
        "exclamation_per_post": round(sum(exclamation_counts) / n, 2) if n else 0.0,
        "question_mark_per_post": round(sum(question_counts) / n, 2) if n else 0.0,
        "ellipsis_per_post": round(sum(ellipsis_counts) / n, 2) if n else 0.0,
        "emoji_per_post": round(sum(emoji_counts) / n, 2) if n else 0.0,
        "parenthetical_per_post": round(sum(parenthetical_counts) / n, 2) if n else 0.0,
    }


def _extract_formatting(texts: List[str]) -> Dict[str, Any]:
    """Extract formatting conventions from raw text."""
    n = len(texts)
    if not n:
        return {
            "has_tldr_ratio": 0.0,
            "has_edit_ratio": 0.0,
            "has_links_ratio": 0.0,
            "has_code_blocks_ratio": 0.0,
            "avg_line_breaks": 0.0,
        }

    tldr_pattern = re.compile(r"tl;?dr|TL;?DR", re.IGNORECASE)
    edit_pattern = re.compile(r"^(?:EDIT|UPDATE|ETA)\s*:", re.MULTILINE)
    link_pattern = re.compile(r"https?://\S+")
    code_pattern = re.compile(r"```|    \S")  # fenced or indented code

    has_tldr = sum(1 for t in texts if tldr_pattern.search(t))
    has_edit = sum(1 for t in texts if edit_pattern.search(t))
    has_links = sum(1 for t in texts if link_pattern.search(t))
    has_code = sum(1 for t in texts if code_pattern.search(t))
    line_breaks = [t.count("\n") for t in texts]

    return {
        "has_tldr_ratio": round(has_tldr / n, 3),
        "has_edit_ratio": round(has_edit / n, 3),
        "has_links_ratio": round(has_links / n, 3),
        "has_code_blocks_ratio": round(has_code / n, 3),
        "avg_line_breaks": round(statistics.mean(line_breaks), 1) if line_breaks else 0.0,
    }


def _extract_openings(top_texts: List[str]) -> Dict[str, Any]:
    """Extract opening patterns from top-performing posts."""
    opening_words = Counter()

    for text in top_texts:
        text = text.strip()
        if not text:
            continue
        # Get first 3-5 words as a pattern
        words = text.split()[:4]
        if len(words) >= 2:
            pattern = " ".join(words)
            # Normalize: replace specific nouns/names with "..."
            opening_words[pattern] += 1

    # Group similar openings (first 2 words match)
    grouped = Counter()
    for pattern, count in opening_words.items():
        words = pattern.split()
        prefix = " ".join(words[:2]) + " ..."
        grouped[prefix] += count

    top_patterns = [
        {"pattern": p, "count": c}
        for p, c in grouped.most_common(10)
        if c >= 1
    ]

    return {
        "top_opening_patterns": top_patterns,
    }


def _extract_imperfections(docs, texts: List[str]) -> Dict[str, Any]:
    """
    Extract imperfection metrics that characterize human-like writing.

    Measures fragment ratio (verbless sentences), parenthetical asides,
    self-correction markers, and dash interruptions. These metrics tell
    the generation LLM how messy to write to match the community.

    Args:
        docs: SpaCy Doc objects for each text
        texts: Raw post texts

    Returns:
        Dict with fragment_ratio, parenthetical_frequency,
        self_correction_rate, dash_interruption_rate
    """
    # Parenthetical regex: 5+ chars inside parens (filters emoticons/short asides)
    parenthetical_pattern = re.compile(r'\([^)]{5,}\)')
    # Self-correction markers
    self_correction_pattern = re.compile(
        r'\b(?:I mean|actually|wait|edit:|update:|sorry,? I meant)\b',
        re.IGNORECASE,
    )
    # Mid-sentence dash interruptions (space-dash-space or em-dash)
    dash_pattern = re.compile(r'\s[-\u2013\u2014]{1,2}\s')

    fragment_count = 0
    total_sentences = 0
    parenthetical_counts = []
    self_correction_counts = []
    dash_counts = []

    for doc, text in zip(docs, texts):
        # Fragment detection: sentences without a VERB POS tag
        for sent in doc.sents:
            tokens = [t for t in sent if t.is_alpha]
            # Skip single-word sentences and punctuation-only sentences
            if len(tokens) <= 1:
                continue
            total_sentences += 1
            has_verb = any(t.pos_ == "VERB" for t in sent)
            if not has_verb:
                fragment_count += 1

        # Per-post counts for averaging
        parenthetical_counts.append(len(parenthetical_pattern.findall(text)))
        self_correction_counts.append(len(self_correction_pattern.findall(text)))
        dash_counts.append(len(dash_pattern.findall(text)))

    n = len(texts)
    return {
        "fragment_ratio": round(fragment_count / total_sentences, 3) if total_sentences > 0 else 0.0,
        "parenthetical_frequency": round(sum(parenthetical_counts) / n, 2) if n > 0 else 0.0,
        "self_correction_rate": round(sum(self_correction_counts) / n, 2) if n > 0 else 0.0,
        "dash_interruption_rate": round(sum(dash_counts) / n, 2) if n > 0 else 0.0,
    }


def _empty_style() -> Dict[str, Any]:
    """Return empty style structure for edge cases."""
    return {
        "vocabulary": {
            "top_terms": [],
            "top_noun_phrases": [],
            "oov_tokens": [],
            "avg_word_length": 0.0,
            "stop_word_ratio": 0.0,
        },
        "structure": {
            "avg_paragraph_count": 0.0,
            "avg_paragraph_length_sentences": 0.0,
            "avg_post_word_count": 0,
            "post_word_count_std": 0,
            "question_sentence_ratio": 0.0,
            "imperative_ratio": 0.0,
        },
        "punctuation": {
            "exclamation_per_post": 0.0,
            "question_mark_per_post": 0.0,
            "ellipsis_per_post": 0.0,
            "emoji_per_post": 0.0,
            "parenthetical_per_post": 0.0,
        },
        "formatting": {
            "has_tldr_ratio": 0.0,
            "has_edit_ratio": 0.0,
            "has_links_ratio": 0.0,
            "has_code_blocks_ratio": 0.0,
            "avg_line_breaks": 0.0,
        },
        "openings": {
            "top_opening_patterns": [],
        },
        "imperfections": {
            "fragment_ratio": 0.0,
            "parenthetical_frequency": 0.0,
            "self_correction_rate": 0.0,
            "dash_interruption_rate": 0.0,
        },
    }
