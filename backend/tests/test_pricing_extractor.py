from app.services.pricing.pricing_extractor import diff_pricing


def test_detects_simple_price_increase():
    old = {"prices": [{"currency": "$", "amount": 29, "period": "month"}], "plan_names": ["Pro"]}
    new = {"prices": [{"currency": "$", "amount": 39, "period": "month"}], "plan_names": ["Pro"]}
    changes = diff_pricing(old, new)
    assert len(changes) == 1
    assert changes[0].old_price == 29
    assert changes[0].new_price == 39


def test_detects_new_plan_added():
    old = {"prices": [{"currency": "$", "amount": 29, "period": "month"}]}
    new = {"prices": [
        {"currency": "$", "amount": 29, "period": "month"},
        {"currency": "$", "amount": 99, "period": "month"},
    ]}
    changes = diff_pricing(old, new)
    assert any(c.new_price == 99 and c.old_price is None for c in changes)


def test_no_change_gives_empty_diff():
    prices = {"prices": [{"currency": "$", "amount": 29, "period": "month"}]}
    changes = diff_pricing(prices, prices)
    assert changes == []
