import pytest
from app.security.ssrf import validate_and_resolve_url, is_safe_url, SSRFValidationError


def test_blocks_localhost():
    with pytest.raises(SSRFValidationError):
        validate_and_resolve_url("http://localhost/admin")


def test_blocks_loopback_ip():
    with pytest.raises(SSRFValidationError):
        validate_and_resolve_url("http://127.0.0.1/secret")


def test_blocks_private_ip_10():
    with pytest.raises(SSRFValidationError):
        validate_and_resolve_url("http://10.0.0.5/internal")


def test_blocks_private_ip_192():
    with pytest.raises(SSRFValidationError):
        validate_and_resolve_url("http://192.168.1.1/router")


def test_blocks_cloud_metadata_endpoint():
    with pytest.raises(SSRFValidationError):
        validate_and_resolve_url("http://169.254.169.254/latest/meta-data/")


def test_blocks_disallowed_scheme():
    with pytest.raises(SSRFValidationError):
        validate_and_resolve_url("file:///etc/passwd")
    with pytest.raises(SSRFValidationError):
        validate_and_resolve_url("ftp://example.com/file")


def test_blocks_credentials_in_url():
    with pytest.raises(SSRFValidationError):
        validate_and_resolve_url("http://user:pass@example.com/")


def test_allows_public_ip_literal():
    # 8.8.8.8 is a public Google DNS IP — should validate fine (no network call needed).
    result = validate_and_resolve_url("http://8.8.8.8/")
    assert result.resolved_ip == "8.8.8.8"


def test_is_safe_url_helper_false_for_private():
    assert is_safe_url("http://10.1.1.1/") is False


def test_is_safe_url_helper_true_for_public_ip():
    assert is_safe_url("https://1.1.1.1/") is True


def test_is_safe_url_verbose_returns_reason_on_failure():
    from app.security.ssrf import is_safe_url_verbose
    safe, reason = is_safe_url_verbose("http://10.1.1.1/")
    assert safe is False
    assert reason is not None
    assert "10.1.1.1" in reason or "not publicly routable" in reason


def test_is_safe_url_verbose_returns_no_reason_on_success():
    from app.security.ssrf import is_safe_url_verbose
    safe, reason = is_safe_url_verbose("https://1.1.1.1/")
    assert safe is True
    assert reason is None
