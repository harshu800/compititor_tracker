"""Field-by-field diff on the structured content extracted from a page
(title, headings, prices, CTAs, plan names). This is what catches
"a pricing tier appeared/disappeared" or "the H1 changed" cleanly,
without relying on noisy free-text diffing alone."""


def structured_diff(old: dict | None, new: dict) -> dict:
    old = old or {}
    changes = {}

    if (old.get("title") or "") != (new.get("title") or ""):
        changes["title"] = {"before": old.get("title", ""), "after": new.get("title", "")}

    old_headings = set(old.get("headings", []))
    new_headings = set(new.get("headings", []))
    if old_headings != new_headings:
        changes["headings"] = {
            "added": sorted(new_headings - old_headings),
            "removed": sorted(old_headings - new_headings),
        }

    old_ctas = set(old.get("ctas", []))
    new_ctas = set(new.get("ctas", []))
    if old_ctas != new_ctas:
        changes["ctas"] = {
            "added": sorted(new_ctas - old_ctas),
            "removed": sorted(old_ctas - new_ctas),
        }

    old_prices = {(p["currency"], p["amount"], p.get("period")) for p in old.get("prices", [])}
    new_prices = {(p["currency"], p["amount"], p.get("period")) for p in new.get("prices", [])}
    if old_prices != new_prices:
        changes["prices"] = {
            "added": [{"currency": c, "amount": a, "period": p} for c, a, p in (new_prices - old_prices)],
            "removed": [{"currency": c, "amount": a, "period": p} for c, a, p in (old_prices - new_prices)],
        }

    old_plans = set(old.get("plan_names", []))
    new_plans = set(new.get("plan_names", []))
    if old_plans != new_plans:
        changes["plan_names"] = {
            "added": sorted(new_plans - old_plans),
            "removed": sorted(old_plans - new_plans),
        }

    return changes
