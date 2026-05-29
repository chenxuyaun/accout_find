from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.models import AccountIdentity, SafetyPolicy
from backend.schemas import (
    ChatRequest,
    ClueExtractRequest,
    MigrationEmailRequest,
    MigrationPhoneRequest,
    OcrImportRequest,
    RecoveryPlanRequest,
)
from backend.services.clue_extractor import extract_clues
from backend.services.migration_checker import check_email_migration, check_phone_migration
from backend.services.mock_llm import mock_llm
from backend.services.privacy_guard import safety_block
from backend.services.recovery_planner import build_recovery_plan
from backend.services.risk_auditor import audit_accounts
from backend.storage import create_account, delete_account, get_account, list_accounts, update_account


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(title="密码记忆替身 API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
def chat(request: ChatRequest) -> dict:
    blocked = safety_block(request.message)
    if blocked:
        return blocked
    return {
        "status": "ok",
        "reply": mock_llm(request.message),
    }
