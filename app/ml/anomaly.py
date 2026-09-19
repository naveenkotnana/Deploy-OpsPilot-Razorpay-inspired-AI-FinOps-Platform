"""Anomaly detection = Isolation Forest (unsupervised) + deterministic rules.

Design decision: the ML model proposes, the RULES decide severity. Severity is
never produced by a model or an LLM because it drives escalation policy and
must be reproducible. IsolationForest only contributes anomaly_score.
"""
import datetime as dt
import uuid
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import Anomaly, Alert

# Deterministic thresholds (documented in docs/ml-anomaly-detection.md)
SEV_THRESHOLDS = [(40.0, "CRITICAL"), (25.0, "HIGH"), (15.0, "MEDIUM"), (8.0, "LOW")]
EXCEPTION_SEV = [(20, "CRITICAL"), (10, "HIGH"), (5, "MEDIUM"), (1, "LOW")]


def severity_from_pct(pct: float) -> str:
    a = abs(pct)
    for thr, sev in SEV_THRESHOLDS:
        if a >= thr:
            return sev
    return "INFO"


def severity_from_exceptions(n: int) -> str:
    for thr, sev in EXCEPTION_SEV:
        if n >= thr:
            return sev
    return "INFO"


def build_features(db: Session) -> pd.DataFrame:
    """Location-month feature matrix. Location grain chosen because an
    operational root cause is almost always site-scoped."""
    rows = db.execute(text("""
        SELECT m.billing_month, m.location_code,
               SUM(m.total_revenue)   AS revenue,
               SUM(m.water_revenue)   AS water_revenue,
               SUM(m.rental_revenue)  AS rental_revenue,
               SUM(m.water_usage_m3)  AS usage_m3,
               COUNT(*)               AS apartments,
               SUM(CASE WHEN m.validation_flag='EXCEPTION' THEN 1 ELSE 0 END) AS exceptions,
               SUM(CASE WHEN m.water_active_days>0 THEN 1 ELSE 0 END)  AS active_water,
               SUM(CASE WHEN m.rental_active_days>0 THEN 1 ELSE 0 END) AS active_rental
        FROM monthly_revenue m GROUP BY m.billing_month, m.location_code
    """)).mappings().all()
    df = pd.DataFrame([dict(r) for r in rows])
    if df.empty:
        return df
    df = df.sort_values(["location_code", "billing_month"])
    g = df.groupby("location_code")
    df["revenue_change_pct"] = g["revenue"].pct_change().fillna(0) * 100
    df["usage_change_pct"] = g["usage_m3"].pct_change().fillna(0) * 100
    df["rev_per_apartment"] = df["revenue"] / df["apartments"].replace(0, np.nan)
    df["exception_rate"] = df["exceptions"] / df["apartments"].replace(0, np.nan)
    return df.fillna(0)


FEATURES = ["revenue", "usage_m3", "apartments", "exceptions",
            "revenue_change_pct", "usage_change_pct",
            "rev_per_apartment", "exception_rate", "active_water", "active_rental"]


def detect(db: Session, contamination=0.08, seed=42) -> dict:
    df = build_features(db)
    if df.empty:
        return {"anomalies": 0, "alerts": 0, "rows_scored": 0}

    X = df[FEATURES].astype(float).values
    model = IsolationForest(n_estimators=200, contamination=contamination,
                            random_state=seed)
    model.fit(X)
    df["iso_flag"] = model.predict(X)                 # -1 anomalous
    df["anomaly_score"] = -model.score_samples(X)     # higher = more anomalous

    db.execute(text("DELETE FROM anomalies"))
    db.execute(text("DELETE FROM alerts"))

    found = []
    for r in df.itertuples():
        reasons, sev, method = [], "INFO", None

        # --- deterministic rules first (they win on severity) ---
        rule_sev = "INFO"
        if abs(r.revenue_change_pct) >= 8.0:
            reasons.append(f"Revenue moved {r.revenue_change_pct:+.1f}% MoM")
            rule_sev = max(rule_sev, severity_from_pct(r.revenue_change_pct),
                           key=_sev_rank)
        if r.exceptions >= 1:
            reasons.append(f"{int(r.exceptions)} validation exception(s)")
            rule_sev = max(rule_sev, severity_from_exceptions(int(r.exceptions)),
                           key=_sev_rank)
        if abs(r.usage_change_pct) >= 25.0:
            reasons.append(f"Water usage moved {r.usage_change_pct:+.1f}% MoM")
            rule_sev = max(rule_sev, severity_from_pct(r.usage_change_pct), key=_sev_rank)

        iso = r.iso_flag == -1
        if iso:
            reasons.append(f"IsolationForest flagged multivariate outlier "
                           f"(score {r.anomaly_score:.3f})")

        if not reasons:
            continue

        method = "RULE+ISOLATION_FOREST" if (iso and rule_sev != "INFO") else \
                 ("ISOLATION_FOREST" if iso else "RULE")
        # ML-only detections are capped at LOW: no rule breached, so we do not
        # escalate on an unsupervised score alone.
        sev = rule_sev if rule_sev != "INFO" else "LOW"

        aid = f"ANM-{r.billing_month}-{r.location_code}-{uuid.uuid4().hex[:4]}"
        db.add(Anomaly(anomaly_id=aid, billing_month=r.billing_month,
                       entity_type="LOCATION", entity_id=r.location_code,
                       metric="total_revenue", method=method,
                       anomaly_score=round(float(r.anomaly_score), 4), severity=sev,
                       reason="; ".join(reasons), observed_value=round(float(r.revenue), 2),
                       expected_value=None))

        if sev in ("MEDIUM", "HIGH", "CRITICAL"):
            db.add(Alert(alert_id=f"ALT-{r.billing_month}-{r.location_code}",
                         metric="total_revenue", entity=r.location_code,
                         billing_month=r.billing_month, severity=sev,
                         observed_value=round(float(r.revenue), 2),
                         expected_value=None,
                         anomaly_score=round(float(r.anomaly_score), 4),
                         evidence_summary="; ".join(reasons), status="OPEN",
                         detected_at=dt.datetime.now()))
        found.append((aid, sev))

    db.commit()
    n_alerts = db.execute(text("SELECT COUNT(*) FROM alerts")).scalar()
    return {"rows_scored": len(df), "anomalies": len(found), "alerts": int(n_alerts)}


_RANK = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def _sev_rank(s: str) -> int:
    return _RANK.get(s, 0)
