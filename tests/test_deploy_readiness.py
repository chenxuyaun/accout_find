import importlib

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from backend.storage import load_accounts


def test_cors_allows_configured_frontend_origin(monkeypatch, tmp_path):
    monkeypatch.setenv("PASSWORD_MEMORY_DATA_FILE", str(tmp_path / "accounts.enc"))
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("CORS_ORIGINS", "https://demo.example.com")
    from backend import main

    reloaded_main = importlib.reload(main)

    with TestClient(reloaded_main.app) as client:
        response = client.options(
            "/health",
            headers={
                "Origin": "https://demo.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://demo.example.com"


def test_cors_allows_local_vite_origin_by_default(monkeypatch, tmp_path):
    monkeypatch.setenv("PASSWORD_MEMORY_DATA_FILE", str(tmp_path / "accounts.enc"))
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    from backend import main

    reloaded_main = importlib.reload(main)

    with TestClient(reloaded_main.app) as client:
        response = client.options(
            "/health",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_seed_demo_writes_eight_safe_demo_accounts(monkeypatch, tmp_path):
    monkeypatch.setenv("PASSWORD_MEMORY_DATA_FILE", str(tmp_path / "accounts.enc"))
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())

    from backend.seed_demo import seed_demo_accounts

    accounts = seed_demo_accounts()

    assert len(accounts) == 8
    assert len(load_accounts()) == 8
    assert all(account.platformName for account in accounts)
    serialized = " ".join(account.model_dump_json() for account in accounts).lower()
    assert "password" not in serialized
    assert "token" not in serialized
    assert "secret" not in serialized


def test_demo_seed_on_empty_populates_accounts_on_startup(monkeypatch, tmp_path):
    monkeypatch.setenv("PASSWORD_MEMORY_DATA_FILE", str(tmp_path / "accounts.enc"))
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("DEMO_SEED_ON_EMPTY", "true")
    from backend import main

    reloaded_main = importlib.reload(main)

    with TestClient(reloaded_main.app) as client:
        response = client.get("/accounts")

    assert response.status_code == 200
    accounts = response.json()
    assert len(accounts) == 8
    assert all(account["platformName"] for account in accounts)


def test_repo_hygiene_files_document_safe_demo_boundaries():
    gitignore = open(".gitignore", encoding="utf-8").read()
    readme = open("README.md", encoding="utf-8").read()

    assert "__pycache__/" in gitignore
    assert ".pytest_cache/" in gitignore
    assert "backend/data/*.enc" in gitignore
    assert "node_modules/" in gitignore
    assert ".env" in gitignore
    assert "密码记忆替身" in readme
    assert "Live Demo" in readme
    assert "Security Boundary" in readme
