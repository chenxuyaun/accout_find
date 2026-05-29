from __future__ import annotations

from backend.models import AccountIdentity
from backend.services.privacy_guard import mask_email, mask_phone

IMPORTANCE_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _sort_accounts(accounts: list[AccountIdentity]) -> list[AccountIdentity]:
    return sorted(accounts, key=lambda item: IMPORTANCE_ORDER.get(str(item.importance), 9))


def check_phone_migration(phone: str, accounts: list[AccountIdentity]) -> dict:
    phone_masked = mask_phone(phone)
    affected = [
        account
        for account in accounts
        if any(binding.valueMasked == phone_masked for binding in account.bindings)
    ]
    affected = _sort_accounts(affected)
    return {
        "status": "ok",
        "affectedAccounts": affected,
        "migrationPriority": [account.platformName for account in affected],
        "steps": [
            "先迁移 critical/high 账号的绑定手机号。",
            "确认 MFA 设备和备用恢复邮箱可用。",
            "完成每个账号迁移后更新最近确认时间。",
        ],
    }


def check_email_migration(email: str, accounts: list[AccountIdentity]) -> dict:
    email_masked = mask_email(email)
    affected = [
        account
        for account in accounts
        if any(binding.valueMasked == email_masked for binding in account.bindings)
    ]
    affected = _sort_accounts(affected)
    return {
        "status": "ok",
        "affectedAccounts": affected,
        "migrationPriority": [account.platformName for account in affected],
        "steps": [
            "先替换 critical/high 账号的登录邮箱或恢复邮箱。",
            "确认新邮箱可收取官方验证邮件。",
            "旧邮箱注销前至少保留一个完整账单周期。",
        ],
    }
