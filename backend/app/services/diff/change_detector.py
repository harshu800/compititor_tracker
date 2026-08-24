"""Combines text_diff + structured_diff into a single change-score and a
meaningful/not-meaningful decision. This is the false-positive gate:
nothing downstream (AI classification, alerting) runs unless
`meaningful=True` comes out of here."""
from dataclasses import dataclass, field

from app.config import get_settings
from app.services.diff.text_diff import word_diff
from app.services.diff.structured_diff import structured_diff

settings = get_settings()

# Minimum number of changed words required before we even consider a
# free-text change "real" — guards against single stray punctuation/
# whitespace diffs slipping through despite normalization.
MIN_CHANGED_WORDS = 3


@dataclass
class DiffResult:
    added: list = field(default_factory=list)
    removed: list = field(default_factory=list)
    modified: list = field(default_factory=list)
    structured_changes: dict = field(default_factory=dict)
    change_score: float = 0.0       # 0-100, magnitude of the diff itself (not business impact)
    meaningful: bool = False


def detect_change(
    old_normalized_text: str | None,
    new_normalized_text: str,
    old_structured: dict | None,
    new_structured: dict,
) -> DiffResult:
    if old_normalized_text is None:
        # First-ever snapshot: nothing to compare against, not a "change".
        return DiffResult(meaningful=False, change_score=0.0)

    td = word_diff(old_normalized_text, new_normalized_text)
    sd = structured_diff(old_structured, new_structured)

    changed_word_count = (
        sum(len(a.split()) for a in td["added"])
        + sum(len(r.split()) for r in td["removed"])
        + sum(len(m["before"].split()) + len(m["after"].split()) for m in td["modified"])
    )

    # change_score blends text-magnitude with whether structured fields (the
    # signals we actually care about) moved at all.
    text_score = td["change_ratio"] * 60  # up to 60 points from raw text churn
    structural_score = min(len(sd) * 15, 40)  # up to 40 points if title/price/cta/heading fields changed
    change_score = round(min(text_score + structural_score, 100.0), 2)

    meaningful = (
        change_score >= settings.min_change_score_threshold
        and (changed_word_count >= MIN_CHANGED_WORDS or bool(sd))
    )

    return DiffResult(
        added=td["added"],
        removed=td["removed"],
        modified=td["modified"],
        structured_changes=sd,
        change_score=change_score,
        meaningful=meaningful,
    )
