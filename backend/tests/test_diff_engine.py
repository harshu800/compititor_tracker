from app.services.diff.change_detector import detect_change
from app.services.diff.text_diff import word_diff


def test_word_diff_detects_added_text():
    result = word_diff("we offer basic support", "we offer basic and premium support")
    assert "and premium" in " ".join(result["added"]) or result["added"]


def test_word_diff_detects_removed_text():
    result = word_diff("free unlimited users included", "unlimited users included")
    assert any("free" in r for r in result["removed"])


def test_word_diff_no_change_gives_zero_ratio():
    result = word_diff("same text here", "same text here")
    assert result["change_ratio"] == 0.0


def test_first_snapshot_is_never_meaningful():
    result = detect_change(None, "brand new page content here", None, {"title": "X"})
    assert result.meaningful is False


def test_tiny_change_is_not_meaningful_noise_filtered():
    old_text = "welcome to our product page for teams everywhere"
    new_text = "welcome to our product page for teams everywhere."  # trailing punctuation only
    result = detect_change(old_text, new_text, {"title": "X"}, {"title": "X"})
    assert result.meaningful is False


def test_real_pricing_change_is_meaningful():
    old_text = "pro plan is 29 dollars per month for teams of five"
    new_text = "pro plan is 39 dollars per month for teams of five and now includes ai reporting"
    old_struct = {"prices": [{"currency": "$", "amount": 29, "period": "month"}], "title": "Pricing"}
    new_struct = {"prices": [{"currency": "$", "amount": 39, "period": "month"}], "title": "Pricing"}
    result = detect_change(old_text, new_text, old_struct, new_struct)
    assert result.meaningful is True
    assert result.change_score > 0
    assert "prices" in result.structured_changes
