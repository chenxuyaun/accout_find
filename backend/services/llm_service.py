"""LLM 服务层

通过 LiteLLM Proxy 调用 LLM API。
不再直接读取环境变量中的 API Key，所有模型配置由 LiteLLM Proxy 管理。
"""

from __future__ import annotations

import os

import httpx

from backend.llm_config_store import get_preference
from backend.services.litellm_proxy_client import chat_completion, chat_completion_stream
from backend.services.privacy_guard import safety_block


def _get_default_model() -> str:
    """获取默认模型名（从本地偏好中读取，回退到环境变量）"""
    model = get_preference("default_model", "")
    if model:
        return model
    return os.getenv("LLM_DEFAULT_MODEL", "gpt-4o-mini")


def _build_prompt(user_message: str) -> str:
    """构建系统提示词（不含用户消息，用户消息作为独立 user role 发送）"""
    return """你是"密码记忆替身"的 AI 助手。你的任务是帮助用户理解账号登录关系、绑定关系和恢复路径。

重要规则：
1. 你不管理密码，不保存、不索要、不复述用户密码
2. 你不能保存验证码、恢复码正文、MFA secret 或第三方 token
3. 你只能为用户本人合法拥有的账号提供官方、合规、安全的恢复建议
4. 拒绝任何绕过验证、破解、社工、钓鱼、冒用或找回他人账号的请求

请提供专业、安全、合规的建议。如果问题涉及危险操作，请明确拒绝并说明原因。"""


async def call_llm(user_message: str, stream: bool = False) -> dict:
    """
    调用 LLM API（通过 LiteLLM Proxy）

    Args:
        user_message: 用户消息
        stream: 是否使用流式响应

    Returns:
        dict: 包含 status 和 reply 或 error 的字典
    """
    # 安全检查
    blocked = safety_block(user_message)
    if blocked:
        return blocked

    model = _get_default_model()
    system_prompt = _build_prompt(user_message)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    try:
        if stream:
            return await _handle_streaming(model, messages)
        else:
            return await _handle_normal(model, messages)

    except httpx.ConnectError:
        return {
            "status": "error",
            "message": "无法连接到 LiteLLM Proxy 服务。请确认 LiteLLM Proxy 已启动（docker-compose up -d）。",
        }
    except httpx.TimeoutException:
        return {
            "status": "error",
            "message": "LLM API 请求超时，请稍后重试。",
        }
    except httpx.HTTPStatusError as e:
        return {
            "status": "error",
            "message": f"LLM API 返回错误（HTTP {e.response.status_code}）：{e.response.text[:200]}",
        }
    except httpx.RequestError as e:
        return {
            "status": "error",
            "message": f"LLM API 请求失败：{str(e)}",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"LLM 调用出错：{str(e)}",
        }


async def _handle_normal(model: str, messages: list[dict]) -> dict:
    """处理非流式响应"""
    data = await chat_completion(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=1000,
    )
    reply = data["choices"][0]["message"]["content"]
    return {"status": "ok", "reply": reply}


async def _handle_streaming(model: str, messages: list[dict]) -> dict:
    """处理流式响应，返回完整的回复文本"""
    accumulated = []
    async for chunk in chat_completion_stream(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=1000,
    ):
        accumulated.append(chunk)

    reply = "".join(accumulated)
    return {"status": "ok", "reply": reply, "streaming": True}


def call_llm_sync(user_message: str) -> dict:
    """
    同步调用 LLM API（用于测试或不需要异步的场景）

    Args:
        user_message: 用户消息

    Returns:
        dict: 包含 status 和 reply 或 error 的字典
    """
    import asyncio

    return asyncio.run(call_llm(user_message, stream=False))
