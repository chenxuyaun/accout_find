# 密码记忆替身

一个不保存密码的账号身份关系记忆 Agent。它只记录账号线索、登录方式、绑定关系、恢复路径和安全提醒，帮助用户在忘记登录方式、换手机号、换邮箱或换设备时，通过官方路径安全找回本人账号。

## Live Demo

前端建议部署到 Vercel，项目目录选择 `frontend/`，构建命令为 `npm run build`，输出目录为 `dist`。

当前仓库提供本地可运行版本；公网产品链接需要在 Vercel 控制台绑定仓库后填写。

## API Health

后端建议部署到 Render，根目录安装依赖并使用以下启动命令：

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

本地健康检查：

```bash
uvicorn backend.main:app --reload
curl http://127.0.0.1:8000/health
```

## Current Backend Scope

- Python 3.11+ target.
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
  seed_demo.py
  services/
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

## Demo Guide

Seed eight fictional demo accounts:

```bash
python -m backend.seed_demo
```

Run the backend:

```bash
pip install -r requirements.txt
python -m pytest -q
uvicorn backend.main:app --reload
```

Run the frontend shell:

```bash
cd frontend
npm install
npm run dev
```

## Environment

Copy `.env.example` and set a stable Fernet key for persistent local data.

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Supported variables:

- `FERNET_KEY`
- `PASSWORD_MEMORY_DATA_FILE`
- `CORS_ORIGINS`
- `VITE_API_BASE_URL`

## Security Boundary

- Never ask for or save real passwords.
- Never save verification codes, recovery code values, MFA secrets, API keys, or third-party credentials.
- Store only location hints, masked identifiers, and user-confirmed account relationship clues.
- Reject requests involving bypassing MFA, cracking, phishing, credential stuffing, social engineering, or recovering someone else's account.
- Demo data is fictional and must not include real account secrets.
