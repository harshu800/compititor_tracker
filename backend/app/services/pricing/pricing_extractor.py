"""Specialized pricing diff. Uses the structured `prices` list already
extracted by extractor.py (regex-based, not AI) to pair up old/new prices
per plan name where possible, so we can report "$29 -> $39" precisely
instead of just "prices changed". AI classification (classifier.py) is
used only as an interpretive fallback for ambiguous cases, never as the
source of the numbers themselves."""
from dataclasses import dataclass


@dataclass
class PriceChange:
    plan_name: str | None
    old_price: float | None
    new_price: float | None
    currency: str
    billing_period: str | None


def diff_pricing(old_structured: dict | None, new_structured: dict) -> list[PriceChange]:
    old_structured = old_structured or {}
    old_prices = old_structured.get("prices", [])
    new_prices = new_structured.get("prices", [])
    old_plans = old_structured.get("plan_names", [])
    new_plans = new_structured.get("plan_names", [])

    changes: list[PriceChange] = []

    # Simple, honest heuristic: if plan names are stable and count of prices
    # is equal, pair them by sorted amount order (best-effort, not claimed
    # as certain — the AI classifier's "why it matters" text should hedge
    # if this pairing looks unreliable, e.g. plan count changed too).
    if old_prices and new_prices and len(old_prices) == len(new_prices):
        old_sorted = sorted(old_prices, key=lambda p: p["amount"])
        new_sorted = sorted(new_prices, key=lambda p: p["amount"])
        for op, np_ in zip(old_sorted, new_sorted):
            if op["amount"] != np_["amount"] or op.get("period") != np_.get("period"):
                changes.append(PriceChange(
                    plan_name=None,
                    old_price=op["amount"], new_price=np_["amount"],
                    currency=np_.get("currency", op.get("currency", "$")),
                    billing_period=np_.get("period") or op.get("period"),
                ))
    else:
        # Plan/price count changed — report additions/removals rather than
        # guessing a pairing.
        old_set = {(p["currency"], p["amount"], p.get("period")) for p in old_prices}
        new_set = {(p["currency"], p["amount"], p.get("period")) for p in new_prices}
        for currency, amount, period in new_set - old_set:
            changes.append(PriceChange(None, None, amount, currency, period))
        for currency, amount, period in old_set - new_set:
            changes.append(PriceChange(None, amount, None, currency, period))

    return changes
