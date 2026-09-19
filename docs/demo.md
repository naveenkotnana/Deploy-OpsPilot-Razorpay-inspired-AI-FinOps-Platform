# 5-Minute Demo

Prerequisite: `python scripts/setup_all.py`, then API and dashboard running. Ollama optional — minute 3 shows the degraded path honestly if it is absent.

## Minute 1 — Revenue dashboard
**Overview** page. Six months of revenue, ~₹1.06M in the latest month, 500 apartments billed. The line chart shows total against the rolling 3-month average. Note the April dip (925K) — that is real, and the next minute explains it.

## Minute 2 — Anomaly and alert
**Alerts** page. Two MEDIUM alerts, both 2026-05 revenue movement: HYD-NORTH +16.1%, HYD-SOUTH +19.5%. Show the **Anomalies** table below — 8 anomalies, only 2 crossed the MEDIUM floor into alerts.

Say out loud: severity came from a deterministic threshold, not from a model. The Isolation Forest contributed only the score.

## Minute 3 — AI investigation
**AI Investigation** page. Pick an alert, click Run. The workflow executes ten nodes: three SQL queries, RAG retrieval, trusted analytics, evidence validation, then Ollama.

Show the evidence verdict: `EVIDENCE_SUFFICIENT`, three streams present.

If Ollama is not running, show the degraded banner — evidence collected YES, automated recommendation NO, manual investigation required YES. That is the honest behaviour, not a failure.

## Minute 4 — Evidence, citations, recommendation
Same page. Walk the output: what happened (FACT), evidence, inference labelled as inference, uncertainty stated explicitly, and citations like `[DOC-005 v2.0 §7]` pointing at the actual policy section.

Then **Approval** page: the workflow sits at PENDING. Point out you are signed in as manager — signing in as analyst and trying to approve returns 403 from the server, not a hidden button.

## Minute 5 — Approve, audit, evaluation
Approve with a reason. One action record is created. Click Approve again — still one record, `DUPLICATE_SKIPPED`. That is the idempotency key working.

**Audit** page: every node, tool, status, latency, input hash, and the approval decision.

**Evaluation** page: RAG 22/22, agent/security 35/35. Say clearly — these numbers came from running the scripts, not from a slide.

## Closing line
"Synthetic data, local inference, no paid APIs. The LLM writes prose and nothing else — it cannot write SQL, cannot do arithmetic, cannot set severity, and cannot execute an action without a human."
