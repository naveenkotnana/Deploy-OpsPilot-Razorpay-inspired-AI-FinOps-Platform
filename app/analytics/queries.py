"""Reusable SQL analytics. Each query documents WHY it exists.

These are also the only statements the agent's SQL tool may run — it selects
by name, never by writing SQL. See app/agent/tools/sql_tool.py.
"""

QUERIES = {

# Q1 - headline trend. Drives the Overview KPI and the MoM anomaly features.
"revenue_by_month": """
WITH monthly AS (
    SELECT billing_month,
           SUM(total_revenue)  AS total_revenue,
           SUM(water_revenue)  AS water_revenue,
           SUM(rental_revenue) AS rental_revenue,
           COUNT(*)            AS apartments
    FROM monthly_revenue GROUP BY billing_month
)
SELECT billing_month, total_revenue, water_revenue, rental_revenue, apartments,
       LAG(total_revenue) OVER (ORDER BY billing_month) AS prev_revenue,
       ROUND(100.0 * (total_revenue - LAG(total_revenue) OVER (ORDER BY billing_month))
             / NULLIF(LAG(total_revenue) OVER (ORDER BY billing_month), 0), 2) AS mom_pct,
       ROUND(AVG(total_revenue) OVER (ORDER BY billing_month
             ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS rolling_3m_avg
FROM monthly ORDER BY billing_month
""",

# Q2 - plan mix. A sudden shift in plan share is a leading indicator of
# mis-assignment, so this feeds the anomaly feature set as well as the UI.
"revenue_by_plan": """
SELECT billing_month, 'WATER' AS service, water_plan_id AS plan_id,
       COUNT(*) AS devices, SUM(water_revenue) AS revenue,
       RANK() OVER (PARTITION BY billing_month ORDER BY SUM(water_revenue) DESC) AS rnk
FROM monthly_revenue WHERE water_plan_id IS NOT NULL
GROUP BY billing_month, water_plan_id
UNION ALL
SELECT billing_month, 'RENTAL', rental_plan_id,
       COUNT(*), SUM(rental_revenue),
       RANK() OVER (PARTITION BY billing_month ORDER BY SUM(rental_revenue) DESC)
FROM monthly_revenue WHERE rental_plan_id IS NOT NULL
GROUP BY billing_month, rental_plan_id
ORDER BY billing_month, service, revenue DESC
""",

# Q3 - location P&L with MoM delta. The primary entity for alerting, because
# an operational cause (a site outage, a bad install batch) is location-scoped.
"revenue_by_location": """
WITH loc AS (
    SELECT billing_month, location_code,
           SUM(total_revenue) AS revenue, COUNT(*) AS apartments,
           SUM(CASE WHEN validation_flag='EXCEPTION' THEN 1 ELSE 0 END) AS exceptions
    FROM monthly_revenue GROUP BY billing_month, location_code
)
SELECT billing_month, location_code, revenue, apartments, exceptions,
       LAG(revenue) OVER (PARTITION BY location_code ORDER BY billing_month) AS prev_revenue,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (PARTITION BY location_code ORDER BY billing_month))
             / NULLIF(LAG(revenue) OVER (PARTITION BY location_code ORDER BY billing_month),0), 2) AS mom_pct,
       ROUND(AVG(revenue) OVER (PARTITION BY location_code ORDER BY billing_month
             ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS rolling_3m_avg
FROM loc ORDER BY billing_month, revenue DESC
""",

# Q4 - active device counts split by service; denominator for per-device revenue.
"active_devices": """
SELECT d.service_type, d.device_status, a.location_code, COUNT(*) AS devices
FROM devices d JOIN apartments a ON a.apartment_id = d.apartment_id
GROUP BY d.service_type, d.device_status, a.location_code
ORDER BY d.service_type, devices DESC
""",

# Q5 - every flagged row, for the Data Quality page and the exception queue.
"missing_data": """
SELECT billing_month, apartment_id, location_code, exception_code,
       water_active_days, rental_active_days, total_revenue
FROM monthly_revenue WHERE validation_flag = 'EXCEPTION'
ORDER BY billing_month DESC, apartment_id
""",

# Q6 - duplicate usage readings. Same device + same day twice inflates water
# revenue directly, so this is checked independently of ingestion.
"duplicate_usage": """
SELECT device_id, usage_date, COUNT(*) AS readings, SUM(consumption_m3) AS total_m3
FROM water_usage GROUP BY device_id, usage_date
HAVING COUNT(*) > 1 ORDER BY readings DESC
""",

# Q7 - an apartment billed on two ACTIVE plans for one service is a
# double-billing risk; deterministic, so it is a RULE anomaly not an ML one.
# NOTE: plan list uses a correlated subquery instead of GROUP_CONCAT / STRING_AGG
# so the query runs identically on SQLite and PostgreSQL.
"multiple_active_plans": """
SELECT a.apartment_id, a.service_type, a.active_plans,
       (SELECT p2.plan_id FROM plan_assignments p2
        WHERE p2.apartment_id = a.apartment_id
          AND p2.service_type = a.service_type
          AND p2.assignment_status = 'ACTIVE'
        ORDER BY p2.plan_id
        LIMIT 1) AS first_plan
FROM (
    SELECT apartment_id, service_type, COUNT(*) AS active_plans
    FROM plan_assignments
    WHERE assignment_status = 'ACTIVE'
    GROUP BY apartment_id, service_type
    HAVING COUNT(*) > 1
) a
ORDER BY a.apartment_id
""",

# Q8 - outlier apartments vs their own location mean. Gives the investigator
# concrete comparable rows rather than a single aggregate number.
"revenue_outliers": """
WITH stats AS (
    SELECT billing_month, location_code, AVG(total_revenue) AS avg_rev
    FROM monthly_revenue GROUP BY billing_month, location_code
)
SELECT m.billing_month, m.apartment_id, m.location_code, m.total_revenue,
       ROUND(s.avg_rev,2) AS location_avg,
       ROUND(m.total_revenue - s.avg_rev, 2) AS delta
FROM monthly_revenue m JOIN stats s
  ON s.billing_month=m.billing_month AND s.location_code=m.location_code
WHERE ABS(m.total_revenue - s.avg_rev) > 0.5 * s.avg_rev
ORDER BY ABS(m.total_revenue - s.avg_rev) DESC
""",

# Q9 - month-over-month movers at apartment grain; used as SQL evidence when
# an alert fires on a location.
"mom_change_by_apartment": """
WITH r AS (
    SELECT apartment_id, location_code, billing_month, total_revenue,
           LAG(total_revenue) OVER (PARTITION BY apartment_id ORDER BY billing_month) AS prev
    FROM monthly_revenue
)
SELECT apartment_id, location_code, billing_month, total_revenue, prev,
       ROUND(total_revenue - prev, 2) AS delta,
       ROUND(100.0*(total_revenue-prev)/NULLIF(prev,0), 2) AS pct_change
FROM r WHERE prev IS NOT NULL
ORDER BY ABS(total_revenue - prev) DESC
""",

# Q10 - device-level revenue ranking within location, for drill-down.
"device_revenue": """
SELECT billing_month, location_code, apartment_id, water_device_id, rental_device_id,
       water_revenue, rental_revenue, total_revenue,
       ROW_NUMBER() OVER (PARTITION BY billing_month, location_code
                          ORDER BY total_revenue DESC) AS rank_in_location
FROM monthly_revenue ORDER BY billing_month DESC, location_code, rank_in_location
""",

# Q11 - data quality run history for the dashboard.
"validation_summary": """
SELECT source, check_name, status, observed, threshold, detail
FROM validation_results ORDER BY
  CASE status WHEN 'FAIL' THEN 0 WHEN 'WARN' THEN 1 ELSE 2 END, source
""",
}


def get_query(name: str) -> str:
    if name not in QUERIES:
        raise KeyError(f"Unknown query '{name}'. Allowed: {sorted(QUERIES)}")
    return QUERIES[name]
