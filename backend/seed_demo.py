from __future__ import annotations

from backend.models import AccountIdentity
from backend.storage import save_accounts


def demo_accounts() -> list[AccountIdentity]:
    return [
        AccountIdentity(
            platformName="腾讯云",
            loginUrl="https://cloud.tencent.com/login",
            registerMethod="微信第三方登录",
            loginMethods=[
                {"type": "wechat", "identifierHint": "微信", "confidence": 0.9},
                {"type": "email", "identifierHint": "demo@example.com", "confidence": 0.7},
            ],
            bindings=[
                {"kind": "phone", "value": "13812345678", "status": "old", "confidence": 0.9},
                {"kind": "email", "value": "demo@example.com", "status": "active", "confidence": 0.8},
            ],
            mfaEnabled=True,
            authenticatorLocationHint="旧手机验证器 App",
            recoveryPaths=[
                {"kind": "recovery_code_location", "locationHint": "纸质笔记本第 3 页", "confidence": 0.8}
            ],
            importance="critical",
            riskTags=["旧手机号仍绑定"],
        ),
        AccountIdentity(
            platformName="微信",
            loginMethods=[{"type": "phone", "identifierHint": "13900001111", "confidence": 0.8}],
            bindings=[{"kind": "phone", "value": "13900001111", "status": "active", "confidence": 0.8}],
            mfaEnabled=True,
            recoveryPaths=[{"kind": "phone", "locationHint": "当前主力手机号", "confidence": 0.7}],
            importance="critical",
        ),
        AccountIdentity(
            platformName="Apple ID",
            loginUrl="https://appleid.apple.com/",
            loginMethods=[{"type": "email", "identifierHint": "apple-demo@example.com", "confidence": 0.8}],
            bindings=[{"kind": "device", "valueMasked": "iPhone 13", "status": "active", "confidence": 0.8}],
            mfaEnabled=True,
            recoveryPaths=[{"kind": "mfa_device", "locationHint": "常用 iPhone", "confidence": 0.8}],
            importance="critical",
        ),
        AccountIdentity(
            platformName="GitHub",
            loginUrl="https://github.com/login",
            loginMethods=[{"type": "email", "identifierHint": "dev@example.com", "confidence": 0.8}],
            bindings=[{"kind": "email", "value": "dev@example.com", "status": "active", "confidence": 0.8}],
            mfaEnabled=True,
            recoveryPaths=[{"kind": "support_ticket", "locationHint": "官方支持入口", "confidence": 0.6}],
            importance="high",
        ),
        AccountIdentity(
            platformName="学校邮箱",
            loginMethods=[{"type": "email", "identifierHint": "student@example.edu", "confidence": 0.8}],
            bindings=[{"kind": "email", "value": "student@example.edu", "status": "old", "confidence": 0.7}],
            recoveryPaths=[{"kind": "support_ticket", "locationHint": "学校 IT 服务台", "confidence": 0.7}],
            importance="high",
            riskTags=["毕业邮箱可能停用"],
        ),
        AccountIdentity(
            platformName="支付宝",
            loginMethods=[{"type": "phone", "identifierHint": "13812345678", "confidence": 0.8}],
            bindings=[{"kind": "phone", "value": "13812345678", "status": "old", "confidence": 0.8}],
            mfaEnabled=True,
            recoveryPaths=[{"kind": "phone", "locationHint": "旧手机号", "confidence": 0.7}],
            importance="critical",
            riskTags=["旧手机号仍绑定"],
        ),
        AccountIdentity(
            platformName="网盘",
            loginMethods=[{"type": "email", "identifierHint": "files@example.com", "confidence": 0.7}],
            bindings=[{"kind": "email", "value": "files@example.com", "status": "active", "confidence": 0.7}],
            recoveryPaths=[],
            importance="medium",
        ),
        AccountIdentity(
            platformName="购物平台",
            loginMethods=[{"type": "phone", "identifierHint": "13900001111", "confidence": 0.7}],
            bindings=[{"kind": "phone", "value": "13900001111", "status": "active", "confidence": 0.7}],
            recoveryPaths=[{"kind": "phone", "locationHint": "当前主力手机号", "confidence": 0.7}],
            importance="medium",
        ),
    ]


def seed_demo_accounts() -> list[AccountIdentity]:
    accounts = demo_accounts()
    save_accounts(accounts)
    return accounts


def main() -> None:
    accounts = seed_demo_accounts()
    print(f"Seeded {len(accounts)} demo accounts.")


if __name__ == "__main__":
    main()
