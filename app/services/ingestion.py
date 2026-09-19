"""CSV -> Postgres/SQLite ingestion with per-run validation and audit trail."""
import uuid, datetime as dt
from typing import List
import pandas as pd
from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import SessionLocal, init_db
from app.models import (Building, Apartment, Device, WaterUsage, RentalPlan,
                        WaterPlan, PlanAssignment, IngestionRun, ValidationResult)
from app.services import validation as V


def _d(v):
    """Parse a date cell; blank/NaT -> None (never invented)."""
    if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() in ("", "nan", "NaT"):
        return None
    ts = pd.to_datetime(v, errors="coerce")
    return None if pd.isna(ts) else ts.date()


def _read(name: str) -> pd.DataFrame:
    return pd.read_csv(settings.RAW_DIR / name)


def _record(db: Session, run_id, source, checks: List[V.CheckResult]):
    for c in checks:
        db.add(ValidationResult(run_id=run_id, source=source, check_name=c.check_name,
                                status=c.status, observed=c.observed,
                                threshold=c.threshold, detail=c.detail))


def _run(db: Session, source, df, checks, loader):
    run_id = f"ING-{dt.datetime.now(dt.timezone.utc).replace(tzinfo=None):%Y%m%d%H%M%S}-{uuid.uuid4().hex[:6]}"
    start = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    status = V.rollup(checks)
    loaded, rejected = 0, 0
    errors = [f"{c.check_name}:{c.observed}" for c in checks if c.status != "PASS"]

    if status != "FAIL":
        loaded, rejected = loader(db, df)
    else:
        rejected = len(df)

    db.add(IngestionRun(run_id=run_id, source=source, start_time=start,
                        end_time=dt.datetime.now(dt.timezone.utc).replace(tzinfo=None), records_received=len(df),
                        records_loaded=loaded, records_rejected=rejected,
                        validation_status=status,
                        error_summary="; ".join(errors) or None))
    _record(db, run_id, source, checks)
    db.commit()
    return {"run_id": run_id, "source": source, "received": len(df),
            "loaded": loaded, "rejected": rejected, "status": status}


def _bulk(db, objs):
    for o in objs:
        db.merge(o)
    return len(objs), 0


def ingest_all(verbose=True):
    init_db()
    db = SessionLocal()
    summaries = []
    try:
        # ---------- buildings ----------
        df = _read("building_master.csv")
        checks = [V.schema_match(df, ["building_id", "location_code"]),
                  V.null_rate(df, ["building_id", "location_code"]),
                  V.duplicate_rate(df, ["building_id"]),
                  V.row_count(df)]
        summaries.append(_run(db, "building_master", df, checks, lambda d, x: _bulk(d, [
            Building(building_id=r.building_id, location_code=r.location_code,
                     building_type=r.building_type, status=r.status)
            for r in x.itertuples()])))

        # ---------- apartments ----------
        df = _read("apartment_master.csv")
        bkeys = set(_read("building_master.csv")["building_id"])
        checks = [V.schema_match(df, ["apartment_id", "building_id", "location_code"]),
                  V.null_rate(df, ["apartment_id", "location_code"]),
                  V.duplicate_rate(df, ["apartment_id"]),
                  V.date_validity(df, ["activation_date"]),
                  V.referential_integrity(df, "building_id", bkeys, "apartment->building"),
                  V.row_count(df)]
        summaries.append(_run(db, "apartment_master", df, checks, lambda d, x: _bulk(d, [
            Apartment(apartment_id=r.apartment_id, building_id=r.building_id,
                      location_code=r.location_code, apartment_type=r.apartment_type,
                      activation_date=_d(r.activation_date), status=r.status)
            for r in x.itertuples()])))

        # ---------- devices ----------
        df = _read("device_service_master.csv")
        akeys = set(_read("apartment_master.csv")["apartment_id"])
        checks = [V.schema_match(df, ["device_id", "apartment_id", "service_type"]),
                  V.null_rate(df, ["device_id", "apartment_id"]),
                  V.duplicate_rate(df, ["device_id"]),
                  V.date_validity(df, ["installation_date", "activation_date", "deactivation_date"]),
                  V.referential_integrity(df, "apartment_id", akeys, "device->apartment"),
                  V.row_count(df)]
        # MISSING_INSTALLATION_DATE business check
        miss = int(df["installation_date"].isna().sum())
        checks.append(V.CheckResult("MISSING_INSTALLATION_DATE",
                                    "PASS" if miss == 0 else "WARN", str(miss), "0"))
        summaries.append(_run(db, "device_service_master", df, checks, lambda d, x: _bulk(d, [
            Device(device_id=r.device_id, apartment_id=r.apartment_id,
                   service_type=r.service_type, device_type=r.device_type,
                   installation_date=_d(r.installation_date),
                   activation_date=_d(r.activation_date),
                   deactivation_date=_d(r.deactivation_date),
                   device_status=r.device_status) for r in x.itertuples()])))

        # ---------- plans ----------
        df = _read("rental_plan_data.csv")
        checks = [V.schema_match(df, ["rental_plan_id", "monthly_rental"]),
                  V.null_rate(df, ["rental_plan_id", "monthly_rental"]),
                  V.duplicate_rate(df, ["rental_plan_id"]),
                  V.value_range(df, "monthly_rental", lo=0),
                  V.row_count(df)]
        summaries.append(_run(db, "rental_plan_data", df, checks, lambda d, x: _bulk(d, [
            RentalPlan(rental_plan_id=r.rental_plan_id, plan_name=r.plan_name,
                       monthly_rental=r.monthly_rental,
                       effective_from=_d(r.effective_from), effective_to=_d(r.effective_to))
            for r in x.itertuples()])))

        df = _read("water_plan_data.csv")
        checks = [V.schema_match(df, ["water_plan_id", "base_fee", "rate_per_m3"]),
                  V.null_rate(df, ["water_plan_id", "base_fee", "rate_per_m3"]),
                  V.duplicate_rate(df, ["water_plan_id"]),
                  V.value_range(df, "rate_per_m3", lo=0),
                  V.row_count(df)]
        summaries.append(_run(db, "water_plan_data", df, checks, lambda d, x: _bulk(d, [
            WaterPlan(water_plan_id=r.water_plan_id, plan_name=r.plan_name,
                      base_fee=r.base_fee, rate_per_m3=r.rate_per_m3,
                      effective_from=_d(r.effective_from), effective_to=_d(r.effective_to))
            for r in x.itertuples()])))

        # ---------- plan assignments ----------
        df = _read("device_plan_assignments.csv")
        valid_plans = set(_read("water_plan_data.csv")["water_plan_id"]) | \
                      set(_read("rental_plan_data.csv")["rental_plan_id"])
        checks = [V.schema_match(df, ["assignment_id", "apartment_id", "plan_id"]),
                  V.null_rate(df, ["assignment_id", "plan_id"]),
                  V.duplicate_rate(df, ["assignment_id"]),
                  V.referential_integrity(df, "apartment_id", akeys, "assignment->apartment"),
                  V.row_count(df)]
        invalid = int((~df["plan_id"].isin(valid_plans)).sum())
        checks.append(V.CheckResult("INVALID_PLAN", "PASS" if invalid == 0 else "FAIL",
                                    str(invalid), "0", "plan_id not in plan master"))
        act = df[df["assignment_status"] == "ACTIVE"]
        multi = int(act.duplicated(subset=["apartment_id", "service_type"]).sum())
        checks.append(V.CheckResult("MULTIPLE_ACTIVE_PLANS", "PASS" if multi == 0 else "WARN",
                                    str(multi), "0", "apartment+service with >1 ACTIVE plan"))
        summaries.append(_run(db, "device_plan_assignments", df, checks, lambda d, x: _bulk(d, [
            PlanAssignment(assignment_id=r.assignment_id, apartment_id=r.apartment_id,
                           service_type=r.service_type, device_id=r.device_id,
                           plan_id=r.plan_id, effective_from=_d(r.effective_from),
                           effective_to=_d(r.effective_to),
                           assignment_status=r.assignment_status) for r in x.itertuples()])))

        # ---------- water usage (bulk, chunked) ----------
        df = _read("water_usage_data.csv")
        dkeys = set(_read("device_service_master.csv")["device_id"])
        checks = [V.schema_match(df, ["usage_id", "device_id", "usage_date", "consumption_m3"]),
                  V.null_rate(df, ["usage_id", "device_id", "usage_date"]),
                  V.duplicate_rate(df, ["usage_id"]),
                  V.value_range(df, "consumption_m3", lo=0, hi=100),
                  V.date_validity(df, ["usage_date"]),
                  V.referential_integrity(df, "device_id", dkeys, "usage->device"),
                  V.freshness(df, "usage_date", settings.BILLING_MONTH),
                  V.row_count(df, 1000)]

        def load_usage(d, x):
            # Idempotent reload: usage is a full-refresh source, so the table is
            # cleared before insert. Re-running setup must not fail on PK collision.
            received = len(x)
            x = x.drop_duplicates(subset=["usage_id"])
            d.execute(sa_text("DELETE FROM water_usage"))
            rows = x.to_dict("records")
            for rec in rows:
                rec["usage_date"] = _d(rec["usage_date"])
            d.bulk_insert_mappings(WaterUsage, rows)
            return len(rows), received - len(rows)

        summaries.append(_run(db, "water_usage_data", df, checks, load_usage))

        if verbose:
            for s in summaries:
                print(f"[{s['status']:4}] {s['source']:26} received={s['received']:6} "
                      f"loaded={s['loaded']:6} rejected={s['rejected']}")
        return summaries
    finally:
        db.close()


if __name__ == "__main__":
    ingest_all()
