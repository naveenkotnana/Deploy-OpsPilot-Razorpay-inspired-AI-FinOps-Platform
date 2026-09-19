# Architecture

## Layers

| Layer | Module | Responsibility |
|---|---|---|
| Ingestion | `app/services/ingestion.py` | CSV → DB with per-run validation + audit |
| Validation | `app/services/validation.py` | 10 reusable check primitives |
| Domain | `app/models/core.py` | Normalized business tables |
| Revenue | `app/services/revenue.py` | Deterministic business rules |
| Analytics | `app/analytics/queries.py` | 11 documented SQL queries |
| ML | `app/ml/anomaly.py` | Isolation Forest + deterministic rules |
| RAG | `app/rag/store.py` | Chunking, retrieval, citations, access levels |
| LLM | `app/rag/ollama_client.py` | Local Ollama, graceful degradation |
| Agent | `app/agent/workflow.py` | One LangGraph workflow, 10 nodes |
| Tools | `app/agent/tools/` | SQL, RAG, analytics, actions |
| Safety | `app/agent/evidence.py` | Evidence sufficiency + numeric grounding |
| API | `app/api/main.py` | FastAPI, JWT, RBAC |
| UI | `dashboard/app.py` | Streamlit, 10 pages |

## The core security idea

The LLM sits in the middle of the pipeline but has the least authority of any component:

| Capability | Who holds it |
|---|---|
| Write SQL | Application (allowlisted named queries) |
| Choose tools | Application (deterministic planner) |
| Do arithmetic | Analytics tool (trusted functions) |
| Set severity | Deterministic rules |
| Execute actions | Only after a stored APPROVED row |
| Write prose | **LLM** |

That last row is the whole scope of the model's authority.

## Trust boundaries

1. **CSV → ingestion.** Untrusted. Every source validated; FAIL blocks loading.
2. **Retrieved documents → LLM.** Untrusted. Wrapped in a labelled block, injection patterns redacted.
3. **LLM output → action.** Untrusted. Numeric grounding checked; action requires human approval.
4. **Dashboard → API.** Untrusted. All RBAC enforced server-side.

## Request flow: investigation

```
POST /alerts/{id}/investigate
  → require("investigate")          RBAC, server-side
  → run_investigation()             creates Workflow row + trace_id
    → intake                        loads alert; fails safe if absent
    → planner                       deterministic tool plan
    → sql_investigator              3 allowlisted named queries
    → retrieval_investigator        RAG + injection scan
    → analytics_investigator        trusted calculations
    → evidence_validator            sufficiency verdict
    → recommendation_generator      Ollama, or deterministic fallback
    → approval_gate                 PENDING row if action is sensitive
    → audit_logger                  persist evidence + recommendation
  → response with citations + verdict
```

The graph **ends** at `approval_gate`. `action_executor` lives in a second graph reachable only through `POST /workflows/{id}/approve`.
