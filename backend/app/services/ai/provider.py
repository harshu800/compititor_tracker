"""
AI provider abstraction. Swap providers via AI_PROVIDER env var without
touching any calling code. Every provider implements the same interface:
`complete_json(system_prompt, user_prompt) -> str` returning raw text that
the caller will validate against a Pydantic schema (never trusted as-is).
"""
from abc import ABC, abstractmethod

from app.config import get_settings

settings = get_settings()


class AIProvider(ABC):
    @abstractmethod
    async def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        ...


class OpenAIProvider(AIProvider):
    def __init__(self):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        resp = await self.client.chat.completions.create(
            model=settings.ai_model,
            response_format={"type": "json_object"},
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return resp.choices[0].message.content or "{}"


class AnthropicProvider(AIProvider):
    def __init__(self):
        from anthropic import AsyncAnthropic
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        resp = await self.client.messages.create(
            model=settings.ai_model if "claude" in settings.ai_model else "claude-sonnet-4-6",
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text_blocks = [b.text for b in resp.content if getattr(b, "type", "") == "text"]
        return "".join(text_blocks) or "{}"


class MockProvider(AIProvider):
    """Used for demo mode / tests / local dev with no API keys. Produces a
    deterministic, clearly-labeled explanation from the diff itself instead
    of calling out to a real model."""
    async def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        import json
        return json.dumps({
            "change_type": "content",
            "importance": "medium",
            "summary": "A change was detected on this page (demo/mock AI response).",
            "what_changed": "Content on the monitored page changed since the last check.",
            "why_it_matters": "This may indicate a shift worth reviewing. Consider investigating further.",
            "recommended_action": "Review the before/after diff on this page to assess relevance.",
            "confidence": 0.5,
        })


def get_ai_provider() -> AIProvider:
    if settings.ai_provider == "openai" and settings.openai_api_key:
        return OpenAIProvider()
    if settings.ai_provider == "anthropic" and settings.anthropic_api_key:
        return AnthropicProvider()
    return MockProvider()
