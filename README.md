# 密码记忆替身

一个不保存密码的账号身份关系记忆 Agent。它只保存账号线索、登录方式、绑定关系、恢复路径和安全提醒，帮助用户在忘记登录方式、换手机号、换邮箱、换设备时安全找回本人账号。

## Current Backend Scope

This backend is a runnable FastAPI demo for the hackathon MVP.

- Python 3.11+ target, tested in the local Python environment.
- FastAPI + Pydantic.
- Encrypted local JSON storage with `cryptography.fernet`.
- No real LLM integration; `backend/services/mock_llm.py` is used.
- Safety-first API behavior: sensitive inputs return `safety_blocked`.

## Project Layout

```txt
backend/
  main.py
  models.py
  schemas.py
  encryption.py
  storage.py
  data/
  services/
    clue_extractor.py
    migration_checker.py
    mock_llm.py
    privacy_guard.py
    recovery_planner.py
    risk_auditor.py
frontend/
prompts/
knowledge/
tests/
```

## API

- `GET /health`
- `GET /accounts`
- `POST /accounts`
- `GET /accounts/{id}`
- `PATCH /accounts/{id}`
- `DELETE /accounts/{id}?confirm=true`
- `POST /clues/extract`
- `POST /recovery/plan`
- `POST /audit/run`
- `POST /migration/phone`
- `POST /migration/email`
- `POST /ocr/import`
- `POST /chat`

## Local Development

```bash
pip install -r requirements.txt
python -m pytest -q
uvicorn backend.main:app --reload
```

## Environment

Copy `.env.example` and set a stable Fernet key for persistent local data.

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Safety Principles

- Never ask for or save real passwords.
- Never save verification codes, recovery code values, MFA secrets, or third-party credentials.
- Store only location hints, masked identifiers, and user-confirmed account relationship clues.
- Reject requests involving bypassing MFA, cracking, phishing, credential stuffing, social engineering, or recovering someone else's account.
