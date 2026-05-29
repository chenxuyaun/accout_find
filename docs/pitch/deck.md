# 《密码记忆替身》路演 Deck

## 1. 标题 / Title

密码记忆替身：不保存密码的账号身份关系记忆 Agent

English summary: A safety-first account recovery memory agent that stores clues, not secrets.

## 2. 问题 / Problem

用户经常忘记某个账号当初使用了哪个手机号、邮箱、第三方登录或设备绑定。真正危险的不是忘记密码，而是在找回过程中误用非官方渠道、泄露验证码、暴露恢复码。

English summary: Account recovery fails because identity clues are scattered and unsafe shortcuts are tempting.

## 3. 核心原则 / Principle

系统不保存密码、验证码、恢复码正文、MFA secret、token 或第三方凭据。只保存经过脱敏的账号线索、绑定关系、恢复路径位置提示和风险提醒。

English summary: Never store credentials. Store redacted relationship memory and recovery hints.

## 4. 解决方案 / Solution

输入零散线索、OCR 摘要、邮箱或短信摘要后，Agent 统一整理账号身份关系图谱，并生成只面向本人账号、优先官方渠道的找回计划。

English summary: Convert scattered clues into a safe, structured recovery plan.

## 5. Demo 工作台 / Demo Workspace

前端是单页工具工作台：左侧导航、中间操作区、右侧详情栏。默认读取真实后端数据；后端不可用或账号为空时明确提示，不伪造成功。

English summary: A real backend-driven workspace, not a mocked landing page.

## 6. 后端能力 / Backend Capabilities

FastAPI 提供账号 CRUD、线索提取、找回计划、安全体检、手机号迁移、邮箱迁移、OCR 导入和安全问答。所有敏感输入会先经过 privacy guard。

English summary: FastAPI endpoints cover CRUD, extraction, audit, migration, OCR, and guarded chat.

## 7. 安全边界 / Safety Boundary

当用户输入绕过 MFA、破解、钓鱼、撞库、恢复他人账号等危险请求时，接口返回 `safety_blocked`。Demo 会展示拒绝结果，而不是隐藏失败。

English summary: Unsafe recovery and credential-abuse requests are blocked and surfaced.

## 8. Demo 路径 / Demo Flow

1. 打开前端，确认后端状态为连接正常。
2. 查看虚构账号列表和右侧绑定详情。
3. 对选中平台生成找回计划。
4. 运行安全体检，展示分数和风险。
5. 检查手机号或邮箱迁移影响。
6. 粘贴危险输入，展示安全拒绝。

English summary: Show data, plan, audit, migration, and safety refusal in one path.

## 9. 技术实现 / Implementation

后端使用 Pydantic 模型约束外部契约，Fernet 加密本地 JSON 存储。前端使用 Vite React、Tailwind 官方 Vite 插件、lucide-react 和 Vitest。

English summary: Typed FastAPI backend, encrypted storage, Vite React frontend.

## 10. 可部署性 / Deployability

Render 部署后端，使用 `$PORT` 和 `0.0.0.0` 启动。Vercel 部署前端，Root Directory 为 `frontend`，输出目录为 `dist`。

English summary: Render for API, Vercel for Vite frontend.

## 11. 可验证性 / Verification

后端通过 pytest 和 py_compile；前端通过 Vitest 和 Vite build。Demo seed 固定生成虚构账号，便于评委复现实验。

English summary: Backend and frontend have repeatable automated verification.

## 12. 下一步 / Next

接入真实 OCR 摘要管道、浏览器本地加密备份、更多官方恢复指南 RAG，以及多设备迁移提醒。

English summary: Add real OCR summaries, local encrypted backup, RAG guides, and migration reminders.
