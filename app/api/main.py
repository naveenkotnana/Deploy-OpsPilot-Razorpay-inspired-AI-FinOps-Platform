"""OpsPilot REST API. Synthetic data only. Local Ollama only. No paid APIs."""
import json, time
import datetime as dt
from typing import List, Optional

from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

from app.agent.tools.action_tool import create_incident
from app.agent.workflow import resume_after_approval, run_investigation
from app.analytics.queries import QUERIES
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.security import (create_access_token, get_current_user, require,
                               seed_demo_users, verify_password)
from app.db.base import SessionLocal, get_db, init_db
from app.models import (ActionRecord, Alert, Approval, AuditLog,
                        EvaluationResult, User, Workflow)
from app.rag import ollama_client
from app.rag.store import get_store
from app.schemas.api import (AlertOut, ApprovalDecision, HealthOut,
                             IncidentCreate, InvestigateResponse, LoginRequest, Token)

setup_logging()

from contextlib import asynccontextmanager


@asynccontextmanager
async def _lifespan(application):
    init_db()
    db = SessionLocal()
    try:
        seed_demo_users(db)
    finally:
        db.close()
    yield   # application runs here


app = FastAPI(
    title="OpsPilot API",
    version="2.0",
    lifespan=_lifespan,
    description="AI Operations Workflow Automation & Intelligence Platform. "
                "SYNTHETIC DATA ONLY. All LLM inference runs locally via Ollama. "
                "No paid LLM APIs are used.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])

_METRICS = {"requests": 0, "errors": 0, "latency_ms_total": 0}


@app.middleware("http")
async def metrics_mw(request, call_next):
    t0 = time.time()
    _METRICS["requests"] += 1
    try:
        resp = await call_next(request)
    except Exception:
        _METRICS["errors"] += 1
        raise
    if resp.status_code >= 500:
        _METRICS["errors"] += 1
    _METRICS["latency_ms_total"] += int((time.time() - t0) * 1000)
    return resp


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ----------------------------------------------------------------- frontend
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root():
    html_file = STATIC_DIR / "index.html"
    if html_file.exists():
        return FileResponse(html_file, media_type="text/html")
    return HTMLResponse("<h1>OpsPilot API is running</h1><p>Visit <a href='/docs'>/docs</a></p>")


@app.get("/index.html", response_class=HTMLResponse, include_in_schema=False)
def index_html():
    return root()


@app.get("/index.htm", response_class=HTMLResponse, include_in_schema=False)
def index_htm():
    htm_file = STATIC_DIR / "index.htm"
    if htm_file.exists():
        return FileResponse(htm_file, media_type="text/html")
    return root()


@app.get("/favicon.ico", include_in_schema=False)
@app.get("/favicon.svg", include_in_schema=False)
def favicon():
    svg_file = STATIC_DIR / "favicon.svg"
    if svg_file.exists():
        return FileResponse(svg_file, media_type="image/svg+xml")
    return Response(status_code=204)


# ----------------------------------------------------------------- health
@app.get("/health", response_model=HealthOut, tags=["system"])
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        dbs = "up"
    except Exception as e:
        dbs = f"down: {type(e).__name__}"
    models = ollama_client.list_models()
    try:
        chunks = get_store().stats()["chunks"]
    except Exception:
        chunks = 0
    return HealthOut(status="ok" if dbs == "up" else "degraded", database=dbs,
                     ollama="up" if models else "unavailable",
                     ollama_models=models, rag_chunks=chunks)


# ------------------------------------------------------------------- auth
@app.post("/auth/login", response_model=Token, tags=["auth"])
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return Token(access_token=create_access_token(user), role=user.role,
                 user_id=user.user_id)


@app.get("/auth/me", tags=["auth"])
def me(user: User = Depends(get_current_user)):
    return {"user_id": user.user_id, "username": user.username, "role": user.role}


# ----------------------------------------------------------------- alerts
@app.get("/alerts", response_model=List[AlertOut], tags=["alerts"])
def list_alerts(severity: Optional[str] = None, status_f: Optional[str] = Query(None, alias="status"),
                db: Session = Depends(get_db), user=Depends(require("view"))):
    q = db.query(Alert)
    if severity:
        q = q.filter(Alert.severity == severity.upper())
    if status_f:
        q = q.filter(Alert.status == status_f.upper())
    return [AlertOut(alert_id=a.alert_id, metric=a.metric, entity=a.entity,
                     billing_month=a.billing_month, severity=a.severity,
                     observed_value=float(a.observed_value or 0),
                     anomaly_score=float(a.anomaly_score or 0),
                     evidence_summary=a.evidence_summary, status=a.status)
            for a in q.all()]


@app.get("/alerts/{alert_id}", tags=["alerts"])
def get_alert(alert_id: str, db: Session = Depends(get_db),
              user=Depends(require("view"))):
    a = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not a:
        raise HTTPException(404, "Alert not found")
    wfs = db.query(Workflow).filter(Workflow.alert_id == alert_id).all()
    return {"alert": {c.name: getattr(a, c.name) for c in a.__table__.columns},
            "workflows": [w.workflow_id for w in wfs]}


@app.post("/alerts/{alert_id}/investigate", response_model=InvestigateResponse,
          tags=["agent"])
def investigate(alert_id: str, question: Optional[str] = None,
                db: Session = Depends(get_db),
                user: User = Depends(require("investigate"))):
    if not db.query(Alert).filter(Alert.alert_id == alert_id).first():
        raise HTTPException(404, "Alert not found")
    s = run_investigation(db, alert_id, user.user_id, user.role, question)
    rec = s.get("recommendation", {})
    return InvestigateResponse(
        workflow_id=s["workflow_id"], alert_id=alert_id,
        evidence_verdict=s.get("evidence", {}).get("verdict", "UNKNOWN"),
        llm_available=bool(s.get("llm_available")), recommendation=rec,
        approval_required=bool(s.get("approval_required")),
        approval_status=s.get("approval_status", "NOT_REQUIRED"),
        citations=rec.get("citations", []), errors=s.get("errors", []),
        latency_ms=sum(s.get("node_timings", {}).values()))


# -------------------------------------------------------------- workflows
@app.get("/workflows/{workflow_id}", tags=["agent"])
def get_workflow(workflow_id: str, db: Session = Depends(get_db),
                 user=Depends(require("view"))):
    w = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
    if not w:
        raise HTTPException(404, "Workflow not found")
    return {"workflow_id": w.workflow_id, "alert_id": w.alert_id,
            "status": w.status, "approval_status": w.approval_status,
            "approval_required": w.approval_required, "final_action": w.final_action,
            "llm_available": w.llm_available, "latency_ms": w.latency_ms,
            "recommendation": json.loads(w.recommendation_json or "{}"),
            "evidence": json.loads(w.evidence_json or "{}"),
            "errors": json.loads(w.errors or "[]")}


@app.post("/workflows/{workflow_id}/approve", tags=["approval"])
def approve(workflow_id: str, body: ApprovalDecision,
            db: Session = Depends(get_db),
            user: User = Depends(require("approve"))):
    ap = db.query(Approval).filter(Approval.workflow_id == workflow_id).order_by(
        Approval.timestamp.desc()).first()
    if not ap:
        raise HTTPException(404, "No approval request for this workflow")
    if ap.decision != "PENDING":
        return {"ok": False, "status": ap.decision,
                "note": "Decision already recorded; idempotent no-op."}
    ap.decision, ap.approver, ap.reason = "APPROVED", user.user_id, body.reason
    ap.timestamp = dt.datetime.now()
    db.commit()
    result = resume_after_approval(db, workflow_id)
    return {"ok": result["ok"], "approval_id": ap.approval_id, "decision": "APPROVED",
            "action_result": result.get("action_result"), "errors": result.get("errors")}


@app.post("/workflows/{workflow_id}/reject", tags=["approval"])
def reject(workflow_id: str, body: ApprovalDecision,
           db: Session = Depends(get_db),
           user: User = Depends(require("reject"))):
    ap = db.query(Approval).filter(Approval.workflow_id == workflow_id).order_by(
        Approval.timestamp.desc()).first()
    if not ap:
        raise HTTPException(404, "No approval request for this workflow")
    if ap.decision != "PENDING":
        return {"ok": False, "status": ap.decision, "note": "Already decided."}
    ap.decision, ap.approver, ap.reason = "REJECTED", user.user_id, body.reason
    db.commit()
    w = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
    if w:
        w.approval_status, w.status = "REJECTED", "REJECTED"
        db.commit()
    return {"ok": True, "decision": "REJECTED", "action_executed": False,
            "note": "No action executes on rejection."}


# ------------------------------------------------------------- analytics
@app.get("/revenue", tags=["analytics"])
def revenue(query: str = "revenue_by_month", db: Session = Depends(get_db),
            user=Depends(require("view"))):
    from app.agent.tools.sql_tool import run_named_query
    r = run_named_query(db, query, limit=500)
    if not r["ok"]:
        raise HTTPException(400, r["error"])
    return r


@app.get("/analytics/queries", tags=["analytics"])
def list_queries(user=Depends(require("view"))):
    return {"queries": sorted(QUERIES)}


@app.get("/anomalies", tags=["analytics"])
def anomalies(db: Session = Depends(get_db), user=Depends(require("view"))):
    rows = db.execute(text("SELECT anomaly_id, billing_month, entity_id, method, "
                           "severity, anomaly_score, reason FROM anomalies "
                           "ORDER BY billing_month DESC")).mappings().all()
    return [dict(r) for r in rows]


@app.get("/data-quality", tags=["analytics"])
def data_quality(db: Session = Depends(get_db), user=Depends(require("view"))):
    runs = db.execute(text("SELECT run_id, source, records_received, records_loaded, "
                           "records_rejected, validation_status FROM ingestion_runs "
                           "ORDER BY start_time DESC")).mappings().all()
    checks = db.execute(text("SELECT source, check_name, status, observed, threshold "
                             "FROM validation_results")).mappings().all()
    return {"runs": [dict(r) for r in runs], "checks": [dict(c) for c in checks]}


# -------------------------------------------------------------- incidents
@app.get("/incidents", tags=["actions"])
def incidents(db: Session = Depends(get_db), user=Depends(require("view"))):
    rows = db.query(ActionRecord).order_by(ActionRecord.timestamp.desc()).all()
    return [{"action_id": r.action_id, "workflow_id": r.workflow_id,
             "action_type": r.action_type, "status": r.status,
             "payload": json.loads(r.payload), "timestamp": r.timestamp}
            for r in rows]


@app.post("/incidents", tags=["actions"])
def post_incident(body: IncidentCreate, db: Session = Depends(get_db),
                  user: User = Depends(require("approve"))):
    """Manual incident creation. Requires approve permission — an Analyst
    cannot create one, matching the approval gate's policy."""
    return create_incident(db, body.workflow_id, body.title, body.severity, body.detail)


# ------------------------------------------------------------------ audit
@app.get("/audit", tags=["audit"])
def audit(workflow_id: Optional[str] = None, limit: int = 200,
          db: Session = Depends(get_db), user=Depends(require("view"))):
    q = db.query(AuditLog)
    if workflow_id:
        q = q.filter(AuditLog.workflow_id == workflow_id)
    rows = q.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [{"audit_id": r.audit_id, "workflow_id": r.workflow_id,
             "user_id": r.user_id, "agent_node": r.agent_node, "tool_name": r.tool_name,
             "input_hash": r.input_hash, "result_status": r.result_status,
             "latency_ms": r.latency_ms, "approval_status": r.approval_status,
             "action": r.action, "timestamp": r.timestamp} for r in rows]


# ---------------------------------------------------------------- metrics
@app.get("/metrics", tags=["system"])
def metrics(db: Session = Depends(get_db), user=Depends(require("view"))):
    wf_total = db.query(Workflow).count()
    wf_completed = db.query(Workflow).filter(Workflow.status == "COMPLETED").count()
    wf_failed = db.query(Workflow).filter(Workflow.status == "FAILED").count()
    ap_total = db.query(Approval).count()
    ap_approved = db.query(Approval).filter(Approval.decision == "APPROVED").count()
    ap_rejected = db.query(Approval).filter(Approval.decision == "REJECTED").count()
    tool_rows = db.execute(text(
        "SELECT result_status, COUNT(*) FROM audit_logs GROUP BY result_status")).all()
    avg_lat = db.execute(text(
        "SELECT AVG(latency_ms) FROM workflows WHERE latency_ms IS NOT NULL")).scalar()
    return {
        "api": {"requests": _METRICS["requests"], "errors": _METRICS["errors"],
                "error_rate": round(_METRICS["errors"] / max(_METRICS["requests"], 1), 4),
                "avg_latency_ms": round(_METRICS["latency_ms_total"]
                                        / max(_METRICS["requests"], 1), 2)},
        "workflows": {"total": wf_total, "completed": wf_completed, "failed": wf_failed,
                      "success_rate": round(wf_completed / max(wf_total, 1), 4),
                      "avg_latency_ms": round(float(avg_lat or 0), 2)},
        "approvals": {"total": ap_total, "approved": ap_approved, "rejected": ap_rejected,
                      "approval_rate": round(ap_approved / max(ap_total, 1), 4),
                      "rejection_rate": round(ap_rejected / max(ap_total, 1), 4)},
        "audit_status_counts": {r[0]: int(r[1]) for r in tool_rows},
        "ollama": {"available": bool(ollama_client.list_models()),
                   "models": ollama_client.list_models(),
                   "note": "Local inference. No API cost exists and none is reported."},
    }


@app.get("/evaluation", tags=["evaluation"])
def evaluation(suite: Optional[str] = None, db: Session = Depends(get_db),
               user=Depends(require("view"))):
    q = db.query(EvaluationResult)
    if suite:
        q = q.filter(EvaluationResult.suite == suite.upper())
    rows = q.order_by(EvaluationResult.run_at.desc()).limit(500).all()
    by_suite = {}
    for r in rows:
        s = by_suite.setdefault(r.suite, {"passed": 0, "total": 0})
        s["total"] += 1
        s["passed"] += 1 if r.passed else 0
    for s in by_suite.values():
        s["pass_rate"] = round(s["passed"] / max(s["total"], 1), 4)
    return {"summary": by_suite,
            "results": [{"suite": r.suite, "case_id": r.case_id, "passed": r.passed,
                         "score": float(r.score) if r.score is not None else None,
                         "detail": r.detail, "run_at": r.run_at} for r in rows]}
