from __future__ import annotations

from backend.models import AccountIdentity, SecurityRisk


def audit_accounts(accounts: list[AccountIdentity]) -> dict:
    risks: list[SecurityRisk] = []
    for account in accounts:
        if account.importance in ("high", "critical") and not account.mfaEnabled:
            risks.append(
                SecurityRisk(
                    level="high",
                    title=f"{account.platformName} 未开启 MFA",
                    reason="高价值账号缺少二次验证保护。",
                    suggestion="在官方设置中开启 MFA，并只记录验证器位置提示。",
                )
            )
        if not account.recoveryPaths:
            risks.append(
                SecurityRisk(
                    level="medium",
                    title=f"{account.platformName} 缺少恢复路径记录",
                    reason="未记录恢复邮箱、手机号、MFA 设备或恢复码位置提示。",
                    suggestion="补充至少一个备用恢复路径，并避免记录恢复码正文。",
                )
            )
        if any(binding.status == "old" for binding in account.bindings):
            risks.append(
                SecurityRisk(
                    level="high" if account.importance in ("high", "critical") else "medium",
                    title=f"{account.platformName} 仍存在旧绑定",
                    reason="旧手机号、旧邮箱或旧设备可能成为账号恢复单点风险。",
                    suggestion="登录官方入口更新绑定关系，并确认新恢复路径可用。",
                )
            )

    score = max(0, 100 - len(risks) * 8)
    return {"status": "ok", "score": score, "risks": risks}
