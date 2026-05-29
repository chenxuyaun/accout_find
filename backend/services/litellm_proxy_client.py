"""LiteLLM Proxy 客户端

封装对 LiteLLM Proxy 的管理 API 和聊天接口的调用。
- 管理 API：模型 CRUD、虚拟密钥管理
- 聊天接口：OpenAI 兼容的 /v1/chat/completions

配置来源：
- LITELLM_PROXY_URL：LiteLLM Proxy 地址，默认 http://localhost:4000
- LITELLM_MASTER_KEY：管理后台和管理 API 的认证密钥
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class ModelInfo:
    """LiteLLM 中的模型信息"""
    model_name: str
    model_info: dict = field(default_factory=dict)
    litellm_params: dict = field(default_factory=dict)


def _proxy_url() -> str:
    return os.getenv("LITELLM_PROXY_URL", "http://localhost:4000").rstrip("/")


def _master_key() -> str:
    return os.getenv("LITELLM_MASTER_KEY", "sk-litellm-master-key")


def _admin_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_master_key()}",
        "Content-Type": "application/json",
    }


# ============================================================
# 管理 API
# ============================================================

async def list_models() -> list[ModelInfo]:
    """获取 LiteLLM Proxy 中已配置的所有模型"""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{_proxy_url()}/model/info",
            headers=_admin_headers(),
        )
        resp.raise_for_status()
        data = resp.json()
        models = []
        for item in data.get("data", []):
            models.append(ModelInfo(
                model_name=item.get("model_name", ""),
                model_info=item.get("model_info", {}),
                litellm_params=item.get("litellm_params", {}),
            ))
        return models


async def add_model(
    model_name: str,
    provider: str,
    model: str,
    api_key: str = "",
    api_base: str = "",
    rpm: int = 100,
    tpm: int = 100000,
    **extra_params: Any,
) -> dict:
    """通过管理 API 动态添加模型

    Args:
        model_name: 在 LiteLLM 中的别名（如 "my-gpt-4"）
        provider: 提供商（如 "openai", "anthropic", "openai_like"）
        model: 实际模型名（如 "gpt-4o", "claude-3-5-sonnet-20241022"）
        api_key: API Key
        api_base: 自定义 API 端点（用于 Ollama、vLLM 等）
        rpm: 每分钟请求限制
        tpm: 每分钟 token 限制
        **extra_params: 其他 litellm 参数

    Returns:
        dict: 添加结果
    """
    litellm_params: dict[str, Any] = {
        "model": f"{provider}/{model}",
        "rpm": rpm,
        "tpm": tpm,
    }
    if api_key:
        litellm_params["api_key"] = api_key
    if api_base:
        litellm_params["api_base"] = api_base
    litellm_params.update(extra_params)

    payload = {
        "model_name": model_name,
        "litellm_params": litellm_params,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{_proxy_url()}/model/new",
            headers=_admin_headers(),
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


async def delete_model(model_name: str) -> dict:
    """通过管理 API 删除模型

    Args:
        model_name: 要删除的模型别名

    Returns:
        dict: 删除结果
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{_proxy_url()}/model/delete",
            headers=_admin_headers(),
            json={"model_name": model_name},
        )
        resp.raise_for_status()
        return resp.json()


async def test_model(model_name: str, message: str = "Hello, this is a test.") -> dict:
    """测试模型是否可用（发送一条简单的聊天请求）

    Args:
        model_name: 模型别名
        message: 测试消息

    Returns:
        dict: 包含 reply 和 model_name 的字典
    """
    try:
        result = await chat_completion(
            model=model_name,
            messages=[{"role": "user", "content": message}],
            max_tokens=50,
        )
        return {
            "ok": True,
            "model_name": model_name,
            "reply": result.get("choices", [{}])[0].get("message", {}).get("content", ""),
        }
    except Exception as e:
        return {
            "ok": False,
            "model_name": model_name,
            "error": str(e),
        }


async def health_check() -> dict:
    """检查 LiteLLM Proxy 是否运行正常"""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{_proxy_url()}/health")
        resp.raise_for_status()
        return resp.json()


# ============================================================
# 聊天接口（OpenAI 兼容）
# ============================================================

async def chat_completion(
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 1000,
    stream: bool = False,
    api_key: str | None = None,
) -> dict:
    """调用 LiteLLM Proxy 的 OpenAI 兼容聊天接口

    Args:
        model: LiteLLM 中的模型别名
        messages: 消息列表
        temperature: 温度参数
        max_tokens: 最大 token 数
        stream: 是否流式响应
        api_key: 虚拟密钥（可选，使用虚拟密钥代替 master key）

    Returns:
        dict: 非流式响应时返回完整结果
    """
    headers = {
        "Authorization": f"Bearer {api_key or _master_key()}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{_proxy_url()}/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


async def chat_completion_stream(
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 1000,
    api_key: str | None = None,
):
    """流式调用 LiteLLM Proxy 的聊天接口

    Args:
        model: LiteLLM 中的模型别名
        messages: 消息列表
        temperature: 温度参数
        max_tokens: 最大 token 数
        api_key: 虚拟密钥（可选）

    Yields:
        str: 流式返回的文本块
    """
    headers = {
        "Authorization": f"Bearer {api_key or _master_key()}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream(
            "POST",
            f"{_proxy_url()}/v1/chat/completions",
            headers=headers,
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
