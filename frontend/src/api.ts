export type LoginMethod = {
  type: string;
  identifierHint?: string | null;
  confidence?: number;
};

export type Binding = {
  kind: string;
  valueMasked?: string | null;
  status?: string;
  confidence?: number;
};

export type RecoveryPath = {
  kind: string;
  locationHint?: string | null;
  officialUrlHint?: string | null;
  confidence?: number;
};

export type AccountIdentity = {
  id: string;
  platformName: string;
  loginUrl?: string | null;
  registerMethod?: string | null;
  loginMethods: LoginMethod[];
  bindings: Binding[];
  mfaEnabled: boolean;
  authenticatorLocationHint?: string | null;
  recoveryPaths: RecoveryPath[];
  importance: string;
  lastConfirmedAt?: string | null;
  riskTags: string[];
};

export type RecoveryPlan = {
  status: string;
  platformName: string;
  legalReminder: string;
  possibleLoginMethods: string[];
  bindings: Binding[];
  officialPathHints: string[];
  recommendedSteps: string[];
  risks: string[];
  uncertainFields: string[];
};

export type AuditReport = {
  status: string;
  score: number;
  risks: Array<{
    id: string;
    level: string;
    title: string;
    reason: string;
    suggestion: string;
  }>;
};

export type MigrationReport = {
  status: string;
  affectedAccounts: AccountIdentity[];
  migrationPriority: string[];
  steps: string[];
};

export type ClueExtractResponse = {
  status: string;
  platforms: string[];
  emailsMasked: string[];
  phonesMasked: string[];
  loginMethods: string[];
  confidence: number;
};

export type ChatResponse =
  | { status: "ok"; reply: string; streaming?: boolean }
  | { status: "safety_blocked"; code: string; message: string };

export type StreamingChatResponse = {
  onChunk: (chunk: string) => void;
  onComplete: (fullReply: string) => void;
  onError: (error: Error) => void;
};

// ============================================================
// LLM 配置管理类型
// ============================================================

export type LLMModelItem = {
  model_name: string;
  provider: string;
  model: string;
  api_base: string;
  rpm: number;
  tpm: number;
  has_api_key: boolean;
};

export type LLMModelListResponse = {
  models: LLMModelItem[];
  total: number;
};

export type LLMConfigResponse = {
  default_model: string;
  proxy_url: string;
  proxy_healthy: boolean;
};

export type LLMModelAddRequest = {
  model_name: string;
  provider: string;
  model: string;
  api_key?: string;
  api_base?: string;
  rpm?: number;
  tpm?: number;
};

export type LLMModelTestRequest = {
  model_name: string;
  message?: string;
};

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const defaultBaseUrl = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");

export function createApiClient(baseUrl = defaultBaseUrl) {
  const normalizedBase = baseUrl.replace(/\/+$/, "");

  async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    if (init.body && !headers.has("content-type")) {
      headers.set("content-type", "application/json");
    }

    let response: Response;
    try {
      response = await fetch(`${normalizedBase}${path}`, {
        ...init,
        headers,
      });
    } catch (error) {
      throw new ApiError(`后端不可用：${error instanceof Error ? error.message : "无法连接服务"}`);
    }

    const text = await response.text();
    const contentType = response.headers.get("content-type") ?? "";
    const trimmedText = text.trim();
    const looksLikeJson = trimmedText.startsWith("{") || trimmedText.startsWith("[");
    if (text && !contentType.includes("application/json") && !looksLikeJson) {
      throw new ApiError("API 返回了非 JSON 内容，请检查 VITE_API_BASE_URL 是否指向后端服务。", response.status);
    }

    let body: unknown = null;
    try {
      body = text ? JSON.parse(text) : null;
    } catch {
      throw new ApiError("API 返回了无法解析的 JSON 内容。", response.status);
    }

    if (!response.ok) {
      const message =
        readErrorMessage(body) ?? `请求失败：HTTP ${response.status}`;
      throw new ApiError(message, response.status);
    }

    return body as T;
  }

  async function streamingChat(
    message: string,
    callbacks: StreamingChatResponse
  ): Promise<void> {
    const headers = new Headers();
    headers.set("content-type", "application/json");

    try {
      const response = await fetch(`${normalizedBase}/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify({ message, stream: true }),
      });

      if (!response.ok) {
        const text = await response.text();
        let body: unknown = null;
        try {
          body = JSON.parse(text);
        } catch {
          // ignore JSON parse error
        }
        const message = readErrorMessage(body) ?? `请求失败：HTTP ${response.status}`;
        throw new ApiError(message, response.status);
      }

      if (!response.body) {
        throw new ApiError("浏览器不支持 streaming 响应");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulated = "";
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const dataStr = line.slice(6);
          if (dataStr.trim() === "[DONE]") continue;

          try {
            const chunk = JSON.parse(dataStr);
            const content = chunk.choices?.[0]?.delta?.content || "";
            if (content) {
              accumulated += content;
              callbacks.onChunk(content);
            }
          } catch {
            // ignore parse errors
          }
        }
      }

      callbacks.onComplete(accumulated);
    } catch (error) {
      callbacks.onError(error instanceof Error ? error : new Error(String(error)));
    }
  }

  return {
    health: () => request<{ status: string }>("/health"),
    accounts: () => request<AccountIdentity[]>("/accounts"),
    recoveryPlan: (platformName: string) =>
      request<RecoveryPlan>("/recovery/plan", {
        method: "POST",
        body: JSON.stringify({ platformName, claimOwnership: true }),
      }),
    auditRun: () => request<AuditReport>("/audit/run", { method: "POST" }),
    migrationPhone: (phone: string) =>
      request<MigrationReport>("/migration/phone", {
        method: "POST",
        body: JSON.stringify({ phone }),
      }),
    migrationEmail: (email: string) =>
      request<MigrationReport>("/migration/email", {
        method: "POST",
        body: JSON.stringify({ email }),
      }),
    ocrImport: (ocrText: string) =>
      request<ClueExtractResponse>("/ocr/import", {
        method: "POST",
        body: JSON.stringify({ ocrText }),
      }),
    chat: (message: string) =>
      request<ChatResponse>("/chat", {
        method: "POST",
        body: JSON.stringify({ message }),
      }),
    streamingChat,
    // LLM 配置管理 API
    llmGetConfig: () => request<LLMConfigResponse>("/llm/config"),
    llmUpdateConfig: (data: { default_model: string }) =>
      request<{ status: string; default_model: string }>("/llm/config", {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    llmListModels: () => request<LLMModelListResponse>("/llm/models"),
    llmAddModel: (data: LLMModelAddRequest) =>
      request<{ status: string; data: unknown }>("/llm/models", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    llmDeleteModel: (modelName: string) =>
      request<{ status: string; data: unknown }>(`/llm/models/${encodeURIComponent(modelName)}`, {
        method: "DELETE",
      }),
    llmTestModel: (data: LLMModelTestRequest) =>
      request<{ status: string; data: { ok: boolean; model_name: string; reply?: string; error?: string } }>(
        "/llm/models/test",
        {
          method: "POST",
          body: JSON.stringify(data),
        },
      ),
  };
}

export const api = createApiClient();

function readErrorMessage(body: unknown): string | null {
  if (!body || typeof body !== "object") {
    return null;
  }

  const record = body as Record<string, unknown>;
  const detail = record.detail;
  if (detail && typeof detail === "object") {
    const detailRecord = detail as Record<string, unknown>;
    if (typeof detailRecord.message === "string") return detailRecord.message;
    if (typeof detailRecord.code === "string") return detailRecord.code;
  }
  if (typeof record.message === "string") return record.message;
  return null;
}
