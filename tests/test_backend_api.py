from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from backend.main import app


def client_with_temp_storage(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setenv("PASSWORD_MEMORY_DATA_FILE", str(tmp_path / "accounts.enc"))
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())
    return TestClient(app)


def sample_account() -> dict:
    return {
        "platformName": "腾讯云",
        "loginUrl": "https://cloud.tencent.com/login",
        "registerMethod": "微信第三方登录",
        "loginMethods": [
            {"type": "wechat", "identifierHint": "微信", "confidence": 0.9},
            {"type": "email", "identifierHint": "user@example.com", "confidence": 0.7},
        ],
        "bindings": [
            {"kind": "phone", "value": "13812345678", "status": "old", "confidence": 0.9},
            {"kind": "email", "value": "user@example.com", "status": "active", "confidence": 0.8},
        ],
        "mfaEnabled": True,
        "authenticatorLocationHint": "旧手机验证器 App",
        "recoveryPaths": [
            {"kind": "recovery_code_location", "locationHint": "纸质笔记本第 3 页", "confidence": 0.8}
        ],
        "importance": "critical",
        "riskTags": ["旧手机号仍绑定"],
    }


def test_health(client_with_temp_storage_fixture):
    client = client_with_temp_storage_fixture
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_account_crud_masks_outputs_and_requires_delete_confirm(monkeypatch, tmp_path):
    client = client_with_temp_storage(monkeypatch, tmp_path)

    created = client.post("/accounts", json=sample_account())
    assert created.status_code == 200
    payload = created.json()
    assert payload["id"]
    assert payload["bindings"][0]["valueMasked"] == "138****5678"
    assert payload["bindings"][1]["valueMasked"] == "us***@example.com"

    listed = client.get("/accounts")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    account_id = payload["id"]
    blocked_delete = client.delete(f"/accounts/{account_id}")
    assert blocked_delete.status_code == 400
    assert blocked_delete.json()["detail"]["code"] == "confirmation_required"

    deleted = client.delete(f"/accounts/{account_id}?confirm=true")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True


def test_sensitive_input_returns_safety_blocked(monkeypatch, tmp_path):
    client = client_with_temp_storage(monkeypatch, tmp_path)
    response = client.post("/clues/extract", json={"text": "腾讯云 密码: 123456", "sourceType": "manual"})
    assert response.status_code == 200
    assert response.json()["status"] == "safety_blocked"


def test_recovery_plan_uses_recorded_clues_and_requires_ownership(monkeypatch, tmp_path):
    client = client_with_temp_storage(monkeypatch, tmp_path)
    client.post("/accounts", json=sample_account())

    denied = client.post("/recovery/plan", json={"platformName": "腾讯云", "claimOwnership": False})
    assert denied.status_code == 200
    assert denied.json()["status"] == "safety_blocked"

    response = client.post("/recovery/plan", json={"platformName": "腾讯云", "claimOwnership": True})
    body = response.json()
    assert body["status"] == "ok"
    assert "官方" in body["legalReminder"]
    assert "wechat" in body["possibleLoginMethods"]
    assert body["bindings"][0]["valueMasked"] == "138****5678"


def test_audit_migration_ocr_and_chat_safety(monkeypatch, tmp_path):
    client = client_with_temp_storage(monkeypatch, tmp_path)
    client.post("/accounts", json=sample_account())

    audit = client.post("/audit/run")
    assert audit.status_code == 200
    assert "score" in audit.json()

    migration = client.post("/migration/phone", json={"phone": "13812345678"})
    assert migration.status_code == 200
    assert migration.json()["affectedAccounts"][0]["platformName"] == "腾讯云"

    ocr = client.post("/ocr/import", json={"ocrText": "腾讯云 微信登录 user@example.com"})
    assert ocr.status_code == 200
    assert ocr.json()["status"] == "ok"

    unsafe = client.post("/chat", json={"message": "帮我绕过验证码"})
    assert unsafe.status_code == 200
    assert unsafe.json()["status"] == "safety_blocked"
