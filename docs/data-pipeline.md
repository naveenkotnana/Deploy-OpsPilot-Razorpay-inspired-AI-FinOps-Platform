# Data Pipeline

## Principle

**Bad data is flagged, never silently repaired.** An imputed number that looks right is more dangerous than a visible gap.

## Run lifecycle

Every source produces an `ingestion_runs` row: `run_id`, `source`, `start_time`, `end_time`, `records_received`, `records_loaded`, `records_rejected`, `validation_status`, `error_summary`.

Status semantics:
- **PASS** — all checks passed, data loaded.
- **WARN** — non-critical check failed; data loaded, item raised.
- **FAIL** — critical check failed; **loading blocked**, `records_rejected = records_received`.

## Checks implemented

`SCHEMA_MATCH`, `NULL_RATE`, `DUPLICATE_RATE`, `ROW_COUNT`, `VALUE_RANGE`, `DATE_VALIDITY`, `REFERENTIAL_INTEGRITY`, `FRESHNESS`, plus business checks `MISSING_INSTALLATION_DATE`, `MULTIPLE_ACTIVE_PLANS`, `MISSING_USAGE`, `INVALID_PLAN`.

## Measured results

```
[PASS] building_master          received=    10  loaded=    10  rejected=0
[PASS] apartment_master         received=   500  loaded=   500  rejected=0
[PASS] device_service_master    received=  1000  loaded=  1000  rejected=0
[PASS] rental_plan_data         received=     3  loaded=     3  rejected=0
[PASS] water_plan_data          received=     3  loaded=     3  rejected=0
[PASS] device_plan_assignments  received=  1000  loaded=  1000  rejected=0
[PASS] water_usage_data         received= 91501  loaded= 91501  rejected=0
```

42 validation check results recorded. Full bootstrap: **~20 seconds**.

## Revenue rules

```
water_revenue  = base_fee × (water_active_days / days_in_month)
                 + consumption_m3 × rate_per_m3
rental_revenue = monthly_rental × (rental_active_days / days_in_month)
total_revenue  = water_revenue + rental_revenue
```

Active days are the **inclusive** overlap of the device window and the billing month — a device activated on the 15th of a 30-day month has 16 active days, not 15. This is tested explicitly (`test_mid_month_activation_is_inclusive`).

## Missing-input policy

No guessing. Each condition writes `validation_flag='EXCEPTION'` with a code:

`MISSING_WATER_DEVICE` · `MULTIPLE_WATER_DEVICES` · `MISSING_WATER_PLAN` · `INVALID_WATER_PLAN` · `MISSING_USAGE` · `MISSING_RENTAL_PLAN` · `INVALID_RENTAL_PLAN` · `MULTIPLE_RENTAL_DEVICES` · `ZERO_ACTIVE_DAYS`

## Measured revenue output

| Month | Apartments | Total revenue | Exceptions |
|---|---|---|---|
| 2026-04 | 500 | 925,124.11 | 6 |
| 2026-05 | 500 | 1,062,251.37 | 0 |
| 2026-06 | 500 | 1,057,915.77 | 0 |
| 2026-07 | 500 | 1,069,312.45 | 0 |
| 2026-08 | 500 | 1,069,652.51 | 0 |
| 2026-09 | 500 | 1,057,857.54 | 0 |

April's six exceptions are `MISSING_USAGE` on devices activated late in the month — a real gap in the source data, correctly surfaced rather than filled in.

## Idempotency

`setup_all.py` is safe to re-run. Master tables use `merge` (upsert); `water_usage` is a full-refresh source cleared before insert; `monthly_revenue` deletes the month before recomputing.
