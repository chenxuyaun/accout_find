#!/usr/bin/env python3
"""LiteLLM Proxy 启动前密钥安全检查脚本。

检查 .env 中的关键密钥是否已从默认值更换，防止使用弱密钥启动服务。

用法：
    python check_keys.py [--strict]
    --strict: 发现默认密钥时退出码非零，阻止启动
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ENV_FILE = Path(__file__).parent / ".env"

# 需要检查的密钥及其默认值（视为不安全的占位值）
DANGEROUS_DEFAULTS: dict[str, set[str]] = {
    "LITELLM_MASTER_KEY": {
        "sk-litellm-master-key",
    },
    "LITELLM_SALT_KEY": {
        "litellm-salt-key",
        "litellm-salt-key-change-in-production",
    },
    "POSTGRES_PASSWORD": {
        "litellm_pass",
        "postgres",
        "password",
    },
}

# 最小密钥长度要求
MIN_KEY_LENGTH: dict[str, int] = {
    "LITELLM_MASTER_KEY": 20,
    "LITELLM_SALT_KEY": 16,
    "POSTGRES_PASSWORD": 10,
}


def _parse_env(path: Path) -> dict[str, str]:
    """简易 .env 解析器（不依赖外部库）。"""
    if not path.exists():
        print(f"[ERROR] 未找到 .env 文件: {path}")
        print("  请从 .env.example 复制：cp .env.example .env")
        sys.exit(1)

    env: dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            env[key] = value
    return env


def check_keys(strict: bool = False) -> int:
    """检查密钥安全性，返回退出码。"""
    env = _parse_env(ENV_FILE)
    issues: list[str] = []
    warnings: list[str] = []

    for key, dangerous_values in DANGEROUS_DEFAULTS.items():
        value = env.get(key, "")
        if not value:
            warnings.append(f"[WARNING] {key} 未设置")
            continue

        # 检查是否使用了默认值
        if value.lower() in dangerous_values:
            issues.append(
                f"[CRITICAL] {key} 使用了默认值 '{value}'，"
                f"生产环境必须更换！"
            )

        # 检查密钥长度
        min_len = MIN_KEY_LENGTH.get(key, 0)
        if len(value) < min_len:
            issues.append(
                f"[CRITICAL] {key} 长度不足（当前 {len(value)} 字符，"
                f"最少 {min_len} 字符）"
            )

    if not issues and not warnings:
        print("[OK] 所有密钥检查通过 ✓")
        return 0

    if warnings:
        for w in warnings:
            print(w)
        print()

    if issues:
        print("=" * 60)
        print("  安全警告：检测到不安全的密钥配置")
        print("=" * 60)
        for issue in issues:
            print(f"  {issue}")
        print()
        print("  生产环境请更换所有默认密钥，生成方式：")
        print('    python -c "import secrets; print(\'sk-\' + secrets.token_hex(32))"')
        print('    python -c "import secrets; print(secrets.token_hex(32))"')
        print('    python -c "import secrets; print(secrets.token_urlsafe(24))"')
        print("=" * 60)

        if strict:
            return 1

    return 0


if __name__ == "__main__":
    strict = "--strict" in sys.argv
    sys.exit(check_keys(strict=strict))
