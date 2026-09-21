import pandas as pd
import pytest
from app.db.base import SessionLocal
from app.services.ingestion import infer_dataset_name, ingest_dataframe, TABLE_ORDER
from app.services.revenue import calculate_all_months
from app.services.anomaly import detect_all_anomalies
from app.rag.retriever import get_retriever


def test_infer_dataset_name():
    assert infer_dataset_name("building_master.csv", ["building_id", "location_code"]) == "building_master"
    assert infer_dataset_name("my_apartments.csv", ["apartment_id", "building_id"]) == "apartment_master"
    assert infer_dataset_name("devices_batch.csv", ["device_id", "service_type"]) == "device_service_master"
    assert infer_dataset_name("water_usage_data.csv", ["usage_id", "consumption_m3"]) == "water_usage_data"
    assert infer_dataset_name("random_name.csv", ["rental_plan_id", "monthly_rental"]) == "rental_plan_data"


def test_ingest_dataframe_and_revenue_recalc():
    db = SessionLocal()
    try:
        # Test ingesting a valid building record
        df_b = pd.DataFrame([
            {"building_id": "BLD-TEST-99", "location_code": "HYD-TEST", "building_type": "RESIDENTIAL", "status": "ACTIVE"}
        ])
        res = ingest_dataframe(db, "building_master", df_b)
        assert res["status"] in ("PASS", "WARN")
        assert res["loaded"] == 1

        # Test calculating all months
        rev_res = calculate_all_months(db=db)
        assert len(rev_res) >= 1
    finally:
        try:
            from sqlalchemy import text
            db.execute(text("DELETE FROM buildings WHERE building_id = 'BLD-TEST-99'"))
            db.commit()
        except Exception:
            pass
        db.close()


def test_anomaly_and_retriever_wrappers():
    # Verify wrappers execute without error
    retriever = get_retriever()
    assert retriever is not None

    anomalies = detect_all_anomalies()
    assert isinstance(anomalies, (dict, str, list))
