# Database

## Schema decisions

**Natural keys as primary keys.** `apartment_id`, `device_id`, `usage_id` are already anonymised surrogates in the source data. Adding an integer surrogate would buy nothing and cost a join hop on every query.

**`Numeric(14,2)` for money.** Float accumulation drifts across 500 apartments × 6 months. Revenue components are quantized half-up at computation time, not at aggregation.

**`billing_month` as `String(7)`.** `'2026-09'` sorts lexicographically in the same order it sorts chronologically, which makes every window function in `queries.py` simpler and index-friendly.

**Unique constraint on `(billing_month, apartment_id)`.** One revenue row per apartment-month, enforced by the database rather than by convention. Recalculation deletes and reinserts the month.

## Tables

### Phase 1
| Table | Rows (loaded) | Purpose |
|---|---|---|
| `buildings` | 10 | Location grouping |
| `apartments` | 500 | Billing entity |
| `devices` | 1,000 | Water meters + rental units |
| `water_usage` | 91,501 | Daily consumption |
| `water_plans` / `rental_plans` | 3 / 3 | Pricing |
| `plan_assignments` | 1,000 | Device → plan mapping |
| `monthly_revenue` | 3,000 | Computed output |
| `ingestion_runs` | per run | Run audit |
| `validation_results` | per check | Data quality history |
| `anomalies` / `alerts` | 8 / 2 | Detection output |

### Phase 2
`users`, `workflows`, `approvals`, `action_records`, `audit_logs`, `evaluation_results`.

## Indexes — chosen, not sprinkled

| Index | Justification |
|---|---|
| `ix_usage_device_date` (composite) | The revenue engine's single hottest query sums usage per device within a date range. |
| `billing_month` on `monthly_revenue` | Every analytics query filters or groups by it. |
| `location_code` on `apartments`, `monthly_revenue` | The alerting entity grain. |
| `idempotency_key` unique on `action_records` | Duplicate prevention enforced by the DB, not by application logic. |
| `severity`, `status` on `alerts` | Dashboard filters. |

Deliberately **not** indexed: `apartment_type`, `device_type`, `plan_name` — low cardinality, never filtered in hot paths.

## SQLite vs PostgreSQL

Default is SQLite so the project runs with zero setup. Postgres via `DATABASE_URL`. One portability note: `GROUP_CONCAT` in `multiple_active_plans` is SQLite syntax; Postgres needs `STRING_AGG(plan_id, ',')`.
