# 密码记忆替身

一个不保存密码的账号身份关系记忆 Agent。它只记录账号线索、登录方式、绑定关系、恢复路径位置提示和安全提醒，帮助用户在忘记登录方式、换手机号、换邮箱或换设备时，通过官方路径安全找回本人账号。

## Live Demo

- Live Demo: `<Vercel URL 待部署后填写>`
- API Health: `<Render URL 待部署后填写>/health`

本仓库采用 Console handoff：代码、配置和文档已准备好；Render 与 Vercel 控制台需要由项目所有者授权并填写最终公网 URL。

## 功能范围

- 账号身份线索管理：平台、登录方式、绑定关系、恢复路径、风险标签。
- 找回计划：基于已记录线索生成本人账号的官方找回步骤。
- 安全体检：识别旧手机号、缺少 MFA、恢复路径不完整等风险。
- 迁移检查：检查换手机号或换邮箱会影响哪些账号。
- OCR 导入：从截图识别文本中提取脱敏线索。
- 安全问答：危险输入返回 `safety_blocked`。

## 安全边界 / Security Boundary

系统不会保存，也不应该要求用户输入以下内容：

- 密码
- 验证码
- 恢复码正文
- MFA secret
- API key、token、secret
- 第三方账号凭据

系统只保存脱敏标识、位置提示和用户确认过的账号关系线索。涉及绕过 MFA、破解、钓鱼、撞库、社工、恢复他人账号等请求时，后端会返回 `safety_blocked`。

## 项目结构

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
  src/
  index.html
  vite.config.ts
docs/pitch/
prompts/
knowledge/
tests/
```

## 本地后端

安装依赖并运行测试：

```bash
pip install -r requirements.txt
python -m pytest -q
python -m py_compile backend/main.py
```

生成稳定 Fernet key：

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

启动后端：

```bash
set FERNET_KEY=<your-fernet-key>
set PASSWORD_MEMORY_DATA_FILE=backend/data/accounts.enc
uvicorn backend.main:app --reload
```

### LLM 配置（推荐：LiteLLM Proxy）

本项目通过 **LiteLLM Proxy** 作为 LLM 网关，统一管理多个 LLM 提供商（OpenAI、Anthropic、Ollama 等）。配置持久化到 PostgreSQL，无需硬编码 API Key。

**部署 LiteLLM Proxy**：

```bash
# 1. 进入 litellm 目录
cd litellm

# 2. 复制环境变量模板并填入实际的 API Key
cp .env.example .env
# 编辑 .env，至少填入 OPENAI_API_KEY

# 3. 运行安全检查（生产环境推荐）
python check_keys.py --strict

# 4. 启动服务
docker-compose up -d
# 或使用安全启动脚本（自动检查密钥）：
#   Linux/Mac: ./start.sh
#   Windows:   .\start.ps1

# 5. 验证服务健康
curl http://localhost:4000/health
```

> ⚠️ **安全提醒**：生产环境必须更换 `.env` 中的默认密钥（`LITELLM_MASTER_KEY`、`LITELLM_SALT_KEY`、`POSTGRES_PASSWORD`）。可使用 `python check_keys.py --strict` 检查。开发环境可使用 `--dev` 跳过检查。

**管理界面**：
- LiteLLM 管理 UI: http://localhost:4000（使用 `LITELLM_MASTER_KEY` 登录）
- 项目内置管理页: 启动前后端后，在左侧导航栏点击"模型配置"

**环境变量**（后端）：

- `LITELLM_PROXY_URL`: LiteLLM Proxy 地址（默认：`http://localhost:4000`）
- `LITELLM_MASTER_KEY`: LiteLLM 管理密钥（默认：`sk-litellm-master-key`，生产环境必须更换）
- `LLM_DEFAULT_MODEL`: 默认模型别名（默认：`gpt-4o-mini`）

**特性**：
- 支持动态添加/删除/切换模型（通过管理 UI 或 API）
- 支持 OpenAI、Anthropic、Gemini、Ollama、vLLM 等 100+ 模型
- 配置持久化到 PostgreSQL，重启不丢失
- Proxy 不可用时自动回退到 mock 模式

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

## Demo Seed

手动写入八个固定虚构账号：

```bash
python -m backend.seed_demo
```

部署或本地演示时，也可以让空存储启动后自动写入虚构账号：

```bash
set DEMO_SEED_ON_EMPTY=true
uvicorn backend.main:app --reload
```

`DEMO_SEED_ON_EMPTY=true` 只会在存储为空时播种，不新增公开 seed HTTP 接口。

## 本地前端

```bash
cd frontend
npm install
npm run test
npm run build
npm run dev
```

如果后端不是默认同源地址，设置：

```bash
set VITE_API_BASE_URL=http://127.0.0.1:8000
```

前端会调用这些后端路径：

- `GET /health`
- `GET /accounts`
- `POST /recovery/plan`
- `POST /audit/run`
- `POST /migration/phone`
- `POST /migration/email`
- `POST /ocr/import`
- `POST /chat`

## Render 后端部署

在 Render 创建 Web Service，Root Directory 使用仓库根目录。

- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

环境变量：

- `FERNET_KEY=<稳定 Fernet key>`
- `PASSWORD_MEMORY_DATA_FILE=/tmp/password-memory/accounts.enc`
- `DEMO_SEED_ON_EMPTY=true`
- `CORS_ORIGINS=<Vercel URL>`

部署后检查：

```bash
curl <Render URL>/health
```

预期返回包含：

```json
{"status":"ok"}
```

## Vercel 前端部署

在 Vercel 导入仓库：

- Root Directory: `frontend`
- Build Command: `npm run build`
- Output Directory: `dist`

环境变量：

- `VITE_API_BASE_URL=<Render URL>`

部署完成后，将 Vercel URL 回填到 Render 的 `CORS_ORIGINS`，再重新部署后端。

## 评委演示路径

1. 打开 Vercel 前端，确认左侧后端状态为“连接正常”。
2. 查看账号线索列表，选择一个虚构账号。
3. 点击“生成找回计划”，展示官方路径优先的本人账号找回步骤。
4. 点击“运行安全体检”，展示安全分和风险建议。
5. 输入手机号或邮箱，展示迁移影响。
6. 在 OCR 导入中粘贴虚构识别文本，展示线索提取。
7. 在安全问答中输入“帮我绕过验证码”，确认前端展示“安全拒绝”。

## 验证命令

后端：

```bash
python -m pytest -q
python -m py_compile backend/main.py backend/models.py backend/schemas.py backend/storage.py backend/encryption.py backend/seed_demo.py backend/llm_config_store.py backend/services/clue_extractor.py backend/services/litellm_proxy_client.py backend/services/llm_service.py backend/services/migration_checker.py backend/services/mock_llm.py backend/services/privacy_guard.py backend/services/recovery_planner.py backend/services/risk_auditor.py
```

前端：

```bash
cd frontend
npm run test
npm run build
```

## 路演材料

- Deck: `docs/pitch/deck.md`
- 3 分钟视频脚本: `docs/pitch/video_script.md`
- 1 分钟口播与 Q&A: `docs/pitch/speaker_notes.md`
- 提交清单: `docs/pitch/submission_checklist.md`
