from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import uuid4

from backend.services.privacy_guard import mask_email, mask_phone, redact_text, safety_block

KNOWN_PLATFORMS = ("腾讯云", "微信", "Apple ID", "学校邮箱", "GitHub", "支付宝", "网盘", "购物平台")

LOGIN_KEYWORDS = {
    "wechat": ("微信", "WeChat"),
    "qq": ("QQ",),
    "apple": ("Apple", "Apple ID"),
    "google": ("Google",),
    "github": ("GitHub",),
    "email": ("邮箱", "email", "@"),
    "phone": ("手机号", "手机", "短信"),
}


def extract_clues(text: str, source_type: str = "manual") -> dict:
    blocked = safety_block(text)
    if blocked:
        return blocked

    platforms = [name for name in KNOWN_PLATFORMS if name.lower() in text.lower()]
    emails = re.findall(r"[\w.+-]+@[\w.-]+\.\w+", text)
    phones = re.findall(r"\b1\d{10}\b", text)
    login_methods = [
        method
        for method, keywords in LOGIN_KEYWORDS.items()
        if any(keyword.lower() in text.lower() for keyword in keywords)
    ]

    return {
        "status": "ok",
        "platforms": platforms,
        "emailsMasked": [mask_email(email) for email in emails],
        "phonesMasked": [mask_phone(phone) for phone in phones],
        "loginMethods": sorted(set(login_methods)),
        "evidence": {
            "id": str(uuid4()),
            "type": source_type,
            "contentRedacted": redact_text(text),
            "createdAt": datetime.now(timezone.utc).isoformat(),
        },
        "confidence": 0.78 if platforms or emails or phones or login_methods else 0.35,
    }
