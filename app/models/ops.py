"""Phase 2 tables: auth, workflow, approval, actions, audit, evaluation."""
from sqlalchemy import (Column, String, Integer, Numeric, DateTime, Text,
                        Boolean, UniqueConstraint, func)
from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    user_id = Column(String(30), primary_key=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(20), index=True)   # ANALYST | MANAGER | ADMIN
    is_active = Column(Boolean, default=True)


class Workflow(Base):
    __tablename__ = "workflows"
    workflow_id = Column(String(40), primary_key=True)
    alert_id = Column(String(40), index=True)
    user_id = Column(String(30), index=True)
    trace_id = Column(String(20), index=True)
    status = Column(String(30), index=True)   # RUNNING|AWAITING_APPROVAL|APPROVED|REJECTED|COMPLETED|FAILED
    question = Column(Text, nullable=True)
    evidence_json = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    recommendation_json = Column(Text, nullable=True)
    approval_required = Column(Boolean, default=True)
    approval_status = Column(String(20), default="PENDING", index=True)
    final_action = Column(String(60), nullable=True)
    errors = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    llm_available = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class Approval(Base):
    __tablename__ = "approvals"
    approval_id = Column(String(40), primary_key=True)
    workflow_id = Column(String(40), index=True)
    approver = Column(String(30))
    decision = Column(String(20), index=True)   # PENDING | APPROVED | REJECTED
    reason = Column(Text, nullable=True)
    recommended_action = Column(String(60))
    timestamp = Column(DateTime, server_default=func.now())


class ActionRecord(Base):
    """Local mock business actions. Idempotency key prevents duplicates."""
    __tablename__ = "action_records"
    action_id = Column(String(40), primary_key=True)
    workflow_id = Column(String(40), index=True)
    action_type = Column(String(40), index=True)   # CREATE_INCIDENT | CREATE_TICKET | SEND_NOTIFICATION
    idempotency_key = Column(String(120), unique=True, index=True)
    payload = Column(Text)
    status = Column(String(20), index=True)   # EXECUTED | DUPLICATE_SKIPPED | FAILED
    timestamp = Column(DateTime, server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"
    audit_id = Column(String(40), primary_key=True)
    workflow_id = Column(String(40), index=True)
    user_id = Column(String(30), index=True)
    agent_node = Column(String(40), index=True)
    tool_name = Column(String(40), nullable=True)
    input_hash = Column(String(64))
    result_status = Column(String(20), index=True)
    latency_ms = Column(Integer)
    approval_status = Column(String(20), nullable=True)
    action = Column(String(60), nullable=True)
    timestamp = Column(DateTime, server_default=func.now())


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    suite = Column(String(30), index=True)   # RAG | AGENT | SECURITY
    case_id = Column(String(40), index=True)
    passed = Column(Boolean, index=True)
    score = Column(Numeric(8, 4), nullable=True)
    detail = Column(Text, nullable=True)
    run_at = Column(DateTime, server_default=func.now())
    __table_args__ = (UniqueConstraint("suite", "case_id", "run_at", name="uq_eval"),)
