from __future__ import annotations

from pydantic import BaseModel, Field

from backend.models import AccountIdentity, SecurityRisk


class SafetyBlockedResponse(BaseModel):
    status: str = "safety_blocked"
    code: str
    message: str


class ClueExtractRequest(BaseModel):
    text: str
    sourceType: str = "manual"


class ClueExtractResponse(BaseModel):
    status: str
    platforms: list[str] = Field(default_factory=list)
    emailsMasked: list[str] = Field(default_factory=list)
    phonesMasked: list[str] = Field(default_factory=list)
    loginMethods: list[str] = Field(default_factory=list)
    evidence: dict | None = None
    confidence: float = 0.0


class RecoveryPlanRequest(BaseModel):
    platformName: str
    claimOwnership: bool = False


class RecoveryPlanResponse(BaseModel):
    status: str
    platformName: str
    legalReminder: str
    possibleLoginMethods: list[str]
    bindings: list[dict]
    officialPathHints: list[str]
    recommendedSteps: list[str]
    risks: list[str]
    uncertainFields: list[str]


class MigrationPhoneRequest(BaseModel):
    phone: str


class MigrationEmailRequest(BaseModel):
    email: str


class MigrationResponse(BaseModel):
    status: str = "ok"
    affectedAccounts: list[AccountIdentity]
    migrationPriority: list[str]
    steps: list[str]


class OcrImportRequest(BaseModel):
    ocrText: str


class ChatRequest(BaseModel):
    message: str
    stream: bool = False


class ChatResponse(BaseModel):
    status: str
    reply: str


class AuditReport(BaseModel):
    status: str = "ok"
    score: int
    risks: list[SecurityRisk]


# ============================================================
# LLM 配置管理 Schemas
# ============================================================

class LLMModelItem(BaseModel):
    """LiteLLM Proxy 中的模型信息（返回给前端）"""
    model_name: str
    provider: str = ""
    model: str = ""
    api_base: str = ""
    rpm: int = 0
    tpm: int = 0
    has_api_key: bool = False  # 是否已配置 API Key（不返回 key 内容）


class LLMModelListResponse(BaseModel):
    """模型列表响应"""
    models: list[LLMModelItem]
    total: int


class LLMModelAddRequest(BaseModel):
    """添加模型请求"""
    model_name: str = Field(..., description="模型别名，如 my-gpt-4")
    provider: str = Field(..., description="提供商: openai, anthropic, openai_like, ollama 等")
    model: str = Field(..., description="实际模型名，如 gpt-4o")
    api_key: str = Field(default="", description="API Key")
    api_base: str = Field(default="", description="自定义 API 端点（Ollama/vLLM 等）")
    rpm: int = Field(default=100, description="每分钟请求限制")
    tpm: int = Field(default=100000, description="每分钟 token 限制")


class LLMModelDeleteRequest(BaseModel):
    """删除模型请求"""
    model_name: str


class LLMModelTestRequest(BaseModel):
    """测试模型请求"""
    model_name: str
    message: str = "Hello, this is a test message."


class LLMConfigResponse(BaseModel):
    """LLM 配置响应"""
    default_model: str = ""
    proxy_url: str = ""
    proxy_healthy: bool = False


class LLMConfigUpdateRequest(BaseModel):
    """更新 LLM 配置请求"""
    default_model: str = Field(..., description="默认模型别名")
