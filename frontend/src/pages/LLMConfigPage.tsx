import {
  AlertTriangle,
  Brain,
  CheckCircle,
  Cpu,
  Key,
  Link,
  Plus,
  RefreshCw,
  Settings,
  Trash2,
  XCircle,
  Zap,
} from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { LLMModelItem, api } from "../api";

export default function LLMConfigPage() {
  const [models, setModels] = useState<LLMModelItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [defaultModel, setDefaultModel] = useState("");
  const [proxyHealthy, setProxyHealthy] = useState(false);
  const [proxyUrl, setProxyUrl] = useState("");

  // 添加模型表单
  const [showAddForm, setShowAddForm] = useState(false);
  const [addForm, setAddForm] = useState({
    model_name: "",
    provider: "openai",
    model: "",
    api_key: "",
    api_base: "",
    rpm: 100,
    tpm: 100000,
  });
  const [adding, setAdding] = useState(false);

  // 测试状态
  const [testingModel, setTestingModel] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{
    model_name: string;
    ok: boolean;
    reply?: string;
    error?: string;
  } | null>(null);

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const [configData, modelsData] = await Promise.all([
        api.llmGetConfig(),
        api.llmListModels(),
      ]);
      setDefaultModel(configData.default_model);
      setProxyHealthy(configData.proxy_healthy);
      setProxyUrl(configData.proxy_url);
      setModels(modelsData.models);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载配置失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleSetDefault(modelName: string) {
    try {
      await api.llmUpdateConfig({ default_model: modelName });
      setDefaultModel(modelName);
    } catch (err) {
      setError(err instanceof Error ? err.message : "设置默认模型失败");
    }
  }

  async function handleAddModel(event: FormEvent) {
    event.preventDefault();
    setAdding(true);
    try {
      await api.llmAddModel(addForm);
      setShowAddForm(false);
      setAddForm({
        model_name: "",
        provider: "openai",
        model: "",
        api_key: "",
        api_base: "",
        rpm: 100,
        tpm: 100000,
      });
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "添加模型失败");
    } finally {
      setAdding(false);
    }
  }

  async function handleDeleteModel(modelName: string) {
    if (!confirm(`确定要删除模型 "${modelName}" 吗？此操作不可撤销。`)) return;
    try {
      await api.llmDeleteModel(modelName);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除模型失败");
    }
  }

  async function handleTestModel(modelName: string) {
    setTestingModel(modelName);
    setTestResult(null);
    try {
      const result = await api.llmTestModel({ model_name: modelName, message: "Hello! 请用中文回复'测试成功'。" });
      setTestResult({
        model_name: modelName,
        ok: result.data.ok,
        reply: result.data.reply,
        error: result.data.error,
      });
    } catch (err) {
      setTestResult({
        model_name: modelName,
        ok: false,
        error: err instanceof Error ? err.message : "测试请求失败",
      });
    } finally {
      setTestingModel(null);
    }
  }

  const providerOptions = [
    { value: "openai", label: "OpenAI" },
    { value: "anthropic", label: "Anthropic (Claude)" },
    { value: "gemini", label: "Google Gemini" },
    { value: "openai_like", label: "OpenAI 兼容 (Ollama/vLLM)" },
    { value: "ollama", label: "Ollama" },
    { value: "deepseek", label: "DeepSeek" },
    { value: "groq", label: "Groq" },
  ];

  return (
    <div className="animate-fadeIn space-y-6">
      {/* 页面标题 */}
      <header className="border-b border-[#ded8ca] pb-6">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-[#1d4f3a] flex items-center justify-center">
            <Brain className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-sm text-[#637166]">LLM Gateway</p>
            <h2 className="text-2xl font-semibold">模型配置管理</h2>
          </div>
        </div>
        <p className="mt-3 text-sm text-[#637166]">
          通过 LiteLLM Proxy 统一管理所有 LLM 模型，支持动态添加/切换/测试。配置持久化到数据库，无需重启。
        </p>
      </header>

      {/* Proxy 状态 */}
      <section className="rounded-xl border border-[#d9d3c2] bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Settings size={20} className="text-[#637166]" />
            <div>
              <h3 className="font-semibold">LiteLLM Proxy 状态</h3>
              <p className="text-sm text-[#637166]">{proxyUrl}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div
              className={`h-3 w-3 rounded-full ${
                proxyHealthy ? "bg-[#2f7d57]" : "bg-[#b94a48]"
              }`}
            >
              {proxyHealthy && (
                <div className="absolute inset-0 rounded-full bg-[#2f7d57] animate-ping opacity-75" />
              )}
            </div>
            <span className={`text-sm font-medium ${proxyHealthy ? "text-[#2f7d57]" : "text-[#b94a48]"}`}>
              {proxyHealthy ? "已连接" : "未连接"}
            </span>
            <button
              className="ml-2 rounded-lg border border-[#d9d3c2] px-3 py-1.5 text-sm transition-colors hover:bg-[#f5f4ef]"
              onClick={loadData}
              type="button"
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            </button>
          </div>
        </div>
        {!proxyHealthy && (
          <div className="mt-4 rounded-lg bg-amber-50 border border-amber-200 p-4 text-sm text-amber-800">
            <AlertTriangle size={16} className="inline mr-2" />
            LiteLLM Proxy 未连接。请确保已执行 <code className="bg-amber-100 px-1 rounded">docker-compose up -d</code> 启动服务。
          </div>
        )}
      </section>

      {/* 模型列表 */}
      <section className="rounded-xl border border-[#d9d3c2] bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-[#f0ede3] px-5 py-4">
          <div className="flex items-center gap-2">
            <Cpu size={20} className="text-[#637166]" />
            <h3 className="font-semibold">已配置模型</h3>
            <span className="rounded-full bg-[#1d4f3a]/10 px-2.5 py-0.5 text-xs font-medium text-[#1d4f3a]">
              {models.length} 个
            </span>
          </div>
          <button
            className="flex items-center gap-1.5 rounded-lg bg-[#1d4f3a] px-4 py-2 text-sm font-medium text-white transition-all hover:bg-[#163829]"
            onClick={() => setShowAddForm(!showAddForm)}
            type="button"
          >
            <Plus size={16} />
            添加模型
          </button>
        </div>

        {/* 添加模型表单 */}
        {showAddForm && (
          <form
            className="border-b border-[#f0ede3] bg-[#f8f7f3] px-5 py-4"
            onSubmit={handleAddModel}
          >
            <h4 className="mb-3 text-sm font-semibold text-[#39443c]">添加新模型</h4>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-[#637166]">
                  模型别名 <span className="text-red-500">*</span>
                </label>
                <input
                  className="w-full rounded-lg border border-[#cfc7b5] px-3 py-2 text-sm focus:border-[#1d4f3a] focus:outline-none focus:ring-2 focus:ring-[#1d4f3a]/20"
                  onChange={(e) => setAddForm({ ...addForm, model_name: e.target.value })}
                  placeholder="如 my-gpt-4o"
                  required
                  value={addForm.model_name}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-[#637166]">
                  提供商 <span className="text-red-500">*</span>
                </label>
                <select
                  className="w-full rounded-lg border border-[#cfc7b5] px-3 py-2 text-sm focus:border-[#1d4f3a] focus:outline-none focus:ring-2 focus:ring-[#1d4f3a]/20 bg-white"
                  onChange={(e) => setAddForm({ ...addForm, provider: e.target.value })}
                  value={addForm.provider}
                >
                  {providerOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-[#637166]">
                  模型名 <span className="text-red-500">*</span>
                </label>
                <input
                  className="w-full rounded-lg border border-[#cfc7b5] px-3 py-2 text-sm focus:border-[#1d4f3a] focus:outline-none focus:ring-2 focus:ring-[#1d4f3a]/20"
                  onChange={(e) => setAddForm({ ...addForm, model: e.target.value })}
                  placeholder="如 gpt-4o"
                  required
                  value={addForm.model}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-[#637166]">API Key</label>
                <input
                  className="w-full rounded-lg border border-[#cfc7b5] px-3 py-2 text-sm focus:border-[#1d4f3a] focus:outline-none focus:ring-2 focus:ring-[#1d4f3a]/20"
                  onChange={(e) => setAddForm({ ...addForm, api_key: e.target.value })}
                  placeholder="sk-..."
                  type="password"
                  value={addForm.api_key}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-[#637166]">
                  API 端点（可选）
                </label>
                <input
                  className="w-full rounded-lg border border-[#cfc7b5] px-3 py-2 text-sm focus:border-[#1d4f3a] focus:outline-none focus:ring-2 focus:ring-[#1d4f3a]/20"
                  onChange={(e) => setAddForm({ ...addForm, api_base: e.target.value })}
                  placeholder="如 http://localhost:11434/v1"
                  value={addForm.api_base}
                />
              </div>
              <div className="flex items-end gap-2">
                <button
                  className="rounded-lg bg-[#1d4f3a] px-4 py-2 text-sm font-medium text-white transition-all hover:bg-[#163829] disabled:opacity-50"
                  disabled={adding}
                  type="submit"
                >
                  {adding ? "添加中..." : "确认添加"}
                </button>
                <button
                  className="rounded-lg border border-[#cfc7b5] px-4 py-2 text-sm transition-colors hover:bg-[#ebe7dc]"
                  onClick={() => setShowAddForm(false)}
                  type="button"
                >
                  取消
                </button>
              </div>
            </div>
          </form>
        )}

        {/* 模型表格 */}
        {loading ? (
          <div className="flex items-center justify-center py-12 text-[#637166]">
            <RefreshCw className="animate-spin mr-2" size={16} />
            加载中...
          </div>
        ) : models.length === 0 ? (
          <div className="py-12 text-center text-[#637166]">
            <Cpu size={32} className="mx-auto mb-3 opacity-30" />
            <p>暂无已配置的模型</p>
            <p className="mt-1 text-sm">点击"添加模型"开始配置第一个 LLM 模型</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left text-sm">
              <thead className="bg-[#f8f7f3] text-[#637166]">
                <tr>
                  <th className="px-5 py-3 font-medium">模型别名</th>
                  <th className="px-5 py-3 font-medium">提供商</th>
                  <th className="px-5 py-3 font-medium">实际模型</th>
                  <th className="px-5 py-3 font-medium">API Key</th>
                  <th className="px-5 py-3 font-medium">限速</th>
                  <th className="px-5 py-3 font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                {models.map((model, index) => (
                  <tr
                    className={`border-t border-[#f0ede3] transition-colors ${
                      model.model_name === defaultModel
                        ? "bg-[#edf4ef]"
                        : index % 2 === 0
                          ? "bg-white hover:bg-[#fafaf5]"
                          : "bg-[#fbfaf6] hover:bg-[#f5f4ef]"
                    }`}
                    key={model.model_name}
                  >
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-[#1d4f3a]">{model.model_name}</span>
                        {model.model_name === defaultModel && (
                          <span className="rounded-full bg-[#1d4f3a] px-2 py-0.5 text-[10px] font-medium text-white">
                            默认
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-5 py-3 text-[#39443c]">
                      <span className="rounded-full bg-[#ebe7dc] px-2 py-0.5 text-xs font-medium">
                        {model.provider || "-"}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-[#39443c] font-mono text-xs">
                      {model.model || "-"}
                    </td>
                    <td className="px-5 py-3">
                      {model.has_api_key ? (
                        <span className="flex items-center gap-1 text-[#2f7d57] text-xs">
                          <Key size={12} />
                          已配置
                        </span>
                      ) : model.api_base ? (
                        <span className="flex items-center gap-1 text-[#637166] text-xs">
                          <Link size={12} />
                          本地
                        </span>
                      ) : (
                        <span className="text-[#b94a48] text-xs">未配置</span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-xs text-[#637166]">
                      {model.rpm} RPM / {model.tpm} TPM
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-1.5">
                        <button
                          className="rounded-md p-1.5 text-[#637166] transition-colors hover:bg-[#f0ede3] hover:text-[#1d4f3a]"
                          disabled={testingModel === model.model_name}
                          onClick={() => handleTestModel(model.model_name)}
                          title="测试模型"
                          type="button"
                        >
                          {testingModel === model.model_name ? (
                            <RefreshCw size={15} className="animate-spin" />
                          ) : (
                            <Zap size={15} />
                          )}
                        </button>
                        {model.model_name !== defaultModel && (
                          <button
                            className="rounded-md p-1.5 text-[#637166] transition-colors hover:bg-[#edf4ef] hover:text-[#1d4f3a]"
                            onClick={() => handleSetDefault(model.model_name)}
                            title="设为默认"
                            type="button"
                          >
                            <CheckCircle size={15} />
                          </button>
                        )}
                        <button
                          className="rounded-md p-1.5 text-[#637166] transition-colors hover:bg-red-50 hover:text-red-600"
                          onClick={() => handleDeleteModel(model.model_name)}
                          title="删除模型"
                          type="button"
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* 测试结果 */}
      {testResult && (
        <section
          className={`rounded-xl border p-5 shadow-sm ${
            testResult.ok
              ? "border-green-200 bg-green-50"
              : "border-red-200 bg-red-50"
          }`}
        >
          <div className="flex items-center gap-2 mb-2">
            {testResult.ok ? (
              <CheckCircle size={18} className="text-[#2f7d57]" />
            ) : (
              <XCircle size={18} className="text-[#b94a48]" />
            )}
            <h3 className="font-semibold">
              {testResult.ok ? "测试成功" : "测试失败"} — {testResult.model_name}
            </h3>
            <button
              className="ml-auto text-sm text-[#637166] hover:text-[#39443c]"
              onClick={() => setTestResult(null)}
              type="button"
            >
              关闭
            </button>
          </div>
          {testResult.ok ? (
            <p className="text-sm text-[#39443c] whitespace-pre-wrap">{testResult.reply}</p>
          ) : (
            <p className="text-sm text-[#9b3733]">{testResult.error}</p>
          )}
        </section>
      )}

      {/* 错误提示 */}
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-[#9b3733]">
          <AlertTriangle size={16} className="inline mr-2" />
          {error}
          <button
            className="ml-2 underline"
            onClick={() => setError("")}
            type="button"
          >
            关闭
          </button>
        </div>
      )}
    </div>
  );
}
