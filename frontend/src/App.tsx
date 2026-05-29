import {
  AlertTriangle,
  Brain,
  ChevronRight,
  ClipboardCheck,
  FileScan,
  KeyRound,
  Mail,
  MessageSquare,
  Phone,
  RefreshCw,
  SearchCheck,
  Send,
  ShieldCheck,
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  AccountIdentity,
  AuditReport,
  ChatResponse,
  ClueExtractResponse,
  MigrationReport,
  RecoveryPlan,
  api,
} from "./api";
import LLMConfigPage from "./pages/LLMConfigPage";

type ConnectionState = "checking" | "ok" | "failed";

type ResultPanel =
  | { kind: "idle" }
  | { kind: "recovery"; data: RecoveryPlan }
  | { kind: "audit"; data: AuditReport }
  | { kind: "migration"; title: string; data: MigrationReport }
  | { kind: "ocr"; data: ClueExtractResponse }
  | { kind: "chat"; data: ChatResponse }
  | { kind: "error"; message: string };

const navItems = [
  { label: "账号线索", icon: KeyRound },
  { label: "找回计划", icon: ClipboardCheck },
  { label: "安全体检", icon: ShieldCheck },
  { label: "迁移检查", icon: RefreshCw },
  { label: "OCR 导入", icon: FileScan },
  { label: "模型配置", icon: Brain },
];

function App() {
  const [connection, setConnection] = useState<ConnectionState>("checking");
  const [error, setError] = useState("");
  const [accounts, setAccounts] = useState<AccountIdentity[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [result, setResult] = useState<ResultPanel>({ kind: "idle" });
  const [phone, setPhone] = useState("13812345678");
  const [email, setEmail] = useState("user@example.com");
  const [ocrText, setOcrText] = useState("腾讯云 微信登录 user@example.com");
  const [chatMessage, setChatMessage] = useState("");
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("账号线索");

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        await api.health();
        const loadedAccounts = await api.accounts();
        if (!active) return;
        setConnection("ok");
        setAccounts(loadedAccounts);
        setSelectedId(loadedAccounts[0]?.id ?? null);
      } catch (loadError) {
        if (!active) return;
        setConnection("failed");
        setError(loadError instanceof Error ? loadError.message : "后端不可用：未知错误");
      }
    }

    load();
    return () => {
      active = false;
    };
  }, []);

  const selectedAccount = useMemo(
    () => accounts.find((account) => account.id === selectedId) ?? accounts[0] ?? null,
    [accounts, selectedId],
  );

  async function runAction(kind: string, action: () => Promise<ResultPanel>) {
    setBusyAction(kind);
    try {
      setResult(await action());
    } catch (actionError) {
      setResult({
        kind: "error",
        message: actionError instanceof Error ? actionError.message : "操作失败",
      });
    } finally {
      setBusyAction(null);
    }
  }

  function handleRecovery() {
    if (!selectedAccount) return;
    runAction("recovery", async () => ({
      kind: "recovery",
      data: await api.recoveryPlan(selectedAccount.platformName),
    }));
  }

  function handleAudit() {
    runAction("audit", async () => ({ kind: "audit", data: await api.auditRun() }));
  }

  function handlePhoneMigration(event: FormEvent) {
    event.preventDefault();
    runAction("phone", async () => ({
      kind: "migration",
      title: "手机号迁移",
      data: await api.migrationPhone(phone),
    }));
  }

  function handleEmailMigration(event: FormEvent) {
    event.preventDefault();
    runAction("email", async () => ({
      kind: "migration",
      title: "邮箱迁移",
      data: await api.migrationEmail(email),
    }));
  }

  function handleOcrImport(event: FormEvent) {
    event.preventDefault();
    runAction("ocr", async () => ({ kind: "ocr", data: await api.ocrImport(ocrText) }));
  }

  async function handleChat(event: FormEvent) {
    event.preventDefault();
    if (!chatMessage.trim()) return;

    // 使用 SSE 流式对话
    setBusyAction("chat");
    setResult({ kind: "chat", data: { status: "ok", reply: "" } });

    try {
      await api.streamingChat(chatMessage, {
        onChunk(chunk) {
          setResult((prev) =>
            prev.kind === "chat"
              ? { kind: "chat", data: { ...prev.data, reply: prev.data.reply + chunk } }
              : prev,
          );
        },
        onComplete(fullReply) {
          setResult({ kind: "chat", data: { status: "ok", reply: fullReply } });
          setBusyAction(null);
        },
        onError(err) {
          setResult({ kind: "error", message: err.message });
          setBusyAction(null);
        },
      });
    } catch (error) {
      setResult({
        kind: "error",
        message: error instanceof Error ? error.message : "聊天请求失败",
      });
      setBusyAction(null);
    }
  }

  return (
    <main className="min-h-screen bg-[#f5f4ef] text-[#17201b]">
      <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[280px_minmax(0,1fr)_400px]">
        {/* 左侧导航栏 */}
        <aside className="border-b border-[#d9d3c2] bg-[#ebe7dc]/90 px-6 py-6 lg:border-b-0 lg:border-r">
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <div className="h-10 w-10 rounded-xl bg-[#1d4f3a] flex items-center justify-center">
                <KeyRound className="h-5 w-5 text-white" />
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#637166]">Password Memory</p>
                <h1 className="text-xl font-semibold">密码记忆替身</h1>
              </div>
            </div>
          </div>

          <nav className="grid gap-1">
            {navItems.map(({ label, icon: Icon }) => (
              <button
                className={`flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium transition-all ${
                  activeTab === label
                    ? "bg-[#1d4f3a] text-white shadow-md"
                    : "text-[#39443c] hover:bg-[#ded8ca]"
                }`}
                key={label}
                onClick={() => setActiveTab(label)}
                type="button"
              >
                <Icon aria-hidden="true" size={18} />
                {label}
                {activeTab === label && <ChevronRight className="ml-auto" size={16} />}
              </button>
            ))}
          </nav>

          <div className="mt-8 border-t border-[#d9d3c2] pt-5 text-sm">
            <p className="text-[#637166] font-medium">后端状态</p>
            <div className="mt-3 flex items-center gap-2.5">
              <div
                className={`relative h-3 w-3 rounded-full ${
                  connection === "ok" ? "bg-[#2f7d57]" : connection === "failed" ? "bg-[#b94a48]" : "bg-[#b8942f]"
                }`}
              >
                {connection === "ok" && (
                  <div className="absolute inset-0 rounded-full bg-[#2f7d57] animate-ping opacity-75" />
                )}
              </div>
              <span className="font-medium">
                {connection === "ok" ? "连接正常" : connection === "failed" ? "连接失败" : "连接中..."}
              </span>
            </div>
            {error ? (
              <div className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-[#9b3733]">
                <p className="font-medium">连接错误</p>
                <p className="mt-1">{error}</p>
              </div>
            ) : null}
          </div>

          <div className="mt-auto pt-8">
            <button
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#1d4f3a] px-4 py-2.5 text-sm font-medium text-white transition-all hover:bg-[#163829] disabled:cursor-not-allowed disabled:opacity-50"
              disabled={connection === "checking"}
              onClick={() => window.location.reload()}
              type="button"
            >
              <RefreshCw className={connection === "checking" ? "animate-spin" : ""} size={16} />
              刷新数据
            </button>
          </div>
        </aside>

        {/* 主内容区 */}
        <section className="px-6 py-6 md:px-10">
          <header className="mb-8 border-b border-[#ded8ca] pb-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
              <div>
                <p className="text-sm text-[#637166]">账号身份关系工作台</p>
                <h2 className="mt-1 text-4xl font-semibold tracking-tight">线索、绑定、找回路径</h2>
              </div>
            </div>
          </header>

          {/* 账号线索表格 */}
          <section className="mb-8" id="账号线索">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-xl font-semibold">账号线索</h3>
              <span className="rounded-full bg-[#1d4f3a]/10 px-3 py-1 text-sm font-medium text-[#1d4f3a]">
                {accounts.length} 个账号
              </span>
            </div>

            {connection === "failed" ? (
              <StatusBlock title="无法读取后端" detail="请确认 FastAPI 后端已启动，并且 VITE_API_BASE_URL 指向正确地址。" />
            ) : accounts.length === 0 ? (
              <StatusBlock title="暂无账号线索" detail="当前后端没有账号记录。可开启 DEMO_SEED_ON_EMPTY 或通过 API 导入虚构演示数据。" />
            ) : (
              <div className="overflow-hidden rounded-xl border border-[#d9d3c2] bg-white shadow-sm">
                <table className="w-full border-collapse text-left text-sm">
                  <thead className="bg-[#f8f7f3] text-[#637166]">
                    <tr>
                      <th className="px-5 py-4 font-medium">平台</th>
                      <th className="px-5 py-4 font-medium">重要性</th>
                      <th className="px-5 py-4 font-medium">登录方式</th>
                      <th className="px-5 py-4 font-medium">风险</th>
                    </tr>
                  </thead>
                  <tbody>
                    {accounts.map((account, index) => (
                      <tr
                        className={`cursor-pointer border-t border-[#f0ede3] transition-colors ${
                          account.id === selectedAccount?.id
                            ? "bg-[#edf4ef]"
                            : index % 2 === 0
                              ? "bg-white hover:bg-[#fafaf5]"
                              : "bg-[#fbfaf6] hover:bg-[#f5f4ef]"
                        }`}
                        key={account.id}
                        onClick={() => setSelectedId(account.id)}
                      >
                        <td className="px-5 py-4 font-medium text-[#1d4f3a]">{account.platformName}</td>
                        <td className="px-5 py-4">
                          <span
                            className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                              account.importance === "critical"
                                ? "bg-red-100 text-red-700"
                                : account.importance === "high"
                                  ? "bg-orange-100 text-orange-700"
                                  : account.importance === "medium"
                                    ? "bg-yellow-100 text-yellow-700"
                                    : "bg-gray-100 text-gray-700"
                            }`}
                          >
                            {account.importance}
                          </span>
                        </td>
                        <td className="px-5 py-4 text-[#39443c]">
                          {account.loginMethods.map((method) => method.type).join(", ") || "unknown"}
                        </td>
                        <td className="px-5 py-4">
                          {account.riskTags.length > 0 ? (
                            <span className="rounded-full bg-red-50 px-2.5 py-1 text-xs font-medium text-red-600">
                              {account.riskTags.length} 个风险
                            </span>
                          ) : (
                            <span className="rounded-full bg-green-50 px-2.5 py-1 text-xs font-medium text-green-600">
                              安全
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* 操作按钮区 */}
          <section className="mb-8 grid gap-4 lg:grid-cols-2">
            <ActionBand
              buttonLabel="生成找回计划"
              busy={busyAction === "recovery"}
              disabled={!selectedAccount}
              icon={<ClipboardCheck size={20} />}
              id="找回计划"
              onClick={handleRecovery}
              title="本人账号找回计划"
            >
              使用当前选中平台生成官方路径优先的找回步骤，默认声明仅处理本人账号。
            </ActionBand>
            <ActionBand
              buttonLabel="运行安全体检"
              busy={busyAction === "audit"}
              icon={<ShieldCheck size={20} />}
              id="安全体检"
              onClick={handleAudit}
              title="安全体检"
            >
              汇总旧绑定、MFA、恢复路径缺口，输出风险和建议。
            </ActionBand>
          </section>

          {/* 迁移检查 */}
          <section className="mb-8 grid gap-4 lg:grid-cols-2" id="迁移检查">
            <ToolForm icon={<Phone size={20} />} onSubmit={handlePhoneMigration} title="手机号迁移">
              <input
                className="min-w-0 flex-1 rounded-lg border border-[#cfc7b5] bg-white px-4 py-2.5 transition-colors focus:border-[#1d4f3a] focus:outline-none focus:ring-2 focus:ring-[#1d4f3a]/20"
                onChange={(event) => setPhone(event.target.value)}
                value={phone}
              />
              <SubmitButton busy={busyAction === "phone"} label="检查手机号" />
            </ToolForm>
            <ToolForm icon={<Mail size={20} />} onSubmit={handleEmailMigration} title="邮箱迁移">
              <input
                className="min-w-0 flex-1 rounded-lg border border-[#cfc7b5] bg-white px-4 py-2.5 transition-colors focus:border-[#1d4f3a] focus:outline-none focus:ring-2 focus:ring-[#1d4f3a]/20"
                onChange={(event) => setEmail(event.target.value)}
                value={email}
              />
              <SubmitButton busy={busyAction === "email"} label="检查邮箱" />
            </ToolForm>
          </section>

          {/* OCR 导入和安全问答 */}
          {activeTab === "OCR 导入" && (
          <section className="grid gap-4 lg:grid-cols-2" id="OCR 导入">
            <form className="rounded-xl border border-[#d9d3c2] bg-white p-5 shadow-sm" onSubmit={handleOcrImport}>
              <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold">
                <FileScan size={20} />
                OCR 导入
              </h3>
              <textarea
                className="mb-4 min-h-32 w-full rounded-lg border border-[#cfc7b5] bg-[#fbfaf6] p-4 text-sm transition-colors focus:border-[#1d4f3a] focus:outline-none focus:ring-2 focus:ring-[#1d4f3a]/20"
                onChange={(event) => setOcrText(event.target.value)}
                placeholder="粘贴截图识别文本..."
                value={ocrText}
              />
              <SubmitButton busy={busyAction === "ocr"} label="提取线索" />
            </form>

            <form className="rounded-xl border border-[#d9d3c2] bg-white p-5 shadow-sm" onSubmit={handleChat}>
              <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold">
                <MessageSquare size={20} />
                安全问答
              </h3>
              <label className="mb-2 block text-sm font-medium text-[#637166]" htmlFor="chat-input">
                安全问答输入
              </label>
              <div className="flex gap-2">
                <input
                  className="min-w-0 flex-1 rounded-lg border border-[#cfc7b5] bg-[#fbfaf6] px-4 py-2.5 text-sm transition-colors focus:border-[#1d4f3a] focus:outline-none focus:ring-2 focus:ring-[#1d4f3a]/20"
                  id="chat-input"
                  onChange={(event) => setChatMessage(event.target.value)}
                  placeholder="输入您的问题..."
                  value={chatMessage}
                />
                <button
                  className="inline-flex items-center gap-2 rounded-lg bg-[#1d4f3a] px-5 py-2.5 text-sm font-medium text-white transition-all hover:bg-[#163829] disabled:cursor-not-allowed disabled:opacity-50"
                  type="submit"
                >
                  <Send size={16} />
                  发送
                </button>
              </div>
            </form>
          </section>
          )}

          {/* 模型配置页面 */}
          {activeTab === "模型配置" && <LLMConfigPage />}
        </section>

        {/* 右侧详情面板 */}
        <aside className="border-t border-[#d9d3c2] bg-[#fbfaf6]/80 px-6 py-6 lg:border-l lg:border-t-0">
          <h2 className="mb-6 text-xl font-semibold">详情</h2>
          <SelectedAccount account={selectedAccount} />
          <ResultView result={result} />
        </aside>
      </div>
    </main>
  );
}

function StatusBlock({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="mt-4 rounded-lg border border-[#d9d3c2] bg-[#fbfaf6] p-5">
      <h3 className="font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-[#637166]">{detail}</p>
    </div>
  );
}

function ActionBand({
  busy,
  buttonLabel,
  children,
  disabled = false,
  icon,
  id,
  onClick,
  title,
}: {
  busy: boolean;
  buttonLabel: string;
  children: string;
  disabled?: boolean;
  icon: React.ReactNode;
  id: string;
  onClick: () => void;
  title: string;
}) {
  return (
    <section className="rounded-xl border border-[#d9d3c2] bg-white p-5 shadow-sm" id={id}>
      <h3 className="flex items-center gap-2 font-semibold">
        {icon}
        {title}
      </h3>
      <p className="mt-2 text-sm text-[#637166]">{children}</p>
      <button
        className="mt-4 rounded-lg bg-[#1d4f3a] px-4 py-2 text-sm font-medium text-white transition-all hover:bg-[#163829] disabled:cursor-not-allowed disabled:opacity-50"
        disabled={disabled || busy}
        onClick={onClick}
        type="button"
      >
        {busy ? "处理中" : buttonLabel}
      </button>
    </section>
  );
}

function ToolForm({
  children,
  icon,
  onSubmit,
  title,
}: {
  children: React.ReactNode;
  icon: React.ReactNode;
  onSubmit: (event: FormEvent) => void;
  title: string;
}) {
  return (
    <form className="rounded-xl border border-[#d9d3c2] bg-white p-5 shadow-sm" onSubmit={onSubmit}>
      <h3 className="flex items-center gap-2 font-semibold">
        {icon}
        {title}
      </h3>
      <div className="mt-3 flex flex-col gap-2 sm:flex-row">{children}</div>
    </form>
  );
}

function SubmitButton({ busy, label }: { busy: boolean; label: string }) {
  return (
    <button
      className="rounded-lg bg-[#1d4f3a] px-4 py-2.5 text-sm font-medium text-white transition-all hover:bg-[#163829] disabled:cursor-not-allowed disabled:opacity-50"
      disabled={busy}
      type="submit"
    >
      {busy ? "处理中" : label}
    </button>
  );
}

function SelectedAccount({ account }: { account: AccountIdentity | null }) {
  if (!account) {
    return <p className="mt-4 text-sm text-[#637166]">选择账号后查看绑定关系、恢复路径和风险标签。</p>;
  }

  return (
    <section className="mt-4 border-b border-[#ded8ca] pb-5 text-sm">
      <h3 className="text-xl font-semibold">当前账号</h3>
      <p className="mt-1 font-medium">平台：{account.platformName}</p>
      <dl className="mt-4 grid gap-3">
        <Detail label="重要性" value={`级别：${account.importance}`} />
        <Detail label="MFA" value={account.mfaEnabled ? "已开启" : "未开启"} />
        <Detail label="登录方式" value={account.loginMethods.map((method) => method.type).join(", ") || "unknown"} />
        <Detail
          label="绑定"
          value={account.bindings.map((binding) => binding.valueMasked ?? binding.kind).join("、") || "暂无"}
        />
        <Detail label="恢复路径" value={account.recoveryPaths.map((path) => path.locationHint ?? path.kind).join("、") || "暂无"} />
      </dl>
    </section>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[#637166]">{label}</dt>
      <dd className="mt-1 font-medium">{value}</dd>
    </div>
  );
}

function ResultView({ result }: { result: ResultPanel }) {
  if (result.kind === "idle") {
    return <p className="mt-5 text-sm text-[#637166]">操作结果会显示在这里。</p>;
  }

  if (result.kind === "error") {
    return <ResultShell title="操作失败" tone="danger" items={[result.message]} />;
  }

  if (result.kind === "recovery") {
    return (
      <ResultShell
        title={`${result.data.platformName} 找回计划`}
        items={[result.data.legalReminder, ...result.data.recommendedSteps, ...result.data.risks]}
      />
    );
  }

  if (result.kind === "audit") {
    return (
      <ResultShell
        title={`安全分 ${result.data.score}`}
        items={result.data.risks.map((risk) => `${risk.level} · ${risk.title}：${risk.suggestion}`)}
      />
    );
  }

  if (result.kind === "migration") {
    return (
      <ResultShell
        title={result.title}
        items={[
          `影响账号 ${result.data.affectedAccounts.length} 个`,
          ...result.data.migrationPriority,
          ...result.data.steps,
        ]}
      />
    );
  }

  if (result.kind === "ocr") {
    return (
      <ResultShell
        title="OCR 线索"
        items={[
          `平台：${result.data.platforms.join("、") || "未识别"}`,
          `邮箱：${result.data.emailsMasked.join("、") || "未识别"}`,
          `手机：${result.data.phonesMasked.join("、") || "未识别"}`,
        ]}
      />
    );
  }

  if (result.data.status === "safety_blocked") {
    return <ResultShell title="安全拒绝" tone="danger" items={[result.data.message]} />;
  }

  return <ResultShell title="安全问答" items={[result.data.reply]} />;
}

function ResultShell({
  items,
  title,
  tone = "normal",
}: {
  items: string[];
  title: string;
  tone?: "normal" | "danger";
}) {
  return (
    <section className="mt-5">
      <h3 className={`flex items-center gap-2 font-semibold ${tone === "danger" ? "text-[#9b3733]" : ""}`}>
        {tone === "danger" ? <AlertTriangle size={18} /> : <SearchCheck size={18} />}
        {title}
      </h3>
      <ul className="mt-3 grid gap-2 text-sm">
        {items.map((item) => (
          <li className="rounded-md bg-[#f0ece2] px-3 py-2" key={item}>
            {item}
          </li>
        ))}
      </ul>
    </section>
  );
}

export default App;
