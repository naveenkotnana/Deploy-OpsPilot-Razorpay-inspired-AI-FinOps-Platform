"""Monthly revenue engine.

Business rules (source: DOC-001 revenue_calculation_sop):
  water_revenue  = base_fee * (water_active_days / days_in_month)
                   + consumption_m3 * rate_per_m3
  rental_revenue = monthly_rental * (rental_active_days / days_in_month)
  total_revenue  = water_revenue + rental_revenue

Missing-input policy: if a required input (plan, device, rate) is absent we
DO NOT guess. The row is written with validation_flag='EXCEPTION' and an
exception_code, and revenue components that cannot be computed are 0 with the
exception recorded. This is deliberate — a silently-imputed number is worse
than a flagged gap.
"""
import calendar
import datetime as dt
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import MonthlyRevenue

Q = Decimal("0.01")


def _money(x) -> Decimal:
    return Decimal(str(x)).quantize(Q, rounding=ROUND_HALF_UP)


def month_bounds(billing_month: str):
    y, m = map(int, billing_month.split("-"))
    days = calendar.monthrange(y, m)[1]
    return dt.date(y, m, 1), dt.date(y, m, days), days


def _as_date(v) -> Optional[dt.date]:
    """SQLite returns DATE columns as strings over raw SQL; normalise both."""
    if v is None or v == "":
        return None
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def active_days(start, end, m_start: dt.date, m_end: dt.date) -> int:
    """Overlap between a device's active window and the billing month."""
    start, end = _as_date(start), _as_date(end)
    if start is None:
        return 0
    s = max(start, m_start)
    e = min(end, m_end) if end else m_end
    return 0 if e < s else (e - s).days + 1


def compute_month(db: Session, billing_month: str) -> dict:
    m_start, m_end, days_in_month = month_bounds(billing_month)

    # Pull everything needed in one pass. Grouping by apartment keeps the
    # per-apartment computation deterministic and auditable.
    rows = db.execute(text("""
        SELECT a.apartment_id, a.location_code, a.status AS apt_status,
               d.device_id, d.service_type, d.activation_date, d.deactivation_date,
               d.device_status,
               pa.plan_id, pa.assignment_status
        FROM apartments a
        LEFT JOIN devices d ON d.apartment_id = a.apartment_id
        LEFT JOIN plan_assignments pa
               ON pa.device_id = d.device_id AND pa.assignment_status = 'ACTIVE'
        ORDER BY a.apartment_id
    """)).mappings().all()

    usage = {r[0]: float(r[1] or 0) for r in db.execute(text("""
        SELECT device_id, SUM(consumption_m3)
        FROM water_usage WHERE usage_date BETWEEN :s AND :e
        GROUP BY device_id
    """), {"s": m_start, "e": m_end}).all()}

    wplans = {r[0]: (float(r[1]), float(r[2])) for r in db.execute(
        text("SELECT water_plan_id, base_fee, rate_per_m3 FROM water_plans")).all()}
    rplans = {r[0]: float(r[1]) for r in db.execute(
        text("SELECT rental_plan_id, monthly_rental FROM rental_plans")).all()}

    apartments = {}
    for r in rows:
        apartments.setdefault(r["apartment_id"], {"location": r["location_code"],
                                                  "devices": []})
        if r["device_id"]:
            apartments[r["apartment_id"]]["devices"].append(r)

    db.execute(text("DELETE FROM monthly_revenue WHERE billing_month = :m"),
               {"m": billing_month})

    out, exceptions = [], 0
    for apt_id, info in apartments.items():
        water = [d for d in info["devices"] if d["service_type"] == "WATER"]
        rental = [d for d in info["devices"] if d["service_type"] == "RENTAL"]
        codes = []

        # --- water ---
        w_rev, w_days, w_m3 = Decimal("0.00"), 0, 0.0
        w_dev = w_plan = None
        if not water:
            codes.append("MISSING_WATER_DEVICE")
        else:
            if len(water) > 1:
                codes.append("MULTIPLE_WATER_DEVICES")
            d = water[0]
            w_dev, w_plan = d["device_id"], d["plan_id"]
            w_days = active_days(d["activation_date"], d["deactivation_date"], m_start, m_end)
            w_m3 = usage.get(w_dev, 0.0)
            if w_days > 0 and w_m3 == 0.0:
                codes.append("MISSING_USAGE")
            if w_plan is None:
                codes.append("MISSING_WATER_PLAN")
            elif w_plan not in wplans:
                codes.append("INVALID_WATER_PLAN")
            elif w_days > 0:
                base, rate = wplans[w_plan]
                w_rev = _money(base * (w_days / days_in_month) + w_m3 * rate)

        # --- rental ---
        r_rev, r_days = Decimal("0.00"), 0
        r_dev = r_plan = None
        if rental:
            if len(rental) > 1:
                codes.append("MULTIPLE_RENTAL_DEVICES")
            d = rental[0]
            r_dev, r_plan = d["device_id"], d["plan_id"]
            r_days = active_days(d["activation_date"], d["deactivation_date"], m_start, m_end)
            if r_plan is None:
                codes.append("MISSING_RENTAL_PLAN")
            elif r_plan not in rplans:
                codes.append("INVALID_RENTAL_PLAN")
            elif r_days > 0:
                r_rev = _money(rplans[r_plan] * (r_days / days_in_month))

        if w_days == 0 and r_days == 0:
            codes.append("ZERO_ACTIVE_DAYS")

        flag = "EXCEPTION" if codes else "PASS"
        if codes:
            exceptions += 1

        out.append(MonthlyRevenue(
            billing_month=billing_month, apartment_id=apt_id,
            location_code=info["location"], water_device_id=w_dev,
            rental_device_id=r_dev, water_plan_id=w_plan, rental_plan_id=r_plan,
            water_active_days=w_days, rental_active_days=r_days,
            water_usage_m3=round(w_m3, 3), water_revenue=w_rev,
            rental_revenue=r_rev, total_revenue=w_rev + r_rev,
            validation_flag=flag, exception_code=",".join(codes) or None))

    db.bulk_save_objects(out)
    db.commit()

    total = sum(float(r.total_revenue) for r in out)
    return {"billing_month": billing_month, "apartments": len(out),
            "exceptions": exceptions, "total_revenue": round(total, 2)}


MONTHS = ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09"]


def calculate_all_months(db: Optional[Session] = None, months: Optional[list] = None, verbose: bool = False) -> list:
    """Calculates deterministic revenue across all configured billing months."""
    from app.db.base import SessionLocal

    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        target_months = months or MONTHS
        results = []
        for m in target_months:
            res = compute_month(db, m)
            results.append(res)
            if verbose:
                print(f"Computed {m}: {res}")
        return results
    finally:
        if close_db:
            db.close()

