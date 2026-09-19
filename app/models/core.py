"""Phase 1 domain tables.

Schema decisions (see docs/database.md):
- Natural business keys (apartment_id, device_id) are the PKs. They are already
  anonymised surrogate IDs in the source data, so adding an integer surrogate
  would only add a join hop.
- Indexes are placed on the columns the analytics layer actually filters and
  groups by: billing_month, location_code, usage_date, device_id.
- Monetary values use Numeric(14,2) to avoid float drift in revenue sums.
"""
from sqlalchemy import (Column, String, Date, Integer, Numeric, DateTime, Text,
                        ForeignKey, Index, UniqueConstraint, func)
from app.db.base import Base


class Building(Base):
    __tablename__ = "buildings"
    building_id = Column(String(20), primary_key=True)
    location_code = Column(String(30), index=True, nullable=False)
    building_type = Column(String(50))
    status = Column(String(20))


class Apartment(Base):
    __tablename__ = "apartments"
    apartment_id = Column(String(20), primary_key=True)
    building_id = Column(String(20), ForeignKey("buildings.building_id"), index=True)
    location_code = Column(String(30), index=True, nullable=False)
    apartment_type = Column(String(20))
    activation_date = Column(Date)
    status = Column(String(20), index=True)


class Device(Base):
    __tablename__ = "devices"
    device_id = Column(String(30), primary_key=True)
    apartment_id = Column(String(20), ForeignKey("apartments.apartment_id"), index=True)
    service_type = Column(String(20), index=True)   # WATER | RENTAL
    device_type = Column(String(40))
    installation_date = Column(Date)
    activation_date = Column(Date)
    deactivation_date = Column(Date, nullable=True)
    device_status = Column(String(20), index=True)


class WaterUsage(Base):
    __tablename__ = "water_usage"
    usage_id = Column(String(40), primary_key=True)
    device_id = Column(String(30), index=True, nullable=False)
    apartment_id = Column(String(20), index=True, nullable=False)
    usage_date = Column(Date, index=True, nullable=False)
    consumption_m3 = Column(Numeric(10, 3))


Index("ix_usage_device_date", WaterUsage.device_id, WaterUsage.usage_date)


class RentalPlan(Base):
    __tablename__ = "rental_plans"
    rental_plan_id = Column(String(20), primary_key=True)
    plan_name = Column(String(60))
    monthly_rental = Column(Numeric(12, 2), nullable=False)
    effective_from = Column(Date)
    effective_to = Column(Date)


class WaterPlan(Base):
    __tablename__ = "water_plans"
    water_plan_id = Column(String(20), primary_key=True)
    plan_name = Column(String(60))
    base_fee = Column(Numeric(12, 2), nullable=False)
    rate_per_m3 = Column(Numeric(12, 2), nullable=False)
    effective_from = Column(Date)
    effective_to = Column(Date)


class PlanAssignment(Base):
    __tablename__ = "plan_assignments"
    assignment_id = Column(String(30), primary_key=True)
    apartment_id = Column(String(20), index=True)
    service_type = Column(String(20), index=True)
    device_id = Column(String(30), index=True)
    plan_id = Column(String(20), index=True)
    effective_from = Column(Date)
    effective_to = Column(Date)
    assignment_status = Column(String(20), index=True)


class MonthlyRevenue(Base):
    """Output of the revenue engine. Recomputed, never hand-edited."""
    __tablename__ = "monthly_revenue"
    id = Column(Integer, primary_key=True, autoincrement=True)
    billing_month = Column(String(7), index=True, nullable=False)
    apartment_id = Column(String(20), index=True, nullable=False)
    location_code = Column(String(30), index=True)
    water_device_id = Column(String(30))
    rental_device_id = Column(String(30))
    water_plan_id = Column(String(20), index=True)
    rental_plan_id = Column(String(20), index=True)
    water_active_days = Column(Integer)
    rental_active_days = Column(Integer)
    water_usage_m3 = Column(Numeric(12, 3))
    water_revenue = Column(Numeric(14, 2))
    rental_revenue = Column(Numeric(14, 2))
    total_revenue = Column(Numeric(14, 2))
    validation_flag = Column(String(20), index=True)   # PASS | EXCEPTION
    exception_code = Column(String(60), nullable=True)
    __table_args__ = (UniqueConstraint("billing_month", "apartment_id",
                                       name="uq_revenue_month_apartment"),)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    run_id = Column(String(40), primary_key=True)
    source = Column(String(80), index=True)
    start_time = Column(DateTime, server_default=func.now())
    end_time = Column(DateTime, nullable=True)
    records_received = Column(Integer, default=0)
    records_loaded = Column(Integer, default=0)
    records_rejected = Column(Integer, default=0)
    validation_status = Column(String(20))   # PASS | WARN | FAIL
    error_summary = Column(Text, nullable=True)


class ValidationResult(Base):
    __tablename__ = "validation_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(40), index=True)
    source = Column(String(80), index=True)
    check_name = Column(String(50), index=True)
    status = Column(String(10), index=True)   # PASS | WARN | FAIL
    observed = Column(String(120))
    threshold = Column(String(120))
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class Anomaly(Base):
    __tablename__ = "anomalies"
    anomaly_id = Column(String(40), primary_key=True)
    billing_month = Column(String(7), index=True)
    entity_type = Column(String(20))     # LOCATION | APARTMENT | GLOBAL
    entity_id = Column(String(40), index=True)
    metric = Column(String(50))
    method = Column(String(30))          # ISOLATION_FOREST | RULE
    anomaly_score = Column(Numeric(8, 4))
    severity = Column(String(10), index=True)
    reason = Column(Text)
    observed_value = Column(Numeric(16, 2), nullable=True)
    expected_value = Column(Numeric(16, 2), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"
    alert_id = Column(String(40), primary_key=True)
    detected_at = Column(DateTime, server_default=func.now())
    metric = Column(String(50), index=True)
    entity = Column(String(60), index=True)
    billing_month = Column(String(7), index=True)
    severity = Column(String(10), index=True)
    observed_value = Column(Numeric(16, 2), nullable=True)
    expected_value = Column(Numeric(16, 2), nullable=True)
    anomaly_score = Column(Numeric(8, 4), nullable=True)
    evidence_summary = Column(Text)
    status = Column(String(20), index=True, default="OPEN")
