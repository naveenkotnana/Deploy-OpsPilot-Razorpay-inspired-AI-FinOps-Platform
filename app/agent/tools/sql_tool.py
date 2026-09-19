"""READ-ONLY SQL tool.

Security model: the LLM never writes SQL. It chooses a query NAME from an
allowlist and supplies typed parameters. The application owns the SQL text.
This eliminates SQL injection through the model by construction rather than by
filtering, which is why there is no "sanitise the LLM's SQL" code path here.

A raw-SQL escape hatch exists for the API layer only and is still validated:
SELECT-only, single statement, allowlisted tables, forced row limit.
"""
import re, time
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.analytics.queries import QUERIES
from app.core.config import settings

ALLOWED_TABLES = {
    "monthly_revenue", "apartments", "buildings", "devices", "water_usage",
    "rental_plans", "water_plans", "plan_assignments", "anomalies", "alerts",
    "validation_results", "ingestion_runs",
}
FORBIDDEN = re.compile(
    r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|ATTACH|"
    r"PRAGMA|COPY|EXEC|MERGE|REPLACE)\b", re.I)


class SQLToolError(Exception):
    pass


def validate_raw_sql(sql: str) -> str:
    s = sql.strip().rstrip(";")
    if ";" in s:
        raise SQLToolError("Multiple statements are not permitted")
    if not re.match(r"^\s*(SELECT|WITH)\b", s, re.I):
        raise SQLToolError("Only SELECT/WITH statements are permitted")
    if FORBIDDEN.search(s):
        raise SQLToolError("Write or DDL keyword detected")
    referenced = set(re.findall(r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)", s, re.I))
    bad = {t.lower() for t in referenced} - ALLOWED_TABLES
    if bad:
        raise SQLToolError(f"Table(s) not allowlisted: {sorted(bad)}")
    if not re.search(r"\bLIMIT\b", s, re.I):
        s += f" LIMIT {settings.SQL_ROW_LIMIT}"
    return s


def run_named_query(db: Session, name: str, params: Optional[dict] = None,
                    limit: int = None) -> dict:
    """The agent-facing entrypoint. name must be in the analytics allowlist."""
    t0 = time.time()
    if name not in QUERIES:
        return {"ok": False, "error": f"Query '{name}' is not allowlisted",
                "allowed": sorted(QUERIES), "rows": [], "row_count": 0}
    limit = limit or settings.SQL_ROW_LIMIT
    sql = QUERIES[name].strip().rstrip(";")
    sql = f"SELECT * FROM ({sql}) AS q LIMIT :_lim"
    p = dict(params or {})
    p["_lim"] = limit
    try:
        rows = db.execute(text(sql), p).mappings().all()
        return {"ok": True, "query_name": name,
                "rows": [dict(r) for r in rows], "row_count": len(rows),
                "latency_ms": int((time.time() - t0) * 1000), "truncated": len(rows) >= limit}
    except Exception as e:
        return {"ok": False, "query_name": name, "error": f"{type(e).__name__}: {e}",
                "rows": [], "row_count": 0,
                "latency_ms": int((time.time() - t0) * 1000)}


def run_raw_sql(db: Session, sql: str) -> dict:
    t0 = time.time()
    try:
        safe = validate_raw_sql(sql)
    except SQLToolError as e:
        return {"ok": False, "error": str(e), "rows": [], "row_count": 0}
    try:
        rows = db.execute(text(safe)).mappings().all()
        return {"ok": True, "rows": [dict(r) for r in rows], "row_count": len(rows),
                "executed_sql": safe, "latency_ms": int((time.time() - t0) * 1000)}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "rows": [], "row_count": 0}
