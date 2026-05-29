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
from backend.routers.llm_config import router as llm_router
from backend.schemas import (
    ChatRequest,
    ClueExtractRequest,
    MigrationEmailRequest,
    MigrationPhoneRequest,
    OcrImportRequest,
    RecoveryPlanRequest,
)
from backend.services.clue_extractor import extract_clues
from backend.services.litellm_proxy_client import chat_completion_stream
from backend.services.llm_service import _build_prompt, _get_default_model, call_llm
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

    # 幂等性检查：同一平台名不能重复创建
    existing = list_accounts()
    for existing_account in existing:
        if existing_account.platformName.lower() == account.platformName.lower():
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "duplicate_platform",
                    "message": f"平台 '{account.platformName}' 已存在（ID: {existing_account.id}），请使用 PATCH 更新已有记录。",
                },
            )
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


# LLM 配置管理路由 — 已拆分到 backend/routers/llm_config.py
app.include_router(llm_router)
