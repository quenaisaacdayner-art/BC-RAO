"""
Inference package: OpenRouter abstraction with model routing and cost tracking.
Re-exports main components for convenience.
"""
from app.inference.client import InferenceClient
from app.inference.router import MODEL_ROUTING, COST_CAPS
from app.inference.cost_tracker import CostTracker

__all__ = ["InferenceClient", "MODEL_ROUTING", "COST_CAPS", "CostTracker"]
