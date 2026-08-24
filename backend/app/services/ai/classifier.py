"""Calls the AI provider to classify a detected, already-meaningful change,
then validates the response strictly. If the LLM output is invalid or
fails validation, we fall back to a safe, honest default rather than
guessing or silently failing — the user still gets an alert, just with a
generic (accurately-labeled) explanation instead of a hallucinated one."""
import json
import logging

from pydantic import ValidationError

from app.services.ai.provider import get_ai_provider
from app.services.ai.schemas import AIClassification

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a competitive intelligence analyst. You are given a \
detected change on a competitor's public web page, along with the diff and the \
user's own company/product context. Your job is to classify the change and \
explain its business relevance.

STRICT RULES:
- Only use information present in the provided diff and page content. Never invent facts, numbers, or motives.
- Do not claim certainty about a competitor's strategy or intent. Use language like \
"this may indicate...", "potentially important because...", "consider investigating...".
- Never write a sentence claiming the competitor "definitely" did something for a \
specific reason unless that reason is explicitly stated in the source content.
- Clearly separate observed facts (what_changed) from interpretation (why_it_matters) \
and suggestion (recommended_action).
- Respond ONLY with a single JSON object matching this schema, no prose, no markdown fences:
{
  "change_type": "pricing|feature|positioning|product|offer|cta|content|messaging|legal|design|other",
  "importance": "critical|high|medium|low",
  "summary": "one sentence",
  "what_changed": "factual description of the diff",
  "why_it_matters": "cautious interpretation, hedged language",
  "recommended_action": "one concrete, actionable suggestion for the user",
  "confidence": 0.0-1.0
}"""


def _build_user_prompt(
    competitor_name: str, page_type: str, diff: dict,
    user_company_description: str, user_product_category: str,
) -> str:
    return json.dumps({
        "competitor_name": competitor_name,
        "page_type": page_type,
        "diff": diff,
        "user_company_description": user_company_description or "(not provided)",
        "user_product_category": user_product_category or "(not provided)",
    }, indent=2)


FALLBACK = AIClassification(
    change_type="content",
    importance="medium",
    summary="A meaningful change was detected on this page.",
    what_changed="The page's content changed since the last check; see the diff for details.",
    why_it_matters="This may be worth reviewing manually — automatic classification was unavailable.",
    recommended_action="Open the before/after diff to assess whether this affects your positioning.",
    confidence=0.3,
)


async def classify_change(
    competitor_name: str, page_type: str, diff: dict,
    user_company_description: str = "", user_product_category: str = "",
) -> AIClassification:
    provider = get_ai_provider()
    user_prompt = _build_user_prompt(
        competitor_name, page_type, diff, user_company_description, user_product_category
    )

    try:
        raw = await provider.complete_json(SYSTEM_PROMPT, user_prompt)
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(cleaned)
        return AIClassification.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as e:
        logger.warning("AI classification failed validation, using fallback: %s", e)
        return FALLBACK
    except Exception as e:
        logger.error("AI classification call failed, using fallback: %s", e)
        return FALLBACK
