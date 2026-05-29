from __future__ import annotations

import re

UNSAFE_REQUEST_KEYWORDS = (
    "绕过",
    "破解",
    "撞库",
    "钓鱼",
    "社工",
    "找回别人的账号",
    "冒用",
    "bypass",
    "crack",
    "phishing",
    "credential stuffing",
    "social engineering",
)

SENSITIVE_PATTERNS = (
    r"(密码|password|pwd)\s*[:：]\s*\S+",
    r"(验证码|verification code|code)\s*[:：]\s*\d{4,8}",
    r"(恢复码|recovery code)\s*[:：]\s*[a-zA-Z0-9-]{6,}",
    r"(token|secret)\s*[:：]\s*\S+",
)


def mask_email(value: str) -> str:
    match = re.fullmatch(r"([^@\s]{1,})(@[^@\s]+\.[^@\s]+)", value)
    if not match:
        return value
    prefix, domain = match.groups()
    visible = prefix[:2] if len(prefix) >= 2 else prefix[:1]
    return f"{visible}***{domain}"


def mask_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) < 7:
        return value
    return f"{digits[:3]}****{digits[-4:]}"


def mask_identifier(value: str) -> str:
    if "@" in value:
        return mask_email(value)
    if re.search(r"\d{7,}", value):
        return mask_phone(value)
    return value


def redact_text(text: str) -> str:
    text = re.sub(r"[\w.+-]+@[\w.-]+\.\w+", lambda m: mask_email(m.group(0)), text)
    text = re.sub(r"\b\+?\d[\d -]{8,}\d\b", lambda m: mask_phone(m.group(0)), text)
    return text


def detect_sensitive_secret(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in SENSITIVE_PATTERNS)


def is_unsafe_request(text: str) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in UNSAFE_REQUEST_KEYWORDS)


def safety_block(text: str) -> dict | None:
    if detect_sensitive_secret(text):
        return {
            "status": "safety_blocked",
            "code": "sensitive_secret_detected",
            "message": "检测到疑似密码、验证码、恢复码正文或密钥。请删除敏感内容后再提交。",
        }
    if is_unsafe_request(text):
        return {
            "status": "safety_blocked",
            "code": "unsafe_request_rejected",
            "message": "我不能协助绕过验证、破解、社工、钓鱼、冒用或找回他人账号。",
        }
    return None
