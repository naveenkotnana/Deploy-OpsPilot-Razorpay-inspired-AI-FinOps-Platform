"""Local mock business actions. Writes ONLY to our own database.

Idempotency: every action carries a deterministic key
(workflow_id + action_type). A repeat is recorded as DUPLICATE_SKIPPED, so a
retried workflow cannot raise two incidents.
"""
import hashlib, json, uuid
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.models import ActionRecord

SENSITIVE_ACTIONS = {"create_incident", "create_ticket", "send_notification"}


def idempotency_key(workflow_id: str, action_type: str, payload: dict) -> str:
    raw = f"{workflow_id}|{action_type}|{json.dumps(payload, sort_keys=True)}"
    return hashlib.sha256(raw.encode()).hexdigest()[:40]


def _execute(db: Session, workflow_id: str, action_type: str, payload: dict) -> dict:
    key = idempotency_key(workflow_id, action_type, payload)
    existing = db.query(ActionRecord).filter(
        ActionRecord.idempotency_key == key).one_or_none()
    if existing:
        return {"ok": True, "status": "DUPLICATE_SKIPPED",
                "action_id": existing.action_id, "action_type": action_type,
                "note": "Identical action already executed for this workflow."}
    action_id = f"ACT-{uuid.uuid4().hex[:10]}"
    rec = ActionRecord(action_id=action_id, workflow_id=workflow_id,
                       action_type=action_type.upper(), idempotency_key=key,
                       payload=json.dumps(payload), status="EXECUTED")
    db.add(rec)
    db.commit()
    return {"ok": True, "status": "EXECUTED", "action_id": action_id,
            "action_type": action_type, "payload": payload}


def create_incident(db, workflow_id, title, severity, detail=""):
    return _execute(db, workflow_id, "create_incident",
                    {"title": title, "severity": severity, "detail": detail})


def create_ticket(db, workflow_id, title, queue="OPS", detail=""):
    return _execute(db, workflow_id, "create_ticket",
                    {"title": title, "queue": queue, "detail": detail})


def send_notification(db, workflow_id, channel, message):
    return _execute(db, workflow_id, "send_notification",
                    {"channel": channel, "message": message})


ACTION_REGISTRY = {"create_incident": create_incident,
                   "create_ticket": create_ticket,
                   "send_notification": send_notification}
