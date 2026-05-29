from __future__ import annotations

import logging
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

_KEY_FILE = Path(os.getenv("FERNET_KEY_FILE", "backend/data/.fernet_key"))


def _load_key() -> bytes:
    """加载 Fernet 密钥，优先从环境变量读取，其次从文件读取，最后自动生成并持久化。"""
    env_key = os.getenv("FERNET_KEY", "")
    if env_key:
        return env_key.encode("utf-8")

    if _KEY_FILE.exists():
        return _KEY_FILE.read_bytes()

    # 首次启动：生成密钥并持久化
    new_key = Fernet.generate_key()
    _KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    _KEY_FILE.write_bytes(new_key)
    logger.warning("已生成新的加密密钥并保存到 %s，请妥善保管。", _KEY_FILE)
    return new_key


def encrypt_text(value: str) -> bytes:
    cipher = Fernet(_load_key())
    return cipher.encrypt(value.encode("utf-8"))


def decrypt_text(value: bytes) -> str:
    cipher = Fernet(_load_key())
    try:
        return cipher.decrypt(value).decode("utf-8")
    except InvalidToken:
        logger.error("解密失败：加密密钥不匹配或数据已损坏。")
        raise
