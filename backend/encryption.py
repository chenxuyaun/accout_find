from __future__ import annotations

import os

from cryptography.fernet import Fernet

_DEFAULT_KEY = Fernet.generate_key().decode()


def get_fernet() -> Fernet:
    key = os.getenv("FERNET_KEY", _DEFAULT_KEY)
    return Fernet(key.encode())


def encrypt_text(value: str) -> bytes:
    return get_fernet().encrypt(value.encode("utf-8"))


def decrypt_text(value: bytes) -> str:
    return get_fernet().decrypt(value).decode("utf-8")
