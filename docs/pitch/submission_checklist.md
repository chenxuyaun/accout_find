# 黑客松提交清单

## 必填链接

- GitHub Repository: `<填写仓库 URL>`
- Live Demo: `<部署 Vercel 后填写>`
- API Health: `<部署 Render 后填写>/health`
- Demo Video: `<填写视频链接>`
- Pitch Deck: `docs/pitch/deck.md`

## 部署前检查

- 后端测试：`python -m pytest -q`
- 后端语法检查：`python -m py_compile backend/main.py backend/models.py backend/schemas.py backend/storage.py backend/encryption.py backend/seed_demo.py backend/services/clue_extractor.py backend/services/migration_checker.py backend/services/mock_llm.py backend/services/privacy_guard.py backend/services/recovery_planner.py backend/services/risk_auditor.py`
- 前端依赖：`cd frontend && npm install`
- 前端测试：`npm run test`
- 前端构建：`npm run build`

## Render 后端环境变量

- `FERNET_KEY=<稳定 Fernet key>`
- `PASSWORD_MEMORY_DATA_FILE=/tmp/password-memory/accounts.enc`
- `DEMO_SEED_ON_EMPTY=true`
- `CORS_ORIGINS=<Vercel URL>`

## Vercel 前端环境变量

- `VITE_API_BASE_URL=<Render URL>`

## 线上验收

- Render `<Render URL>/health` 返回 `status=ok`。
- Vercel 页面打开后显示“连接正常”。
- Network 请求指向 Render URL。
- 完成一次“生成找回计划”。
- 完成一次“运行安全体检”。
- 输入危险问答“帮我绕过验证码”，前端展示“安全拒绝”。

## 安全确认

- 不提交真实密码、验证码、恢复码正文、MFA secret、token、API key。
- 不新增公开 seed HTTP 接口。
- Demo 账号均为虚构数据。
- README 中 Live Demo 和 API Health 链接在 Console 部署完成后再填写真实 URL。
