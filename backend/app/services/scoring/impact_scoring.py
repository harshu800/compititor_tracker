"""
Deterministic impact scoring. The backend OWNS this number — the LLM never
assigns the numeric score, only contextual explanation. This keeps scoring
auditable, reproducible, and immune to prompt-injection or LLM drift.

Formula (spec section 20/40):
  base_score(change_type) + magnitude_component + page_weight_multiplier
  -> normalized to 0-100
"""
from app.services.diff.change_detector import DiffResult

# Base points per detected change_type (before page-weight multiplier).
CHANGE_TYPE_BASE_POINTS = {
    "pricing": 40,
    "feature": 30,
    "positioning": 30,
    "product": 25,
    "offer": 20,
    "cta": 15,
    "messaging": 10,
    "content": 8,
    "design": 5,
    "legal": 2,
    "other": 5,
}

# Page-type importance weights (spec section 40).
PAGE_TYPE_WEIGHTS = {
    "pricing": 1.5,
    "homepage": 1.4,
    "features": 1.3,
    "product": 1.2,
    "changelog": 1.0,
    "blog": 0.7,
    "custom": 1.0,
}

IMPORTANCE_BANDS = [
    (76, 100, "critical"),
    (51, 75, "high"),
    (21, 50, "medium"),
    (0, 20, "low"),
]


def importance_from_score(score: float) -> str:
    for lo, hi, label in IMPORTANCE_BANDS:
        if lo <= score <= hi:
            return label
    return "low"


def calculate_impact_score(change_type: str, page_type: str, diff: DiffResult) -> tuple[float, str]:
    base = CHANGE_TYPE_BASE_POINTS.get(change_type, CHANGE_TYPE_BASE_POINTS["other"])

    # Change magnitude contributes up to +20 extra points, scaled by the
    # diff engine's own 0-100 change_score (how much of the page moved).
    magnitude_bonus = (diff.change_score / 100) * 20

    page_weight = PAGE_TYPE_WEIGHTS.get(page_type, 1.0)

    raw_score = (base + magnitude_bonus) * page_weight
    normalized = max(0.0, min(round(raw_score, 1), 100.0))

    return normalized, importance_from_score(normalized)
