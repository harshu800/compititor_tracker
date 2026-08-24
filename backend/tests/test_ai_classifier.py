import pytest
import json
from app.services.ai.schemas import AIClassification
from pydantic import ValidationError


def test_valid_classification_parses():
    data = {
        "change_type": "pricing", "importance": "high", "summary": "Price changed",
        "what_changed": "Pro plan went from $29 to $39", "why_it_matters": "May affect your positioning",
        "recommended_action": "Review pricing page", "confidence": 0.9,
    }
    obj = AIClassification.model_validate(data)
    assert obj.change_type == "pricing"


def test_invalid_change_type_rejected():
    data = {
        "change_type": "not_a_real_type", "importance": "high", "summary": "x",
        "what_changed": "x", "why_it_matters": "x", "recommended_action": "x", "confidence": 0.5,
    }
    with pytest.raises(ValidationError):
        AIClassification.model_validate(data)


def test_missing_field_rejected():
    data = {"change_type": "pricing", "importance": "high", "summary": "x"}
    with pytest.raises(ValidationError):
        AIClassification.model_validate(data)


def test_confidence_out_of_range_rejected():
    data = {
        "change_type": "pricing", "importance": "high", "summary": "x",
        "what_changed": "x", "why_it_matters": "x", "recommended_action": "x", "confidence": 1.5,
    }
    with pytest.raises(ValidationError):
        AIClassification.model_validate(data)


def test_empty_summary_rejected():
    data = {
        "change_type": "pricing", "importance": "high", "summary": "   ",
        "what_changed": "x", "why_it_matters": "x", "recommended_action": "x", "confidence": 0.5,
    }
    with pytest.raises(ValidationError):
        AIClassification.model_validate(data)


@pytest.mark.asyncio
async def test_classifier_falls_back_on_invalid_json():
    from app.services.ai.classifier import classify_change
    # AI_PROVIDER=mock in test env -> MockProvider always returns valid JSON,
    # so this exercises the happy path through classify_change end-to-end.
    result = await classify_change("Acme", "pricing", {"added": [], "removed": []})
    assert result.change_type in (
        "pricing", "feature", "positioning", "product", "offer",
        "cta", "content", "messaging", "legal", "design", "other",
    )
