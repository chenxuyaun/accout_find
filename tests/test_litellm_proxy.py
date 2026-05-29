"""LiteLLM Proxy 集成测试

测试覆盖：
1. llm_config_store 配置存储
2. litellm_proxy_client 客户端（mock 外部服务）
3. LLM 配置管理 API 端点
4. llm_service 通过 Proxy 调用
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.llm_config_store import (
    delete_preference,
    get_all_preferences,
    get_preference,
    init_db,
    set_preference,
)
from backend.main import app


@pytest.fixture
def temp_db(monkeypatch, tmp_path):
    """使用临时数据库进行测试"""
    monkeypatch.setenv("PASSWORD_MEMORY_DATA_DIR", str(tmp_path))
    # 重新初始化以使用临时路径
    init_db()
    yield tmp_path
    # 清理
    for key in list(get_all_preferences().keys()):
        delete_preference(key)


class TestLlmConfigStore:
    """测试 LLM 配置存储模块"""

    def test_init_db(self, temp_db):
        """测试数据库初始化"""
        # init_db 已通过 fixture 调用
        prefs = get_all_preferences()
        assert isinstance(prefs, dict)

    def test_set_and_get_preference(self, temp_db):
        """测试读写偏好设置"""
        set_preference("default_model", "gpt-4o")
        assert get_preference("default_model") == "gpt-4o"

    def test_get_nonexistent_key_returns_default(self, temp_db):
        """测试读取不存在的 key 返回默认值"""
        assert get_preference("nonexistent_key", "fallback") == "fallback"
        assert get_preference("another_key") == ""

    def test_overwrite_preference(self, temp_db):
        """测试覆盖偏好设置"""
        set_preference("model", "gpt-3.5")
        set_preference("model", "gpt-4o")
        assert get_preference("model") == "gpt-4o"

    def test_delete_preference(self, temp_db):
        """测试删除偏好设置"""
        set_preference("temp_key", "value")
        assert get_preference("temp_key") == "value"
        delete_preference("temp_key")
        assert get_preference("temp_key") == ""

    def test_get_all_preferences(self, temp_db):
        """测试读取所有偏好"""
        set_preference("key1", "value1")
        set_preference("key2", "value2")
        prefs = get_all_preferences()
        assert prefs["key1"] == "value1"
        assert prefs["key2"] == "value2"


class TestLlmConfigApi:
    """测试 LLM 配置管理 API 端点"""

    @pytest.fixture
    def client(self, monkeypatch, tmp_path):
        monkeypatch.setenv("PASSWORD_MEMORY_DATA_DIR", str(tmp_path))
        monkeypatch.setenv("FERNET_KEY", "test-fernet-key-1234567890123456789012")
        monkeypatch.setenv("LITELLM_PROXY_URL", "http://localhost:4000")
        init_db()
        return TestClient(app)

    def test_get_config(self, client):
        """测试获取 LLM 配置"""
        response = client.get("/llm/config")
        assert response.status_code == 200
        data = response.json()
        assert "default_model" in data
        assert "proxy_url" in data
        assert "proxy_healthy" in data
        assert data["proxy_url"] == "http://localhost:4000"

    def test_update_config(self, client):
        """测试更新 LLM 配置"""
        response = client.patch("/llm/config", json={"default_model": "claude-3-5-sonnet"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["default_model"] == "claude-3-5-sonnet"

        # 验证持久化
        response2 = client.get("/llm/config")
        assert response2.json()["default_model"] == "claude-3-5-sonnet"

    def test_list_models_proxy_unavailable(self, client):
        """测试 Proxy 不可用时的模型列表"""
        response = client.get("/llm/models")
        # 应该返回 502，因为 Proxy 未启动
        assert response.status_code == 502
        detail = response.json()["detail"]
        assert detail["code"] == "proxy_unavailable"


class TestLiteLLmProxyClient:
    """测试 LiteLLM Proxy 客户端（mock）"""

    @pytest.mark.asyncio
    @patch("backend.services.litellm_proxy_client.httpx.AsyncClient")
    async def test_chat_completion_success(self, mock_async_client):
        """测试聊天接口正常调用"""
        from backend.services.litellm_proxy_client import chat_completion

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "你好！"}}],
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client

        mock_async_client.return_value = mock_client

        result = await chat_completion(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
        )
        assert "choices" in result
        assert result["choices"][0]["message"]["content"] == "你好！"

    @pytest.mark.asyncio
    @patch("backend.services.litellm_proxy_client.httpx.AsyncClient")
    async def test_chat_completion_timeout(self, mock_async_client):
        """测试聊天接口超时"""
        import httpx
        from backend.services.litellm_proxy_client import chat_completion

        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")
        mock_client.__aenter__.return_value = mock_client
        mock_async_client.return_value = mock_client

        with pytest.raises(httpx.TimeoutException):
            await chat_completion(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hello"}],
            )

    @pytest.mark.asyncio
    @patch("backend.services.litellm_proxy_client.httpx.AsyncClient")
    async def test_list_models(self, mock_async_client):
        """测试获取模型列表"""
        from backend.services.litellm_proxy_client import list_models

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "model_name": "gpt-4o-mini",
                    "model_info": {},
                    "litellm_params": {
                        "model": "openai/gpt-4o-mini",
                        "api_key": "sk-***",
                        "rpm": 100,
                        "tpm": 100000,
                    },
                },
                {
                    "model_name": "claude-3-5-sonnet",
                    "model_info": {},
                    "litellm_params": {
                        "model": "anthropic/claude-3-5-sonnet-20241022",
                        "api_key": "sk-ant-***",
                        "rpm": 50,
                        "tpm": 50000,
                    },
                },
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_async_client.return_value = mock_client

        models = await list_models()
        assert len(models) == 2
        assert models[0].model_name == "gpt-4o-mini"
        assert models[1].model_name == "claude-3-5-sonnet"


class TestLlmServiceWithProxy:
    """测试 llm_service 通过 Proxy 调用"""

    def test_safety_blocked(self):
        """测试安全拦截（不经过 Proxy）"""
        from backend.services.llm_service import call_llm_sync

        result = call_llm_sync("帮我绕过验证码")
        assert result["status"] == "safety_blocked"

    @pytest.mark.asyncio
    @patch("backend.services.llm_service.chat_completion")
    async def test_successful_call_via_proxy(self, mock_chat):
        """测试通过 Proxy 成功调用 LLM"""
        from backend.services.llm_service import call_llm

        mock_chat.return_value = {
            "choices": [{"message": {"content": "这是一个测试回复"}}],
        }

        result = await call_llm("如何找回微信账号？", stream=False)
        assert result["status"] == "ok"
        assert result["reply"] == "这是一个测试回复"

    @pytest.mark.asyncio
    @patch("backend.services.llm_service.chat_completion")
    async def test_proxy_unavailable(self, mock_chat):
        """测试 Proxy 不可用时的错误处理"""
        import httpx
        from backend.services.llm_service import call_llm

        mock_chat.side_effect = httpx.ConnectError("Connection refused")

        result = await call_llm("测试问题", stream=False)
        assert result["status"] == "error"
        assert "LiteLLM Proxy" in result["message"]


class TestChatEndpointWithProxy:
    """测试 /chat 端点通过 Proxy 调用"""

    @pytest.fixture
    def client(self, monkeypatch, tmp_path):
        monkeypatch.setenv("PASSWORD_MEMORY_DATA_DIR", str(tmp_path))
        monkeypatch.setenv("FERNET_KEY", "test-fernet-key-1234567890123456789012")
        monkeypatch.setenv("LITELLM_PROXY_URL", "http://localhost:4000")
        return TestClient(app)

    @patch("backend.main.call_llm")
    def test_chat_calls_proxy(self, mock_call_llm, client):
        """测试聊天端点调用 Proxy"""
        async def mock_result(msg, stream=False):
            return {"status": "ok", "reply": "AI 回复内容"}

        mock_call_llm.side_effect = mock_result

        response = client.post("/chat", json={"message": "测试问题"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["reply"] == "AI 回复内容"

    @patch("backend.main.call_llm")
    def test_chat_falls_back_to_mock(self, mock_call_llm, client):
        """测试 Proxy 不可用时回退到 mock"""
        async def mock_result(msg, stream=False):
            return {"status": "error", "message": "无法连接 LiteLLM Proxy"}

        mock_call_llm.side_effect = mock_result

        response = client.post("/chat", json={"message": "测试问题"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        # 回退到 mock 应该也有 reply
        assert "reply" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
