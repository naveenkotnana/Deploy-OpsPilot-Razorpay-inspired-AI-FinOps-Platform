# Limitations

Stated plainly. Nothing here is hidden in a footnote.

## Not measured

**LLM generation quality.** Ollama was not available in the environment where this project was built. The fallback path was exercised; the generation path was not. Every LLM failure mode is tested (unavailable, timeout, malformed JSON) and the system degrades cleanly, but narrative quality, groundedness of real model output, and end-to-end latency with a model loaded are **not** measured. Run `scripts/run_agent_eval.py` locally with Ollama running.

**Anomaly precision/recall.** The dataset contains one intentional duplicate usage row and six April exceptions, correctly surfaced. That is too small a ground truth to report precision or recall from, so neither is claimed. A proper injected-anomaly benchmark is future work.

## Design trade-offs

**TF-IDF is lexical.** Recall@4 = 1.000 on this corpus, partly because the evaluation questions share vocabulary with the documents. Real user phrasing diverges more. `EMBEDDING_MODE=ollama` enables dense local embeddings.

**Fixed investigation plan.** The planner runs the same three queries for every alert. Correct for this alert taxonomy, but it does not adapt to alert type.

**Location-month grain only.** Anomaly detection does not operate at apartment or device grain. Apartment-level outliers are surfaced by SQL (`revenue_outliers`) but do not generate alerts.

## Incomplete

**Alembic.** Listed in requirements; schema is created via `create_all`. No migration history is authored.

**Customer config not wired to runtime.** The loader and accessors are implemented and tested, but `app/ml/anomaly.py` still reads module constants rather than per-customer thresholds.

**`SQL_TIMEOUT_S` not driver-enforced** for SQLite. Row limits are enforced.

**Observability.** Structured JSON logs with `trace_id`/`workflow_id`, and a `/metrics` endpoint. No Prometheus exporter, no distributed tracing backend.

## Security gaps

No rate limiting, no refresh-token rotation, no secrets manager, permissive CORS. Appropriate for a local synthetic project; all would need addressing before real deployment.

## Scope

Synthetic data only. Mock actions write to the local database and contact no external system. No production usage and no real customers are claimed anywhere.
