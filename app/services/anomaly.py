"""Anomaly detection service wrapper."""
from typing import Optional
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.ml.anomaly import detect


def detect_all_anomalies(db: Optional[Session] = None, verbose: bool = False):
    """Run unsupervised IsolationForest and deterministic rule evaluation."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        res = detect(db)
        if verbose:
            print("Anomaly detection result:", res)
        return res
    finally:
        if close_db:
            db.close()
