"""
SpaCy NLP pipeline with custom components for Reddit post analysis.

Custom components:
- formality_scorer: Calculates text formality using Flesch-Kincaid and Gunning FOG
- tone_classifier: Classifies sentiment using VADER
- rhythm_analyzer: Analyzes sentence length patterns and vocabulary complexity

IMPORTANT: This module requires en_core_web_md model installed:
    python -m spacy download en_core_web_md

Zero external API costs - all processing is local.
"""

import statistics
from typing import Optional

import spacy
import textstat
from spacy.language import Language
from spacy.tokens import Doc
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Initialize textstat for English
textstat.set_lang('en')

# Load SpaCy model at module level (disable NER to save memory)
nlp = spacy.load("en_core_web_md", disable=["ner"])

# Initialize VADER sentiment analyzer
vader = SentimentIntensityAnalyzer()

# Register custom Doc extensions
Doc.set_extension("formality_score", default=None, force=True)
Doc.set_extension("tone", default=None, force=True)
Doc.set_extension("tone_compound", default=None, force=True)
Doc.set_extension("avg_sentence_length", default=None, force=True)
Doc.set_extension("sentence_length_std", default=None, force=True)
Doc.set_extension("vocabulary_complexity", default=None, force=True)
Doc.set_extension("num_sentences", default=None, force=True)


@Language.component("formality_scorer")
def formality_scorer(doc: Doc) -> Doc:
    """
    Calculate formality score using Flesch-Kincaid and Gunning FOG.

    Skip texts < 20 chars to avoid textstat errors on very short inputs.
    """
    text = doc.text.strip()

    if len(text) < 20:
        doc._.formality_score = None
        return doc

    try:
        fk_grade = textstat.flesch_kincaid_grade(text)
        gunning_fog = textstat.gunning_fog(text)

        # Average the two scores
        doc._.formality_score = (fk_grade + gunning_fog) / 2.0
    except (ZeroDivisionError, ValueError):
        # Handle edge cases where textstat fails
        doc._.formality_score = None

    return doc


@Language.component("tone_classifier")
def tone_classifier(doc: Doc) -> Doc:
    """
    Classify text tone using VADER sentiment analysis.

    Compound >= 0.05: positive
    Compound <= -0.05: negative
    Otherwise: neutral
    """
    text = doc.text.strip()

    if not text:
        doc._.tone = "neutral"
        doc._.tone_compound = 0.0
        return doc

    scores = vader.polarity_scores(text)
    compound = scores['compound']

    doc._.tone_compound = compound

    if compound >= 0.05:
        doc._.tone = "positive"
    elif compound <= -0.05:
        doc._.tone = "negative"
    else:
        doc._.tone = "neutral"

    return doc


@Language.component("rhythm_analyzer")
def rhythm_analyzer(doc: Doc) -> Doc:
    """
    Analyze sentence length patterns and vocabulary complexity.

    Calculates:
    - Average sentence length (tokens per sentence)
    - Sentence length standard deviation (rhythm consistency)
    - Vocabulary complexity (type-token ratio for alphabetic tokens)
    """
    sentences = list(doc.sents)
    doc._.num_sentences = len(sentences)

    if not sentences:
        doc._.avg_sentence_length = None
        doc._.sentence_length_std = None
        doc._.vocabulary_complexity = None
        return doc

    # Calculate sentence lengths
    sentence_lengths = [len(sent) for sent in sentences]
    doc._.avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths)

    # Calculate standard deviation (handle single-sentence case)
    if len(sentence_lengths) > 1:
        doc._.sentence_length_std = statistics.stdev(sentence_lengths)
    else:
        doc._.sentence_length_std = 0.0

    # Calculate vocabulary complexity (type-token ratio for alphabetic tokens)
    alpha_tokens = [token.lemma_.lower() for token in doc if token.is_alpha]

    if alpha_tokens:
        unique_lemmas = len(set(alpha_tokens))
        total_tokens = len(alpha_tokens)
        doc._.vocabulary_complexity = unique_lemmas / total_tokens
    else:
        doc._.vocabulary_complexity = None

    return doc


# Add custom components to pipeline
nlp.add_pipe("formality_scorer", last=True)
nlp.add_pipe("tone_classifier", last=True)
nlp.add_pipe("rhythm_analyzer", last=True)


def get_nlp_pipeline():
    """
    Get the configured SpaCy NLP pipeline (singleton pattern).

    Returns:
        Configured SpaCy Language object with custom components.
    """
    return nlp


def analyze_posts_batch(texts: list[str], batch_size: int = 100) -> list[dict]:
    """
    Process texts in batches and extract NLP metrics.

    IMPORTANT: Never use n_process parameter inside Celery workers
    (causes deadlock per research pitfall 2).

    Args:
        texts: List of post texts to analyze
        batch_size: Number of texts to process per batch

    Returns:
        List of dicts with NLP metrics for each text:
        - formality_score
        - tone
        - tone_compound
        - avg_sentence_length
        - sentence_length_std
        - vocabulary_complexity
        - num_sentences
    """
    results = []

    for doc in nlp.pipe(texts, batch_size=batch_size):
        # Handle empty/None texts gracefully
        if not doc.text.strip():
            results.append({
                "formality_score": None,
                "tone": "neutral",
                "tone_compound": 0.0,
                "avg_sentence_length": None,
                "sentence_length_std": None,
                "vocabulary_complexity": None,
                "num_sentences": 0,
            })
        else:
            results.append({
                "formality_score": doc._.formality_score,
                "tone": doc._.tone,
                "tone_compound": doc._.tone_compound,
                "avg_sentence_length": doc._.avg_sentence_length,
                "sentence_length_std": doc._.sentence_length_std,
                "vocabulary_complexity": doc._.vocabulary_complexity,
                "num_sentences": doc._.num_sentences,
            })

    return results
