from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

FORBIDDEN_ACCOUNT_FIELDS = {"password", "secret", "token"}


class Importance(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class SafetyPolicy(BaseModel):
    storesPasswords: bool = False
    storesRecoveryCodeValues: bool = False
    storesThirdPartyCredentials: bool = False
    requiresOwnerAccount: bool = True


class LoginMethod(BaseModel):
    type: Literal["email", "phone", "username", "wechat", "qq", "apple", "google", "github", "unknown"]
    identifierHint: str | None = None
    lastConfirmedAt: str | None = None
    confidence: float = Field(default=0.5, ge=0, le=1)


class BindingRelation(BaseModel):
    kind: Literal["email", "phone", "device", "third_party"]
    value: str | None = Field(default=None, exclude=True)
    valueMasked: str | None = None
    status: Literal["active", "old", "unknown"] = "unknown"
    confidence: float = Field(default=0.5, ge=0, le=1)


class RecoveryPath(BaseModel):
    kind: Literal["email", "phone", "mfa_device", "recovery_code_location", "support_ticket"]
    locationHint: str | None = None
    officialUrlHint: str | None = None
    confidence: float = Field(default=0.5, ge=0, le=1)

    @model_validator(mode="after")
    def reject_recovery_code_value(self) -> "RecoveryPath":
        if self.kind == "recovery_code_location" and not self.locationHint:
            raise ValueError("recovery code entries must use locationHint only")
        return self


class EvidenceSource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: Literal["manual", "ocr", "email_summary", "sms_summary", "bookmark"]
    contentRedacted: str
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UserNote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    contentRedacted: str
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SecurityRisk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    level: RiskLevel
    title: str
    reason: str
    suggestion: str


class AccountIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid4()))
    platformName: str
    loginUrl: str | None = None
    registerMethod: str | None = None
    loginMethods: list[LoginMethod] = Field(default_factory=list)
    bindings: list[BindingRelation] = Field(default_factory=list)
    mfaEnabled: bool = False
    authenticatorLocationHint: str | None = None
    recoveryPaths: list[RecoveryPath] = Field(default_factory=list)
    importance: Importance = Importance.medium
    lastConfirmedAt: str | None = None
    riskTags: list[str] = Field(default_factory=list)
    notes: list[UserNote] = Field(default_factory=list)
    evidence: list[EvidenceSource] = Field(default_factory=list)

    @field_validator("platformName")
    @classmethod
    def platform_name_required(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("platformName is required")
        return stripped
