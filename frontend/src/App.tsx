import {
  AlertTriangle,
  ClipboardCheck,
  FileScan,
  KeyRound,
  Mail,
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

  function handleChat(event: FormEvent) {
    event.preventDefault();
    if (!chatMessage.trim()) return;
    runAction("chat", async () => ({ kind: "chat", data: await api.chat(chatMessage) }));
  }

  return (
    <main className="min-h-screen bg-[#f5f4ef] text-[#17201b]">
      <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[240px_minmax(0,1fr)_360px]">
        <aside className="border-b border-[#d9d3c2] bg-[#ebe7dc] px-5 py-5 lg:border-b-0 lg:border-r">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#637166]">Password Memory</p>
            <h1 className="mt-2 text-2xl font-semibold">密码记忆替身</h1>
          </div>
          <nav className="mt-8 grid gap-1">
            {navItems.map(({ label, icon: Icon }) => (
              <a
                className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-[#39443c] hover:bg-[#ded8ca]"
                href={`#${label}`}
                key={label}
              >
                <Icon aria-hidden="true" size={17} />
                {label}
              </a>
            ))}
          </nav>
          <div className="mt-8 border-t border-[#d9d3c2] pt-5 text-sm">
            <p className="text-[#637166]">后端状态</p>
            <p className="mt-2 flex items-center gap-2 font-medium">
              <span
                className={`h-2.5 w-2.5 rounded-full ${
                  connection === "ok" ? "bg-[#2f7d57]" : connection === "failed" ? "bg-[#b94a48]" : "bg-[#b8942f]"
                }`}
              />
              {connection === "ok" ? "连接正常" : connection === "failed" ? "连接失败" : "连接中"}
            </p>
            {error ? <p className="mt-3 text-sm text-[#9b3733]">{error}</p> : null}
          </div>
        </aside>

        <section className="px-5 py-5 md:px-8">
          <header className="flex flex-col gap-4 border-b border-[#ded8ca] pb-5 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-sm text-[#637166]">账号身份关系工作台</p>
              <h2 className="mt-1 text-3xl font-semibold tracking-normal">线索、绑定、找回路径</h2>
            </div>
            <button
              className="inline-flex items-center justify-center gap-2 rounded-md bg-[#1d4f3a] px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
              disabled={connection === "checking"}
              onClick={() => window.location.reload()}
              type="button"
            >
              <RefreshCw size={16} />
              刷新数据
            </button>
          </header>

          <section className="mt-6" id="账号线索">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">账号线索</h3>
              <span className="text-sm text-[#637166]">{accounts.length} 个账号</span>
            </div>

            {connection === "failed" ? (
              <StatusBlock title="无法读取后端" detail="请确认 FastAPI 后端已启动，并且 VITE_API_BASE_URL 指向正确地址。" />
            ) : accounts.length === 0 ? (
              <StatusBlock title="暂无账号线索" detail="当前后端没有账号记录。可开启 DEMO_SEED_ON_EMPTY 或通过 API 导入虚构演示数据。" />
            ) : (
              <div className="mt-4 overflow-hidden rounded-md border border-[#d9d3c2] bg-[#fbfaf6]">
                <table className="w-full border-collapse text-left text-sm">
                  <thead className="bg-[#ebe7dc] text-[#637166]">
                    <tr>
                      <th className="px-4 py-3 font-medium">平台</th>
                      <th className="px-4 py-3 font-medium">重要性</th>
                      <th className="px-4 py-3 font-medium">登录方式</th>
                      <th className="px-4 py-3 font-medium">风险</th>
                    </tr>
                  </thead>
                  <tbody>
                    {accounts.map((account) => (
                      <tr
                        className={`cursor-pointer border-t border-[#e5dfd1] ${
                          account.id === selectedAccount?.id ? "bg-[#edf4ef]" : "hover:bg-[#f3f0e8]"
                        }`}
                        key={account.id}
                        onClick={() => setSelectedId(account.id)}
                      >
                        <td className="px-4 py-3 font-medium">{account.platformName}</td>
                        <td className="px-4 py-3">{account.importance}</td>
                        <td className="px-4 py-3">
                          {account.loginMethods.map((method) => method.type).join(", ") || "unknown"}
                        </td>
                        <td className="px-4 py-3">{account.riskTags.join("、") || "未标记"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="mt-8 grid gap-4 xl:grid-cols-2">
            <ActionBand
              buttonLabel="生成找回计划"
              busy={busyAction === "recovery"}
              disabled={!selectedAccount}
              icon={<ClipboardCheck size={18} />}
              id="找回计划"
              onClick={handleRecovery}
              title="本人账号找回计划"
            >
              使用当前选中平台生成官方路径优先的找回步骤，默认声明仅处理本人账号。
            </ActionBand>
            <ActionBand
              buttonLabel="运行安全体检"
              busy={busyAction === "audit"}
              icon={<ShieldCheck size={18} />}
              id="安全体检"
              onClick={handleAudit}
              title="安全体检"
            >
              汇总旧绑定、MFA、恢复路径缺口，输出风险和建议。
            </ActionBand>
          </section>

          <section className="mt-8 grid gap-4 xl:grid-cols-2" id="迁移检查">
            <ToolForm icon={<Phone size={18} />} onSubmit={handlePhoneMigration} title="手机号迁移">
              <input
                className="min-w-0 flex-1 rounded-md border border-[#cfc7b5] bg-white px-3 py-2"
                onChange={(event) => setPhone(event.target.value)}
                value={phone}
              />
              <SubmitButton busy={busyAction === "phone"} label="检查手机号" />
            </ToolForm>
            <ToolForm icon={<Mail size={18} />} onSubmit={handleEmailMigration} title="邮箱迁移">
              <input
                className="min-w-0 flex-1 rounded-md border border-[#cfc7b5] bg-white px-3 py-2"
                onChange={(event) => setEmail(event.target.value)}
                value={email}
              />
              <SubmitButton busy={busyAction === "email"} label="检查邮箱" />
            </ToolForm>
          </section>

          <section className="mt-8 grid gap-4 xl:grid-cols-2" id="OCR 导入">
            <form className="rounded-md border border-[#d9d3c2] bg-[#fbfaf6] p-4" onSubmit={handleOcrImport}>
              <h3 className="flex items-center gap-2 font-semibold">
                <FileScan size={18} />
                OCR 导入
              </h3>
              <textarea
                className="mt-3 min-h-28 w-full rounded-md border border-[#cfc7b5] bg-white p-3"
                onChange={(event) => setOcrText(event.target.value)}
                value={ocrText}
              />
              <SubmitButton busy={busyAction === "ocr"} label="提取线索" />
            </form>

            <form className="rounded-md border border-[#d9d3c2] bg-[#fbfaf6] p-4" onSubmit={handleChat}>
              <h3 className="flex items-center gap-2 font-semibold">
                <SearchCheck size={18} />
                安全问答
              </h3>
              <label className="mt-3 block text-sm text-[#637166]" htmlFor="chat-input">
                安全问答输入
              </label>
              <div className="mt-2 flex gap-2">
                <input
                  className="min-w-0 flex-1 rounded-md border border-[#cfc7b5] bg-white px-3 py-2"
                  id="chat-input"
                  onChange={(event) => setChatMessage(event.target.value)}
                  value={chatMessage}
                />
                <button
                  className="inline-flex items-center gap-2 rounded-md bg-[#1d4f3a] px-4 py-2 text-sm font-medium text-white"
                  type="submit"
                >
                  <Send size={16} />
                  发送
                </button>
              </div>
            </form>
          </section>
        </section>

        <aside className="border-t border-[#d9d3c2] bg-[#fbfaf6] px-5 py-5 lg:border-l lg:border-t-0">
          <h2 className="text-lg font-semibold">详情</h2>
          <SelectedAccount account={selectedAccount} />
          <ResultView result={result} />
        </aside>
      </div>
    </main>
  );
}

function StatusBlock({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="mt-4 rounded-md border border-[#d9d3c2] bg-[#fbfaf6] p-5">
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
    <section className="rounded-md border border-[#d9d3c2] bg-[#fbfaf6] p-4" id={id}>
      <h3 className="flex items-center gap-2 font-semibold">
        {icon}
        {title}
      </h3>
      <p className="mt-2 text-sm text-[#637166]">{children}</p>
      <button
        className="mt-4 rounded-md bg-[#1d4f3a] px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
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
    <form className="rounded-md border border-[#d9d3c2] bg-[#fbfaf6] p-4" onSubmit={onSubmit}>
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
      className="rounded-md bg-[#1d4f3a] px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
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
