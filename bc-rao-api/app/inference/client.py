"""
InferenceClient: OpenRouter abstraction with model routing and cost tracking.
Provides task-based model selection with automatic fallback and budget enforcement.
"""
from typing import Optional
import httpx
from app.config import settings
from app.inference.router import MODEL_ROUTING
from app.inference.cost_tracker import CostTracker
from app.utils.errors import AppError, ErrorCode


class InferenceClient:
    """
    Client for making inference calls via OpenRouter with cost tracking.
    Each instance is configured for a specific task type.
    """

    def __init__(self, task: str):
        """
        Initialize client for a specific task type.

        Args:
            task: Task key from MODEL_ROUTING (e.g., "classify_archetype")

        Raises:
            ValueError: If task is not in MODEL_ROUTING
        """
        if task not in MODEL_ROUTING:
            raise ValueError(f"Unknown task: {task}. Must be one of {list(MODEL_ROUTING.keys())}")

        self.task = task
        self.config = MODEL_ROUTING[task]
        self.cost_tracker = CostTracker()

    async def call(
        self,
        prompt: str,
        user_id: str,
        plan: str,
        campaign_id: Optional[str] = None
    ) -> dict:
        """
        Make inference call with budget checking and cost tracking.

        Args:
            prompt: User prompt/input
            user_id: User UUID for cost tracking
            plan: User plan (trial, starter, growth)
            campaign_id: Campaign UUID (optional)

        Returns:
            dict with keys: content, model_used, token_count, cost_usd

        Raises:
            AppError: PLAN_LIMIT_REACHED if over budget
            AppError: INFERENCE_FAILED if OpenRouter call fails
        """
        # 1. Check budget
        can_proceed, remaining = await self.cost_tracker.check_budget(user_id, plan)
        if not can_proceed:
            raise AppError(
                code=ErrorCode.PLAN_LIMIT_REACHED,
                message=f"Monthly budget cap reached for {plan} plan",
                details={"remaining_budget": remaining},
                status_code=402  # Payment Required
            )

        # 2. Try primary model
        try:
            result = await self._call_openrouter(
                prompt=prompt,
                model=self.config["model"],
                max_tokens=self.config["max_tokens"],
                temperature=self.config["temperature"]
            )
        except Exception as e:
            # 3. Fallback to secondary model on failure
            try:
                result = await self._call_openrouter(
                    prompt=prompt,
                    model=self.config["fallback"],
                    max_tokens=self.config["max_tokens"],
                    temperature=self.config["temperature"]
                )
            except Exception as fallback_error:
                raise AppError(
                    code=ErrorCode.INFERENCE_FAILED,
                    message="Inference call failed after fallback attempt",
                    details={
                        "primary_error": str(e),
                        "fallback_error": str(fallback_error),
                        "task": self.task
                    },
                    status_code=503  # Service Unavailable
                )

        # 4. Calculate cost (rough estimate based on token count)
        # OpenRouter pricing varies by model, this is a simplified calculation
        # In production, parse actual cost from OpenRouter response headers
        token_count = result["token_count"]
        cost_usd = self._estimate_cost(token_count, result["model_used"])

        # 5. Record usage
        await self.cost_tracker.record_usage(
            user_id=user_id,
            action_type=self._map_task_to_action(self.task),
            campaign_id=campaign_id,
            token_count=token_count,
            cost_usd=cost_usd
        )

        # 6. Return result
        return {
            "content": result["content"],
            "model_used": result["model_used"],
            "token_count": token_count,
            "cost_usd": cost_usd
        }

    async def _call_openrouter(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float
    ) -> dict:
        """
        Make HTTP call to OpenRouter API.

        Returns:
            dict with keys: content, model_used, token_count
        """
        url = f"{settings.OPENROUTER_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://bcrao.app",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()

        data = response.json()

        # Parse response
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        token_count = usage.get("total_tokens", 0)

        return {
            "content": content,
            "model_used": model,
            "token_count": token_count
        }

    def _estimate_cost(self, token_count: int, model: str) -> float:
        """
        Estimate cost based on token count and model.

        TODO: Parse actual cost from OpenRouter response headers (X-OpenRouter-Cost or generation_info)
        Current implementation uses hardcoded 2024 pricing estimates which may be inaccurate.
        This affects budget tracking and usage limits.
        """
        # Rough cost per 1K tokens (in USD) - 2024 pricing
        cost_per_1k = {
            "claude-3-haiku": 0.0005,
            "claude-sonnet-4": 0.015,
            "gemini-flash": 0.0002,
            "gpt-4o-mini": 0.0003,
        }

        # Match model to cost tier
        for key, cost in cost_per_1k.items():
            if key in model.lower():
                return (token_count / 1000) * cost

        # Default conservative estimate
        return (token_count / 1000) * 0.001

    def _map_task_to_action(self, task: str) -> str:
        """
        Map task type to usage_action enum.
        """
        mapping = {
            "classify_archetype": "analyze",
            "generate_draft": "generate",
            "score_post": "analyze",
            "extract_patterns": "analyze",
        }
        return mapping.get(task, "analyze")
