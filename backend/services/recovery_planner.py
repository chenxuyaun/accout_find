from __future__ import annotations

from backend.models import AccountIdentity
from backend.schemas import SafetyBlockedResponse


def build_recovery_plan(platform_name: str, accounts: list[AccountIdentity], claim_ownership: bool) -> dict:
    if not claim_ownership:
        return SafetyBlockedResponse(
            code="ownership_required",
            message="找回建议仅适用于你本人合法拥有的账号，请先确认账号归属。",
        ).model_dump()

    account = next((item for item in accounts if item.platformName == platform_name), None)
    if not account:
        return {
            "status": "not_found",
            "code": "account_not_found",
            "message": "未找到该平台的账号线索。",
        }

    methods = [method.type for method in account.loginMethods]
    official_hints = [
        account.loginUrl or "使用平台官方网站或 App 内的官方账号找回入口",
        "不要使用非官方代找回、代验证或远程协助链接",
    ]

    return {
        "status": "ok",
        "platformName": account.platformName,
        "legalReminder": "以下建议只适用于你本人合法拥有的账号，并且应通过官方路径完成。",
        "possibleLoginMethods": methods,
        "bindings": [binding.model_dump(mode="json") for binding in account.bindings],
        "officialPathHints": official_hints,
        "recommendedSteps": [
            "先尝试最近确认过或置信度最高的登录方式。",
            "检查已记录的绑定邮箱、手机号或第三方登录关系是否仍可用。",
            "确认 MFA 设备位置和恢复码存放位置提示，但不要录入恢复码正文。",
            "通过平台官方找回入口提交本人身份验证。",
        ],
        "risks": account.riskTags,
        "uncertainFields": [
            item
            for item in [
                "未记录最近确认时间" if not account.lastConfirmedAt else "",
                "部分绑定关系可能已过期",
            ]
            if item
        ],
    }
