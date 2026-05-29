from __future__ import annotations

import json
import os
import time
from pathlib import Path

from backend.encryption import decrypt_text, encrypt_text
from backend.models import AccountIdentity
from backend.services.privacy_guard import mask_identifier

_last_load_time = 0.0
_cache_ttl = 2.0  # 缓存有效期（秒）
_cached_accounts: list[AccountIdentity] = []


def data_file() -> Path:
    return Path(os.getenv("PASSWORD_MEMORY_DATA_FILE", "backend/data/accounts.enc"))


def _account_for_output(account: AccountIdentity) -> AccountIdentity:
    for binding in account.bindings:
        if binding.value and not binding.valueMasked:
            binding.valueMasked = mask_identifier(binding.value)
        binding.value = None
    for method in account.loginMethods:
        if method.identifierHint:
            method.identifierHint = mask_identifier(method.identifierHint)
    return account


def load_accounts() -> list[AccountIdentity]:
    path = data_file()
    if not path.exists():
        return []
    raw = decrypt_text(path.read_bytes())
    payload = json.loads(raw)
    return [AccountIdentity.model_validate(item) for item in payload]


def save_accounts(accounts: list[AccountIdentity]) -> None:
    global _last_load_time, _cached_accounts
    path = data_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [account.model_dump(mode="json") for account in accounts]
    path.write_bytes(encrypt_text(json.dumps(payload, ensure_ascii=False)))
    # 写入后立即刷新缓存
    _cached_accounts = [_account_for_output(account.model_copy(deep=True)) for account in accounts]
    _last_load_time = time.monotonic()


def list_accounts() -> list[AccountIdentity]:
    global _last_load_time, _cached_accounts
    now = time.monotonic()
    if now - _last_load_time < _cache_ttl and _cached_accounts:
        return _cached_accounts
    _cached_accounts = [_account_for_output(account.model_copy(deep=True)) for account in load_accounts()]
    _last_load_time = now
    return _cached_accounts


def get_account(account_id: str) -> AccountIdentity | None:
    for account in list_accounts():
        if account.id == account_id:
            return account
    return None


def create_account(account: AccountIdentity) -> AccountIdentity:
    accounts = load_accounts()
    for binding in account.bindings:
        if binding.value and not binding.valueMasked:
            binding.valueMasked = mask_identifier(binding.value)
    accounts.append(account)
    save_accounts(accounts)
    return _account_for_output(account.model_copy(deep=True))


def update_account(account_id: str, patch: dict) -> AccountIdentity | None:
    accounts = load_accounts()
    for index, account in enumerate(accounts):
        if account.id == account_id:
            data = account.model_dump(mode="json")
            data.update(patch)
            updated = AccountIdentity.model_validate(data)
            accounts[index] = updated
            save_accounts(accounts)
            return _account_for_output(updated.model_copy(deep=True))
    return None


def delete_account(account_id: str) -> bool:
    accounts = load_accounts()
    kept = [account for account in accounts if account.id != account_id]
    if len(kept) == len(accounts):
        return False
    save_accounts(kept)
    return True
