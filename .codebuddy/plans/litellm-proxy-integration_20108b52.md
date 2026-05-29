---
name: litellm-proxy-integration
overview: 集成 LiteLLM Proxy 作为 LLM 网关，提供统一的模型配置管理页面，支持动态添加/切换多个 LLM 提供商（OpenAI、Anthropic、Ollama 等），配置持久化到 PostgreSQL，不写死任何文件。
design:
  architecture:
    framework: react
    component: shadcn
  styleKeywords:
    - Warm Vintage
    - Minimalism
    - Clean
  fontSystem:
    fontFamily: PingFang SC
    heading:
      size: 24px
      weight: 600
    subheading:
      size: 16px
      weight: 500
    body:
      size: 14px
      weight: 400
  colorSystem:
    primary:
      - "#1d4f3a"
      - "#163829"
    background:
      - "#f5f4ef"
      - "#fbfaf6"
      - "#ffffff"
    text:
      - "#17201b"
      - "#39443c"
      - "#637166"
    functional:
      - "#2f7d57"
      - "#b94a48"
      - "#b8942f"
todos:
  - id: create-litellm-deploy-files
    content: 创建 litellm/ 目录，编写 docker-compose.yml、.env、config.yaml 部署文件
    status: completed
  - id: create-litellm-proxy-client
    content: 新建 backend/services/litellm_proxy.py，封装 call_llm_via_proxy 函数
    status: completed
    dependencies:
      - create-litellm-deploy-files
  - id: modify-llm-service
    content: 修改 backend/services/llm_service.py，改为调用 litellm_proxy，删除环境变量读取逻辑
    status: completed
    dependencies:
      - create-litellm-proxy-client
  - id: create-llm-config-router
    content: 新建 backend/routers/llm_config.py 和 __init__.py，实现模型配置管理 API
    status: completed
    dependencies:
      - create-litellm-deploy-files
  - id: modify-main-py
    content: 修改 backend/main.py，注册 llm_config 路由，修改 /chat 端点
    status: completed
    dependencies:
      - modify-llm-service
      - create-llm-config-router
  - id: create-llm-config-page
    content: 新建 frontend/src/pages/LlmConfigPage.tsx，实现模型配置页面组件
    status: completed
    dependencies:
      - create-llm-config-router
  - id: modify-frontend
    content: 修改 frontend/src/api.ts 和 App.tsx，添加配置页面导航和 API 客户端
    status: completed
    dependencies:
      - create-llm-config-page
  - id: integration-test
    content: 启动全部服务，执行联调测试，验证端到端功能
    status: completed
    dependencies:
      - modify-frontend
      - modify-main-py
---

## 用户需求

将当前硬编码环境变量的 LLM 调用方式，升级为通过 LiteLLM Proxy 网关统一管理多模型配置，并在前端提供通用配置页面。配置数据持久化到 PostgreSQL，不写死在文件（.env 或 config.yaml）中。

## 产品概述

"密码记忆替身"项目当前 LLM 配置通过 LiteLLM Proxy 管理，但配置页面（`LLMConfigPage.tsx`）尚未创建，且存在一些代码问题需要修复：

1. `encryption.py` 密钥管理不安全（重启后数据丢失）
2. `_build_prompt()` 将用户消息嵌入 system prompt 而非独立 user role
3. 流式响应异常捕获缺少日志
4. `recovery_planner.py` 安全回退格式不统一

## 核心功能（剩余）

1. **创建缺失的 `litellm/.env` 文件**（已完成 ✅）
2. **修复 `encryption.py` 密钥持久化**（未完成 🔴）
3. **修复 `_build_prompt()` 消息角色分离**（未完成 🟡）
4. **修复流式响应异常日志**（未完成 🟡）
5. **统一 `recovery_planner.py` 安全回退格式**（未完成 🟡）
6. **创建前端 `LLMConfigPage.tsx` 配置页面**（已完成 ✅，但需验证）
7. **联调测试**（未完成）

## 技术栈

- **后端框架**：FastAPI（已有）
- **LLM 网关**：LiteLLM Proxy（Docker 部署，端口 4000，已完成）
- **数据库**：PostgreSQL 16（Docker 部署，已完成）
- **HTTP 客户端**：`httpx>=0.27`（已有）
- **前端框架**：React + TypeScript + Tailwind CSS（已有）
- **前端路由**：单页应用，通过导航切换视图（已有）

## 实施方案

### 阶段一：修复后端问题（优先级：🔴 → 🟡）

#### 1.1 修复 `encryption.py` 密钥持久化

**文件**: `backend/encryption.py`

**问题**: 当前使用 `Fernet.generate_key()` 生成随机密钥，未持久化到文件。重启后端后，`FERNET_KEY` 环境变量丢失，导致无法解密已有 `accounts.enc` 数据。

**修复方案**:

```python
# FILEPATH: d:/software/code/ideas/tools/list/backend/encryption.py

import logging
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

_KEY_FILE = Path(os.getenv("FERNET_KEY_FILE", "backend/data/.fernet_key"))


def _load_key() -> bytes:
    """加载 Fernet 密钥，优先从环境变量读取，其次从文件读取，最后自动生成并持久化。"""
    env_key = os.getenv("FERNET_KEY", "")
    if env_key:
        return env_key.encode("utf-8")

    if _KEY_FILE.exists():
        return _KEY_FILE.read_bytes()

    # 首次启动：生成密钥并持久化
    new_key = Fernet.generate_key()
    _KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    _KEY_FILE.write_bytes(new_key)
    logger.warning("已生成新的加密密钥并保存到 %s，请妥善保管。", _KEY_FILE)
    return new_key


def encrypt_text(plaintext: str) -> bytes:
    cipher = Fernet(_load_key())
    return cipher.encrypt(plaintext.encode("utf-8"))


def decrypt_text(ciphertext: bytes) -> str:
    cipher = Fernet(_load_key())
    try:
        return cipher.decrypt(ciphertext).decode("utf-8")
    except InvalidToken:
        logger.error("解密失败：加密密钥不匹配或数据已损坏。")
        raise
```

#### 1.2 修复 `_build_prompt()` 消息角色分离

**文件**: `backend/services/llm_service.py`

**问题**: `_build_prompt()` 将用户消息嵌入 system prompt 字符串中，而不是作为独立的 `user` role 发送。这违反了 LLM 消息角色规范。

**修复方案**:

```python
# FILEPATH: d:/software/code/ideas/tools/list/backend/services/llm_service.py

def _build_prompt(user_message: str) -> str:
    """构建系统提示词（不含用户消息，用户消息作为独立 user role 发送）"""
    return """你是"密码记忆替身"的 AI 助手。你的任务是帮助用户理解账号登录关系、绑定关系和恢复路径。

重要规则：
1. 你不管理密码，不保存、不索要、不复述用户密码
2. 你不能保存验证码、恢复码正文、MFA secret 或第三方 token
3. 你只能为用户本人合法拥有的账号提供官方、合规、安全的恢复建议
4. 拒绝任何绕过验证、破解、社工、钓鱼、冒用或找回他人账号的请求

请提供专业、安全、合规的建议。如果问题涉及危险操作，请明确拒绝并说明原因。"""
```

同时更新 `call_llm()` 和 `main.py` 中的消息构造：

```python
# FILEPATH: d:/software/code/ideas/tools/list/backend/services/llm_service.py

    model = _get_default_model()
    system_prompt = _build_prompt(user_message)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
```

```python
# FILEPATH: d:/software/code/ideas/tools/list/backend/main.py

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
```

#### 1.3 修复流式响应异常日志

**文件**: `backend/main.py`

**问题**: 流式 SSE 生成器中的 `except Exception` 吞掉所有异常且没有日志记录。

**修复方案**:

```python
# FILEPATH: d:/software/code/ideas/tools/list/backend/main.py

            except Exception:
                logger.exception("流式 LLM 调用失败，回退到 mock")
                reply = mock_llm(request.message)
                yield f"data: {json.dumps({'choices': [{'delta': {'content': reply}}]}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
```

#### 1.4 统一 `recovery_planner.py` 安全回退格式

**文件**: `backend/services/recovery_planner.py`

**问题**: `build_recovery_plan` 返回的 `status: "safety_blocked"` 格式与 `privacy_guard.py` 中的 `safety_block()` 返回格式不完全一致。

**修复方案**:

```python
# FILEPATH: d:/software/code/ideas/tools/list/backend/services/recovery_planner.py

from backend.schemas import SafetyBlockedResponse


def build_recovery_plan(platform_name: str, accounts: list[AccountIdentity], claim_ownership: bool) -> dict:
    if not claim_ownership:
        return SafetyBlockedResponse(
            code="ownership_required",
            message="找回建议仅适用于你本人合法拥有的账号，请先确认账号归属。",
        ).model_dump()
    ...
```

---

### 阶段二：验证前端配置页面

#### 2.1 验证 `LLMConfigPage.tsx` 功能

**文件**: `frontend/src/pages/LLMConfigPage.tsx`

**验证清单**:

- [ ] Proxy 状态栏正确显示连接状态
- [ ] 模型列表正确加载和显示
- [ ] 添加模型表单验证和提交正常
- [ ] 删除模型确认对话框和删除操作正常
- [ ] 测试连接按钮功能正常

**注意**: 该文件已创建，但需要验证功能完整性。

---

### 阶段三：联调测试

#### 3.1 启动全部服务

```
# 终端 1：启动 LiteLLM Proxy
cd d:/software/code/ideas/tools/list/litellm
docker compose up -d

# 终端 2：启动后端
cd d:/software/code/ideas/tools/list
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# 终端 3：启动前端
cd d:/software/code/ideas/tools/list/frontend
npm run dev
```

#### 3.2 验证清单

**后端 API 测试**:

- [ ] `GET http://localhost:8000/health` 返回 `{"status": "ok"}`
- [ ] `GET http://localhost:8000/llm/config` 返回 Proxy 配置和健康状况
- [ ] `GET http://localhost:8000/llm/models` 返回模型列表
- [ ] `POST http://localhost:8000/llm/models` 添加模型成功
- [ ] `DELETE http://localhost:8000/llm/models/{name}` 删除模型成功
- [ ] `POST http://localhost:8000/chat` 通过 Proxy 调用模型并返回回复
- [ ] 加密密钥持久化测试：重启后端后仍能解密 `accounts.enc`

**前端测试**:

- [ ] 访问 `http://localhost:5173`，左侧导航显示"模型配置"项
- [ ] 点击"模型配置"，页面正常渲染
- [ ] 添加/删除模型功能正常
- [ ] 在"安全问答"中发送消息，后端通过 Proxy 调用模型并返回回复
- [ ] 停止 Proxy，前端显示连接失败状态

#### 3.3 更新 `README.md`

在 README 中添加"LLM 配置"章节：

- LiteLLM Proxy 的启动方式
- 如何通过 UI 配置模型
- 相关环境变量说明
- 加密密钥管理说明

---

## 目录结构变更

```
d:/software/code/ideas/tools/list/
├── litellm/
│   ├── docker-compose.yml             [EXISTING]
│   ├── .env                          [NEW] 已创建
│   └── config.yaml                   [EXISTING]
├── backend/
│   ├── encryption.py                 [MODIFY] 密钥持久化
│   ├── services/
│   │   ├── llm_service.py          [MODIFY] 消息角色分离
│   │   ├── litellm_proxy_client.py [EXISTING]
│   │   └── recovery_planner.py     [MODIFY] 统一安全回退格式
│   ├── main.py                     [MODIFY] 流式异常日志
│   └── schemas.py                 [EXISTING]
├── frontend/
│   └── src/
│       ├── api.ts                   [EXISTING]
│       ├── pages/
│       │   └── LLMConfigPage.tsx  [EXISTING] 需验证
│       └── App.tsx                 [EXISTING]
└── README.md                        [MODIFY] 添加 LLM 配置章节
```

---

## 性能与可靠性考虑

1. **密钥管理**：`FERNET_KEY_FILE` 应加入 `.gitignore`，避免提交到版本控制
2. **Proxy 高可用**：LiteLLM Proxy 支持多实例部署，当前为单实例
3. **错误处理**：所有异常都应记录日志，便于线上排查
4. **安全**：`LITELLM_MASTER_KEY` 仅后端持有，前端不直接调用 Proxy 管理 API

---

## 实施注意事项

1. **Windows Docker 环境**：确保 Docker Desktop 正在运行
2. **端口冲突**：PostgreSQL 使用 `5432:5432` 映射（可根据需要调整）
3. **环境变量**：

- `FERNET_KEY_FILE`: 密钥文件路径（默认 `backend/data/.fernet_key`）
- `LITELLM_PROXY_URL`: Proxy 地址（默认 `http://localhost:4000`）
- `LITELLM_MASTER_KEY`: Proxy 管理密钥（默认 `sk-litellm-master-key`）

4. **生产部署**：

- 更换 `LITELLM_MASTER_KEY` 为强密钥
- 更换 `FERNET_KEY` 为强密钥并持久化
- 配置防火墙规则，限制 Proxy 管理端点访问