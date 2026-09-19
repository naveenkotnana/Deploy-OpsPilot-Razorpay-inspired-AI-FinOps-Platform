from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AlertOut(BaseModel):
    alert_id: str
    metric: str
    entity: str
    billing_month: str
    severity: str
    observed_value: Optional[float] = None
    anomaly_score: Optional[float] = None
    evidence_summary: Optional[str] = None
    status: str


class RevenueRow(BaseModel):
    billing_month: str
    total_revenue: float
    water_revenue: float
    rental_revenue: float
    apartments: int
    mom_pct: Optional[float] = None
    rolling_3m_avg: Optional[float] = None


class InvestigateResponse(BaseModel):
    workflow_id: str
    alert_id: str
    evidence_verdict: str
    llm_available: bool
    recommendation: Dict[str, Any]
    approval_required: bool
    approval_status: str
    citations: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    latency_ms: int = 0


class ApprovalDecision(BaseModel):
    reason: Optional[str] = None


class IncidentCreate(BaseModel):
    workflow_id: str
    title: str
    severity: str = "MEDIUM"
    detail: str = ""


class HealthOut(BaseModel):
    status: str
    database: str
    ollama: str
    ollama_models: List[str]
    rag_chunks: int
    version: str = "2.0"
