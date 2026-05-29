import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client_with_temp_storage_fixture(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setenv("PASSWORD_MEMORY_DATA_FILE", str(tmp_path / "accounts.enc"))
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())
    return TestClient(app)
