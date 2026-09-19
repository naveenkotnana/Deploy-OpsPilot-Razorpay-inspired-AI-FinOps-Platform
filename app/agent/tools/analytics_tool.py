"""Trusted deterministic calculations.

The LLM is never asked to do arithmetic. It calls these and quotes the result.
Every function returns the numbers AND the basis, so the evidence validator can
check a claim against a real figure.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session


def calculate_revenue(db: Session, billing_month: str, location: str = None) -> dict:
    q = ("SELECT SUM(total_revenue) t, SUM(water_revenue) w, SUM(rental_revenue) r, "
         "COUNT(*) n FROM monthly_revenue WHERE billing_month=:m")
    p = {"m": billing_month}
    if location:
        q += " AND location_code=:loc"; p["loc"] = location
    row = db.execute(text(q), p).first()
    return {"billing_month": billing_month, "location": location or "ALL",
            "total_revenue": float(row[0] or 0), "water_revenue": float(row[1] or 0),
            "rental_revenue": float(row[2] or 0), "apartments": int(row[3] or 0)}


def calculate_active_devices(db: Session, location: str = None) -> dict:
    q = ("SELECT d.service_type, COUNT(*) FROM devices d "
         "JOIN apartments a ON a.apartment_id=d.apartment_id "
         "WHERE d.device_status='ACTIVE'")
    p = {}
    if location:
        q += " AND a.location_code=:loc"; p["loc"] = location
    q += " GROUP BY d.service_type"
    rows = db.execute(text(q), p).all()
    out = {r[0]: int(r[1]) for r in rows}
    out["total"] = sum(out.values())
    out["location"] = location or "ALL"
    return out


def calculate_revenue_change(db: Session, billing_month: str, location: str = None) -> dict:
    q = ("SELECT billing_month, SUM(total_revenue) FROM monthly_revenue "
         "WHERE billing_month <= :m")
    p = {"m": billing_month}
    if location:
        q += " AND location_code=:loc"; p["loc"] = location
    q += " GROUP BY billing_month ORDER BY billing_month DESC LIMIT 2"
    rows = db.execute(text(q), p).all()
    if len(rows) < 2:
        return {"billing_month": billing_month, "location": location or "ALL",
                "current": float(rows[0][1]) if rows else 0.0,
                "previous": None, "change_pct": None,
                "note": "No prior month available; change not computable."}
    cur, prev = float(rows[0][1]), float(rows[1][1])
    return {"billing_month": billing_month, "location": location or "ALL",
            "current": round(cur, 2), "previous": round(prev, 2),
            "previous_month": rows[1][0],
            "change_abs": round(cur - prev, 2),
            "change_pct": round(100 * (cur - prev) / prev, 2) if prev else None}


def calculate_plan_revenue(db: Session, billing_month: str) -> dict:
    w = db.execute(text("SELECT water_plan_id, SUM(water_revenue) FROM monthly_revenue "
                        "WHERE billing_month=:m AND water_plan_id IS NOT NULL "
                        "GROUP BY water_plan_id"), {"m": billing_month}).all()
    r = db.execute(text("SELECT rental_plan_id, SUM(rental_revenue) FROM monthly_revenue "
                        "WHERE billing_month=:m AND rental_plan_id IS NOT NULL "
                        "GROUP BY rental_plan_id"), {"m": billing_month}).all()
    return {"billing_month": billing_month,
            "water": {k: round(float(v), 2) for k, v in w},
            "rental": {k: round(float(v), 2) for k, v in r}}


def calculate_location_revenue(db: Session, billing_month: str) -> dict:
    rows = db.execute(text("SELECT location_code, SUM(total_revenue), COUNT(*) "
                           "FROM monthly_revenue WHERE billing_month=:m "
                           "GROUP BY location_code ORDER BY 2 DESC"),
                      {"m": billing_month}).all()
    return {"billing_month": billing_month,
            "locations": [{"location_code": r[0], "revenue": round(float(r[1]), 2),
                           "apartments": int(r[2])} for r in rows]}


def calculate_anomaly_context(db: Session, billing_month: str, location: str) -> dict:
    """Everything an investigator needs about one location-month, in one call."""
    rev = calculate_revenue(db, billing_month, location)
    chg = calculate_revenue_change(db, billing_month, location)
    exc = db.execute(text("SELECT exception_code, COUNT(*) FROM monthly_revenue "
                          "WHERE billing_month=:m AND location_code=:loc "
                          "AND validation_flag='EXCEPTION' GROUP BY exception_code"),
                     {"m": billing_month, "loc": location}).all()
    usage = db.execute(text("SELECT SUM(water_usage_m3) FROM monthly_revenue "
                            "WHERE billing_month=:m AND location_code=:loc"),
                       {"m": billing_month, "loc": location}).scalar()
    return {"revenue": rev, "change": chg,
            "exceptions": {r[0]: int(r[1]) for r in exc},
            "exception_total": sum(int(r[1]) for r in exc),
            "water_usage_m3": round(float(usage or 0), 3),
            "active_devices": calculate_active_devices(db, location)}


TOOL_REGISTRY = {
    "calculate_revenue": calculate_revenue,
    "calculate_active_devices": calculate_active_devices,
    "calculate_revenue_change": calculate_revenue_change,
    "calculate_plan_revenue": calculate_plan_revenue,
    "calculate_location_revenue": calculate_location_revenue,
    "calculate_anomaly_context": calculate_anomaly_context,
}
