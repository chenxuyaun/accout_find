"""LLM 配置持久化存储

使用 SQLite 轻量存储 LLM 配置偏好（不存储 API Key）。
API Key 由 LiteLLM Proxy 管理，后端只存储"当前使用的模型名"等偏好设置。

数据库文件位置：backend/data/llm_config.db
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from threading import Lock

_db_lock = Lock()


def _db_path() -> Path:
    data_dir = Path(os.getenv("PASSWORD_MEMORY_DATA_DIR", "backend/data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "llm_config.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """初始化数据库表"""
    with _db_lock:
        conn = _get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS llm_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            conn.commit()
        finally:
            conn.close()


def get_preference(key: str, default: str = "") -> str:
    """读取偏好设置"""
    with _db_lock:
        conn = _get_connection()
        try:
            row = conn.execute(
                "SELECT value FROM llm_preferences WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else default
        finally:
            conn.close()


def set_preference(key: str, value: str) -> None:
    """写入偏好设置"""
    with _db_lock:
        conn = _get_connection()
        try:
            conn.execute(
                """
                INSERT INTO llm_preferences (key, value, updated_at)
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = datetime('now')
                """,
                (key, value),
            )
            conn.commit()
        finally:
            conn.close()


def delete_preference(key: str) -> None:
    """删除偏好设置"""
    with _db_lock:
        conn = _get_connection()
        try:
            conn.execute("DELETE FROM llm_preferences WHERE key = ?", (key,))
            conn.commit()
        finally:
            conn.close()


def get_all_preferences() -> dict[str, str]:
    """读取所有偏好设置"""
    with _db_lock:
        conn = _get_connection()
        try:
            rows = conn.execute("SELECT key, value FROM llm_preferences").fetchall()
            return {row["key"]: row["value"] for row in rows}
        finally:
            conn.close()


# 初始化
init_db()
