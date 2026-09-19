# SQL Analytics

11 named queries in `app/analytics/queries.py`. This dictionary is also the agent's **SQL allowlist** — the model picks a name, never writes SQL.

## Techniques used

CTEs, `LAG`, `RANK`, `ROW_NUMBER`, partitioned window frames, rolling averages (`ROWS BETWEEN 2 PRECEDING AND CURRENT ROW`), `NULLIF` guards against divide-by-zero, `HAVING`, `UNION ALL`, self-joins against aggregate CTEs.

## Why each query exists

| Query | Rows | Rationale |
|---|---|---|
| `revenue_by_month` | 6 | Headline trend. MoM % and rolling 3-month average feed both the Overview KPI and the anomaly feature set. |
| `revenue_by_plan` | 36 | Plan mix shifts are a leading indicator of mis-assignment. `UNION ALL` across water and rental with per-month ranking. |
| `revenue_by_location` | 30 | Primary alerting entity — operational root causes are site-scoped. Partitioned `LAG` gives per-location MoM. |
| `active_devices` | 10 | Denominator for per-device revenue; splits by service and status. |
| `missing_data` | 6 | Every flagged row, for the exception queue. |
| `duplicate_usage` | 1 | Same device + same day inflates revenue directly. Checked independently of ingestion. |
| `multiple_active_plans` | 0 | Double-billing risk. Deterministic, so it is a RULE anomaly, never an ML one. |
| `revenue_outliers` | 64 | Apartments >50% from their own location mean. Gives an investigator comparable rows, not just an aggregate. |
| `mom_change_by_apartment` | 2,500 | Apartment-grain movers — the SQL evidence when a location alert fires. |
| `device_revenue` | 3,000 | `ROW_NUMBER` ranking within location for drill-down. |
| `validation_summary` | 42 | Data quality history, FAIL-first ordering. |

All 11 execute successfully; verified by `test_all_analytics_queries_execute`.

## Guardrails

Every agent call is wrapped: `SELECT * FROM (<query>) AS q LIMIT :_lim`, default 200 rows. The raw-SQL path (API only) additionally validates SELECT-only, single-statement, allowlisted tables, and injects a `LIMIT` when absent.
