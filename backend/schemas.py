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


class ChatResponse(BaseModel):
    status: str
    reply: str


class AuditReport(BaseModel):
    status: str = "ok"
    score: int
    risks: list[SecurityRisk]
