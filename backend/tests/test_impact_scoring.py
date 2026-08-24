from app.services.scoring.impact_scoring import calculate_impact_score, importance_from_score
from app.services.diff.change_detector import DiffResult


def test_pricing_change_on_pricing_page_scores_high():
    diff = DiffResult(change_score=70.0, meaningful=True)
    score, importance = calculate_impact_score("pricing", "pricing", diff)
    assert score > 50
    assert importance in ("high", "critical")


def test_legal_change_on_blog_scores_low():
    diff = DiffResult(change_score=10.0, meaningful=True)
    score, importance = calculate_impact_score("legal", "blog", diff)
    assert score < 21
    assert importance == "low"


def test_importance_bands_cover_full_range():
    assert importance_from_score(0) == "low"
    assert importance_from_score(20) == "low"
    assert importance_from_score(21) == "medium"
    assert importance_from_score(50) == "medium"
    assert importance_from_score(51) == "high"
    assert importance_from_score(75) == "high"
    assert importance_from_score(76) == "critical"
    assert importance_from_score(100) == "critical"


def test_score_never_exceeds_100():
    diff = DiffResult(change_score=100.0, meaningful=True)
    score, _ = calculate_impact_score("pricing", "pricing", diff)
    assert score <= 100.0
