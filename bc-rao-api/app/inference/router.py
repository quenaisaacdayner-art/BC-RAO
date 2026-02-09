"""
Model routing configuration for inference tasks.
Maps task types to OpenRouter models with fallback options.
"""

# Model routing per task type (Section 6.1 of system spec)
MODEL_ROUTING = {
    "classify_archetype": {
        "model": "anthropic/claude-3-haiku-20240307",
        "max_tokens": 200,
        "temperature": 0.1,
        "fallback": "google/gemini-flash-1.5"
    },
    "generate_draft": {
        "model": "anthropic/claude-sonnet-4-20250514",
        "max_tokens": 2000,
        "temperature": 0.7,
        "fallback": "openai/gpt-4o-mini"
    },
    "score_post": {
        "model": "anthropic/claude-3-haiku-20240307",
        "max_tokens": 500,
        "temperature": 0.0,
        "fallback": "google/gemini-flash-1.5"
    },
    "extract_patterns": {
        "model": "anthropic/claude-3-haiku-20240307",
        "max_tokens": 1000,
        "temperature": 0.2,
        "fallback": "google/gemini-flash-1.5"
    },
}

# Cost caps per plan (Section 6.2 of system spec)
COST_CAPS = {
    "trial": 5.00,
    "starter": 15.00,
    "growth": 40.00,
}
