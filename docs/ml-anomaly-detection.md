# ML Anomaly Detection

## Hybrid by design

Isolation Forest **proposes**. Deterministic rules **decide severity**. Severity drives escalation policy, so it must be reproducible — a model score is not.

## Features (location-month grain, 10 features)

`revenue`, `usage_m3`, `apartments`, `exceptions`, `revenue_change_pct`, `usage_change_pct`, `rev_per_apartment`, `exception_rate`, `active_water`, `active_rental`.

Location-month grain chosen because an operational root cause — a site outage, a bad install batch, a plan migration — is almost always site-scoped.

## Model

`IsolationForest(n_estimators=200, contamination=0.08, random_state=42)`. Fixed seed for reproducibility. `anomaly_score = -score_samples(X)`, higher = more anomalous.

## Severity ladder (deterministic)

Revenue/usage movement, on **absolute** value — a sharp increase escalates the same as a drop, because both indicate the same class of billing error:

| |Δ%| | Severity |
|---|---|
| ≥ 40 | CRITICAL |
| ≥ 25 | HIGH |
| ≥ 15 | MEDIUM |
| ≥ 8 | LOW |

Exception count: ≥20 CRITICAL, ≥10 HIGH, ≥5 MEDIUM, ≥1 LOW.

**ML-only detections are capped at LOW.** If no rule breached, an unsupervised score is a prompt to investigate, not grounds to escalate. This is the single most important line in the module.

## Alerting

Anomalies at MEDIUM or above create an `alerts` row. Below MEDIUM they are recorded as anomalies only.

## Measured results

30 location-months scored → **8 anomalies**, **2 alerts** (both MEDIUM, both revenue movement: HYD-NORTH +16.1%, HYD-SOUTH +19.5% in 2026-05).

## What is not claimed

Precision and recall against a broad injected-anomaly ground truth are **not** measured. The dataset contains one intentional duplicate usage row and six April exceptions, which the pipeline surfaces correctly, but that is too small a set to report meaningful precision/recall from. Building that benchmark is listed in future work. No fabricated metric appears anywhere.
