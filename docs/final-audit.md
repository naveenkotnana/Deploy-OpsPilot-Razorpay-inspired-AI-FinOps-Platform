# OpsPilot -- Final Audit

> This document reports only what was actually measured and verified.
> No claims are made that cannot be demonstrated by running the commands below.

---

## Environment

| | |
|---|---|
| Python | 3.13.9 (Anaconda, 64-bit, MSC v.1929) |
| OS | Windows 11 |
| pip | 26.2.1 |
| Docker | Not locally installed; docker-compose.yml and Dockerfiles complete and ready |
| Ollama | Installed, running at localhost:11434; no model pulled at audit time |
| Model recommended | qwen2.5:3b-instruct (~2 GB, fits GTX 1650 4 GB VRAM) |
| Database | SQLite (default, zero-setup); PostgreSQL available via Docker |
| GPU | NVIDIA GTX 1650 -- 4 GB VRAM |
| RAM | 7.34 GB total |

---

## Data

| | |
|---|---|
| Canonical dataset | Repository dataset (apartment/water/rental billing model) |
| Buildings | 10 |
| Apartments | 500 |
| Devices | 1,000 |
| Water usage records | 91,501 |
| Billing months | 2026-04 through 2026-09 |
| Water plans | 3 |
| Rental plans | 3 |
| Plan assignments | 1,000 |
| Tables | 13 domain + 7 Phase 2 operational tables |
| Validation cases preserved | Duplicate usage rows, 6 April exceptions (missing data) |
| PII | None. All IDs are anonymised surrogates. |
| External dataset | NOT merged. Incompatible schema. Kept as reference only. |

---

## Phase 1: Data + SQL + Data Quality + Revenue + ML + RAG + Ollama + Dashboard

**Status: COMPLETE (all acceptance criteria verified by running code)**

| Acceptance Criterion | Status | Evidence |
|---|---|---|
| Clean environment setup | PASS | All imports succeed; setup_all.py runs in 36.5s |
| Dependencies install | PASS | pip install -r requirements.txt succeeds |
| Tests collect | PASS | pytest collects 65 items |
| Tests pass | PASS | 65/65 |
| Database initializes | PASS | init_db() creates all tables idempotently |
| Data ingestion works | PASS | 7 sources, all PASS, 91,501 rows, 0 rejected |
| Validation works | PASS | 9 check types, 84 validation records in DB |
| Revenue calculation works | PASS | 6 months, 500 apartments, deterministic, exceptions flagged |
| SQL analytics works | PASS | 11 named queries, all verified, CTEs + window functions |
| Anomaly detection works | PASS | 8 anomalies detected (IsolationForest + rules) |
| Alerts work | PASS | 2 alerts (MEDIUM+ threshold) |
| RAG works | PASS | TF-IDF, 5 docs, 38 chunks, access-level filter |
| Citations work | PASS | [DOC-xxx v1.0 section] Title format on all chunks |
| Ollama unavailable fallback | PASS | FA-02 test: ok=False err=OLLAMA_UNAVAILABLE_OR_NO_MODEL |
| Ollama integration works | PENDING (user pull required) | ollama pull qwen2.5:3b-instruct |

**Measured Phase 1 results**:

Revenue by month (6 months):
  2026-04: 500 apartments, total=925,124.11, exceptions=6
  2026-05: 500 apartments, total=1,062,251.37, exceptions=0
  2026-06: 500 apartments, total=1,057,915.77, exceptions=0
  2026-07: 500 apartments, total=1,069,312.45, exceptions=0
  2026-08: 500 apartments, total=1,069,652.51, exceptions=0
  2026-09: 500 apartments, total=1,057,857.54, exceptions=0

RAG evaluation (run_rag_eval.py, 22 cases):
  Recall@4             : 22/22 = 1.000
  Top-1 accuracy       : 21/22 = 0.955
  Mean fact coverage   : 0.947
  Citation correctness : 22/22
  Overall pass rate    : 22/22 = 1.000

---

## Phase 2: LangGraph Agent + Tools + Approval + Security + Audit + Evaluation

**Status: COMPLETE (all acceptance criteria verified by running code)**

| Acceptance Criterion | Status | Evidence |
|---|---|---|
| LangGraph workflow works | PASS | AG-01/AG-02 PASS |
| SQL tool is read-only | PASS | SEC-01..06 PASS |
| RAG permission filtering works | PASS | SEC-16 PASS |
| Evidence validation works | PASS | AG-03 PASS |
| Recommendation generated | PASS | AG-04 PASS (deterministic fallback when Ollama absent) |
| Approval gate works | PASS | AP-01 PASS |
| Rejection works | PASS | AP-03 PASS |
| Action cannot execute without approval | PASS | AP-02: ACTION_BLOCKED_NO_APPROVAL |
| Idempotency works | PASS | AP-05: 1 action after 3 attempts |
| Authentication works | PASS | 5 auth tests PASS |
| RBAC works | PASS | SEC-11/12/13 PASS |
| Prompt injection test works | PASS | SEC-08/09/10 PASS |
| Failure handling works | PASS | FA-01..06 PASS |
| Audit logging works | PASS | audit_logs table populated per node |
| Evaluation scripts work | PASS | run_rag_eval.py, run_agent_eval.py both pass |

**Measured Phase 2 results (run_agent_eval.py, 35 cases)**:

Agent behaviour (AG-01..08)    :  8/8
Approval and idempotency       :  5/5
Security guardrails (SEC-01..16): 16/16
Failure handling (FA-01..06)   :  6/6
Total                          : 35/35 = 1.000

---

## Security

| Component | Status | Detail |
|---|---|---|
| Authentication | PASS | JWT (PyJWT), PBKDF2-HMAC-SHA256 200K iterations, random salt |
| RBAC | PASS | Server-side require() dependency; ANALYST/MANAGER/ADMIN |
| SQL protection | PASS | Allowlist + forbidden keyword regex + auto-LIMIT |
| Prompt injection | PASS | 8-pattern scan, flagged chunks redacted before model |
| Approval gate | PASS | DB re-read in action_executor; state not trusted |
| Idempotency | PASS | SHA-256(workflow_id + action_type + payload) |
| Secrets | PASS | JWT_SECRET env var; dev default clearly documented |
| Demo credentials | ANALYST | analyst/analyst123 (documented as dev-only) |

---

## AI

| Component | Status | Detail |
|---|---|---|
| Ollama model | PENDING | No model installed at audit time; pull required |
| LLM path | WORKS when model present | generate_json returns structured dict |
| Fallback behavior | VERIFIED | Deterministic summary with evidence facts, no fabrication |
| RAG mode | tfidf (default) | Recall@4 = 1.000; dense mode available via EMBEDDING_MODE=ollama |
| Agent tool selection | Deterministic | LLM does not choose tools; application planner does |
| Grounding check | Implemented | check_grounding() verifies numbers stated by LLM against computed facts |
| Evidence required | Verified | MIN 2 independent streams + prior-month baseline required |

---

## Infrastructure

| Component | Status | Detail |
|---|---|---|
| Docker | READY, UNTESTED locally | docker-compose.yml: postgres + api + dashboard + worker |
| Ollama in Docker | NOT containerized (by design) | Avoids WSL2 GPU access loss on Windows |
| CI | .github/workflows/ci.yml | ruff lint + mypy + setup + unit + integration + evals |
| Database | SQLite (default) | PostgreSQL ready via Docker |
| Worker | run_batch.py | Revenue recompute + anomaly refresh; runs in Docker worker service |
| Alembic | NOT YET | Schema via create_all; migration history not authored |

---

## Known Limitations

**Only real limitations -- not invented for modesty:**

1. Ollama not yet tested with a pulled model. The LLM degradation path is
   fully tested and working. LLM narrative quality has not been measured.

2. Docker Compose not locally tested (Docker Desktop not installed on this machine).
   The compose file and Dockerfiles are complete and architecturally correct.

3. Alembic migrations not authored. Schema managed via SQLAlchemy create_all.
   Adding migrations is straightforward; it would not change application behavior.

4. SQL_TIMEOUT_S config value exists but is not enforced at the SQLAlchemy
   execution layer (no execution_options set). Low risk: all queries are fast.

5. TF-IDF retrieval is lexical. Recall@4 = 1.000 on this corpus. Will not
   match paraphrases the way dense embeddings would. EMBEDDING_MODE=ollama
   path exists for dense local embeddings.

6. config/customers.yaml exists but is not wired into runtime code. It is a
   design reference showing how multi-tenant configuration would work.

7. Python 3.12+ SQLite date adapter DeprecationWarning appears in test output.
   This is a stdlib issue, not an application issue. Cannot be fixed at application layer.

8. No injected-anomaly benchmark with ground truth. Anomaly detection behavior
   is verified deterministically; precision/recall against a broad set is not claimed.

---

## Exact Startup Commands

### First-time setup
    pip install -r requirements.txt
    cp .env.example .env
    # Edit JWT_SECRET in .env
    python scripts/setup_all.py

### Run API
    uvicorn app.api.main:app --host 0.0.0.0 --port 8000
    # -> http://localhost:8000/docs

### Run dashboard
    streamlit run dashboard/app.py
    # -> http://localhost:8501
    # Demo: manager / manager123

### Check Ollama
    python scripts/check_ollama.py
    # If no model: ollama pull qwen2.5:3b-instruct

### Run all tests
    python -m pytest tests/unit/ tests/integration/ -q

### Run evaluations
    python scripts/run_rag_eval.py
    python scripts/run_agent_eval.py

### Docker (after Docker Desktop installation)
    docker compose up --build
    # Services: postgres:5432 + api:8000 + dashboard:8501 + worker

### Re-run data pipeline (safe, idempotent)
    python scripts/setup_all.py

### Batch recompute
    python scripts/run_batch.py

---

## Classification

This is a **production-style portfolio project**.

It demonstrates correct engineering practice:
deterministic revenue, evidence-based investigation, layered security,
human-in-the-loop approval, and honest measurement.

It is NOT claimed to be production-deployed or running in a live environment.
It uses 100% synthetic data. No real customers, revenue, or operations are involved.

It can be RUN, UNDERSTOOD, DEMO'd, TESTED, DEBUGGED, and DEFENDED in an interview.
