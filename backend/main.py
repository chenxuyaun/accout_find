from __future__ import annotations

import json
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.models import AccountIdentity, SafetyPolicy
from backend.llm_config_store import get_preference, set_preference
from backend.schemas import (
    ChatRequest,
    ClueExtractRequest,
    LLMConfigResponse,
    LLMConfigUpdateRequest,
    LLMModelAddRequest,
    LLMModelDeleteRequest,
    LLMModelItem,
    LLMModelListResponse,
    LLMModelTestRequest,
    MigrationEmailRequest,
    MigrationPhoneRequest,
    OcrImportRequest,
    RecoveryPlanRequest,
)
from backend.services.clue_extractor import extract_clues
from backend.services.llm_service import call_llm
from backend.services.migration_checker import check_email_migration, check_phone_migration
from backend.services.mock_llm import mock_llm
from backend.services.privacy_guard import safety_block
from backend.services.recovery_planner import build_recovery_plan
from backend.services.risk_auditor import audit_accounts
from backend.storage import create_account, delete_account, get_account, list_accounts, load_accounts, update_account

logger = logging.getLogger(__name__)


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "")
    configured = [origin.strip() for origin in raw.split(",") if origin.strip()]
    if configured:
        return configured
    return ["http://127.0.0.1:5173", "http://localhost:5173"]


def _env_flag_enabled(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


app = FastAPI(title="密码记忆替身 API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def seed_demo_on_empty_storage() -> None:
    if not _env_flag_enabled("DEMO_SEED_ON_EMPTY"):
        return
    if load_accounts():
        return

    from backend.seed_demo import seed_demo_accounts

    seed_demo_accounts()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    seed_demo_on_empty_storage()
    yield


app.router.lifespan_context = lifespan


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "password-memory-agent",
        "safety": SafetyPolicy().model_dump(),
    }


@app.get("/accounts")
def accounts_list() -> list[AccountIdentity]:
    return list_accounts()


@app.post("/accounts")
def accounts_create(account: AccountIdentity) -> AccountIdentity | dict:
    blocked = safety_block(account.model_dump_json())
    if blocked:
        return blocked
    return create_account(account)


@app.get("/accounts/{account_id}")
def accounts_get(account_id: str) -> AccountIdentity:
    account = get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail={"code": "account_not_found", "message": "账号不存在。"})
    return account


@app.patch("/accounts/{account_id}")
def accounts_patch(account_id: str, patch: dict) -> AccountIdentity | dict:
    blocked = safety_block(str(patch))
    if blocked:
        return blocked
    account = update_account(account_id, patch)
    if not account:
        raise HTTPException(status_code=404, detail={"code": "account_not_found", "message": "账号不存在。"})
    return account


@app.delete("/accounts/{account_id}")
def accounts_delete(account_id: str, confirm: bool = False) -> dict:
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail={"code": "confirmation_required", "message": "删除账号线索需要 confirm=true。"},
        )
    if not delete_account(account_id):
        raise HTTPException(status_code=404, detail={"code": "account_not_found", "message": "账号不存在。"})
    return {"status": "ok", "deleted": True}


@app.post("/clues/extract")
def clues_extract(request: ClueExtractRequest) -> dict:
    return extract_clues(request.text, request.sourceType)


@app.post("/recovery/plan")
def recovery_plan(request: RecoveryPlanRequest) -> dict:
    return build_recovery_plan(request.platformName, list_accounts(), request.claimOwnership)


@app.post("/audit/run")
def audit_run() -> dict:
    return audit_accounts(list_accounts())


@app.post("/migration/phone")
def migration_phone(request: MigrationPhoneRequest) -> dict:
    blocked = safety_block(request.phone)
    if blocked:
        return blocked
    return check_phone_migration(request.phone, list_accounts())


@app.post("/migration/email")
def migration_email(request: MigrationEmailRequest) -> dict:
    blocked = safety_block(request.email)
    if blocked:
        return blocked
    return check_email_migration(request.email, list_accounts())


@app.post("/ocr/import")
def ocr_import(request: OcrImportRequest) -> dict:
    return extract_clues(request.ocrText, "ocr")


@app.post("/chat")
async def chat(request: ChatRequest):
    blocked = safety_block(request.message)
    if blocked:
        return blocked

    if request.stream:
        # 流式响应模式（SSE）
        async def generate():
            try:
                from backend.services.litellm_proxy_client import chat_completion_stream
                from backend.services.llm_service import _build_prompt, _get_default_model

                model = _get_default_model()
                system_prompt = _build_prompt(request.message)
                async for chunk in chat_completion_stream(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": request.message},
                    ],
                    temperature=0.7,
                    max_tokens=1000,
                ):
                    yield f"data: {json.dumps({'choices': [{'delta': {'content': chunk}}]}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception:
                # 流式异常时回退到 mock（一次性返回）
                logger.exception("流式 LLM 调用失败，回退到 mock")
                reply = mock_llm(request.message)
                yield f"data: {json.dumps({'choices': [{'delta': {'content': reply}}]}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    # 非流式模式
    try:
        result = await call_llm(request.message, stream=False)
        if result.get("status") == "error":
            logger.warning("LLM call failed, falling back to mock")
            return {
                "status": "ok",
                "reply": mock_llm(request.message),
            }
        return result
    except Exception:
        logger.exception("Unexpected error in /chat endpoint, falling back to mock")
        return {
            "status": "ok",
            "reply": mock_llm(request.message),
        }


# ============================================================
# LLM 配置管理路由
# ============================================================

@app.get("/llm/config", response_model=LLMConfigResponse)
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


@app.patch("/llm/config")
async def llm_update_config(request: LLMConfigUpdateRequest) -> dict:
    """更新 LLM 配置（设置默认模型等）"""
    set_preference("default_model", request.default_model)
    return {"status": "ok", "default_model": request.default_model}


@app.get("/llm/models", response_model=LLMModelListResponse)
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


@app.post("/llm/models")
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


@app.delete("/llm/models/{model_name}")
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


@app.post("/llm/models/test")
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
