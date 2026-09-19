"""End-to-end data pipeline integration."""
from sqlalchemy import text
from app.services.revenue import compute_month
from app.ml.anomaly import detect
from app.rag.store import get_store


def test_data_is_loaded(db):
    assert db.execute(text("SELECT COUNT(*) FROM apartments")).scalar() == 500
    assert db.execute(text("SELECT COUNT(*) FROM devices")).scalar() == 1000
    assert db.execute(text("SELECT COUNT(*) FROM water_usage")).scalar() > 90000


def test_ingestion_runs_recorded(db):
    n = db.execute(text("SELECT COUNT(*) FROM ingestion_runs")).scalar()
    assert n >= 7


def test_validation_results_recorded(db):
    n = db.execute(text("SELECT COUNT(*) FROM validation_results")).scalar()
    assert n > 0


def test_revenue_computation_is_reproducible(db):
    a = compute_month(db, "2026-09")
    b = compute_month(db, "2026-09")
    assert a["total_revenue"] == b["total_revenue"]
    assert a["apartments"] == 500


def test_revenue_components_sum_to_total(db):
    row = db.execute(text(
        "SELECT SUM(water_revenue), SUM(rental_revenue), SUM(total_revenue) "
        "FROM monthly_revenue WHERE billing_month='2026-09'")).first()
    assert abs((float(row[0]) + float(row[1])) - float(row[2])) < 0.5


def test_exceptions_are_flagged_not_repaired(db):
    rows = db.execute(text(
        "SELECT exception_code FROM monthly_revenue "
        "WHERE validation_flag='EXCEPTION' LIMIT 5")).all()
    for r in rows:
        assert r[0]   # every exception row carries a code


def test_all_analytics_queries_execute(db):
    from app.analytics.queries import QUERIES
    for name, q in QUERIES.items():
        db.execute(text(q)).fetchall()


def test_anomaly_detection_produces_severities(db):
    detect(db)
    sevs = {r[0] for r in db.execute(text("SELECT DISTINCT severity FROM anomalies")).all()}
    assert sevs <= {"INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"}


def test_alerts_only_medium_and_above(db):
    detect(db)
    sevs = {r[0] for r in db.execute(text("SELECT DISTINCT severity FROM alerts")).all()}
    assert sevs <= {"MEDIUM", "HIGH", "CRITICAL"}


def test_rag_store_builds(db):
    s = get_store().stats()
    assert s["documents"] == 5 and s["chunks"] > 20


def test_rag_returns_citations(db):
    hits = get_store().search("how is rental revenue prorated", k=3)
    assert hits and all(h["citation"].startswith("[DOC-") for h in hits)
