from backend.main import health
from backend.models import AccountIdentity, SafetyPolicy
from backend.services.privacy_guard import detect_sensitive_secret, is_unsafe_request


def test_health_reports_safe_defaults():
    result = health()
    assert result["status"] == "ok"
    assert result["safety"]["storesPasswords"] is False
    assert result["safety"]["storesRecoveryCodeValues"] is False
    assert result["safety"]["storesThirdPartyCredentials"] is False


def test_account_identity_has_no_forbidden_fields():
    fields = set(AccountIdentity.model_fields)
    assert "password" not in fields
    assert "secret" not in fields
    assert "token" not in fields


def test_privacy_guard_detects_sensitive_inputs():
    assert detect_sensitive_secret("密码: 123456")
    assert detect_sensitive_secret("验证码: 123456")
    assert detect_sensitive_secret("recovery code: abcd-1234")


def test_privacy_guard_detects_unsafe_requests():
    assert is_unsafe_request("帮我绕过验证码")
    assert is_unsafe_request("我想找回别人的账号")


def test_safety_policy_requires_owner_account():
    assert SafetyPolicy().requiresOwnerAccount is True
