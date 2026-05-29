"""LLM 配置管理路由。

提供 LiteLLM Proxy 模型管理、默认模型配置等功能。
"""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from backend.llm_config_store import get_preference, set_preference
from backend.schemas import (
    LLMConfigResponse,
    LLMConfigUpdateRequest,
    LLMModelAddRequest,
    LLMModelDeleteRequest,
    LLMModelItem,
    LLMModelListResponse,
    LLMModelTestRequest,
)

router = APIRouter(prefix="/llm", tags=["LLM 配置"])


@router.get("/config", response_model=LLMConfigResponse)
async def llm_get_config() -> LLMConfigResponse:
    """获取 LLM 配置（默认模型 + Proxy 健康状态）"""
    from backend.services.litellm_proxy_client import health_check as proxy_health

    default_model = get_preference("default_model", os.getenv("LLM_DEFAULT_MODEL", "gpt-4o-mini"))
    proxy_url = os.getenv("LITELLM_PROXY_URL", "http://localhost:4000")

    proxy_healthy = False
    try:
        await proxy_health()
        proxy_healthy = True
    except Exception:
        pass

    return LLMConfigResponse(
        default_model=default_model,
        proxy_url=proxy_url,
        proxy_healthy=proxy_healthy,
    )


@router.patch("/config")
async def llm_update_config(request: LLMConfigUpdateRequest) -> dict:
    """更新 LLM 配置（设置默认模型等）"""
    set_preference("default_model", request.default_model)
    return {"status": "ok", "default_model": request.default_model}


@router.get("/models", response_model=LLMModelListResponse)
async def llm_list_models() -> LLMModelListResponse:
    """获取 LiteLLM Proxy 中已配置的所有模型"""
    from backend.services.litellm_proxy_client import list_models as proxy_list_models

    try:
        models = await proxy_list_models()
        items = []
        for m in models:
            litellm_params = m.litellm_params or {}
            full_model = litellm_params.get("model", "")
            # 解析 provider/model：格式为 "openai/gpt-4o"
            provider, actual_model = "", full_model
            if "/" in full_model:
                parts = full_model.split("/", 1)
                provider = parts[0]
                actual_model = parts[1]

            items.append(LLMModelItem(
                model_name=m.model_name,
                provider=provider,
                model=actual_model,
                api_base=litellm_params.get("api_base", ""),
                rpm=litellm_params.get("rpm", 0),
                tpm=litellm_params.get("tpm", 0),
                has_api_key=bool(litellm_params.get("api_key", "")),
            ))
        return LLMModelListResponse(models=items, total=len(items))
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={"code": "proxy_unavailable", "message": f"无法连接 LiteLLM Proxy：{str(e)}"},
        )


@router.post("/models")
async def llm_add_model(request: LLMModelAddRequest) -> dict:
    """通过 LiteLLM Proxy 管理 API 添加新模型"""
    from backend.services.litellm_proxy_client import add_model as proxy_add_model

    try:
        result = await proxy_add_model(
            model_name=request.model_name,
            provider=request.provider,
            model=request.model,
            api_key=request.api_key,
            api_base=request.api_base,
            rpm=request.rpm,
            tpm=request.tpm,
        )
        return {"status": "ok", "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={"code": "add_model_failed", "message": f"添加模型失败：{str(e)}"},
        )


@router.delete("/models/{model_name}")
async def llm_delete_model(model_name: str) -> dict:
    """通过 LiteLLM Proxy 管理 API 删除模型"""
    from backend.services.litellm_proxy_client import delete_model as proxy_delete_model

    try:
        result = await proxy_delete_model(model_name)
        return {"status": "ok", "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={"code": "delete_model_failed", "message": f"删除模型失败：{str(e)}"},
        )


@router.post("/models/test")
async def llm_test_model(request: LLMModelTestRequest) -> dict:
    """测试模型是否可用"""
    from backend.services.litellm_proxy_client import test_model as proxy_test_model

    try:
        result = await proxy_test_model(request.model_name, request.message)
        return {"status": "ok", "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={"code": "test_model_failed", "message": f"测试模型失败：{str(e)}"},
        )
