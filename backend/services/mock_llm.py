from __future__ import annotations


def mock_llm(user_message: str) -> str:
    if "找回" in user_message or "忘" in user_message:
        return "请提供平台名称，并确认这是你本人合法拥有的账号。我会基于已记录线索生成官方找回路径。"
    if "换手机号" in user_message:
        return "请提供要迁移的手机号。我会列出受影响账号、迁移优先级和官方操作建议。"
    if "体检" in user_message:
        return "可以运行账号安全体检，检查旧绑定、MFA、恢复路径和长期未确认账号。"
    return "我可以帮助整理账号身份线索、绑定关系、恢复路径和安全提醒，但不会保存密码、验证码或恢复码正文。"
