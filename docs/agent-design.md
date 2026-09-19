# Agent Design

## One workflow, not many agents

A single stateful LangGraph workflow with ten nodes. No multi-agent architecture, because nothing here requires one: the investigation is a fixed sequence of evidence gathering followed by a safety gate. Multiple autonomous agents would add coordination failure modes and nondeterminism in exchange for nothing.

## State

`workflow_id`, `alert_id`, `user_id`, `role`, `permissions`, `question`, `trace_id`, `investigation_context`, `sql_results`, `retrieved_documents`, `analytics_results`, `evidence`, `recommendation`, `approval_required`, `approval_status`, `final_action`, `errors`, `node_timings`, `llm_available`.

## Nodes

| # | Node | Does | LLM? |
|---|---|---|---|
| 1 | `intake` | Load alert, build question; fails safe if absent | No |
| 2 | `planner` | Deterministic tool plan | **No** |
| 3 | `sql_investigator` | 3 allowlisted named queries | No |
| 4 | `retrieval_investigator` | RAG + injection scan | No |
| 5 | `analytics_investigator` | Trusted calculations | No |
| 6 | `evidence_validator` | Sufficiency verdict | No |
| 7 | `recommendation_generator` | Narrative + grounding check | **Yes** |
| 8 | `approval_gate` | Creates PENDING approval | No |
| 9 | `action_executor` | Executes after approval | No |
| 10 | `audit_logger` | Persists everything | No |

**The planner is deliberately not LLM-driven.** Tool selection is a security boundary. Letting the model choose tools means letting a prompt-injected document choose tools.

## The gate is structural, not conditional

The graph **ends** at `approval_gate`. `action_executor` is in a separate graph, invoked only by `POST /workflows/{id}/approve`. There is no code path from recommendation to action that does not pass through a stored approval row.

`action_executor` re-reads the approval from the database rather than trusting `state["approval_status"]`, so a forged state object still cannot execute an action.

## Evidence validation

Three independent streams — ANALYTICS, SQL, POLICY. A recommendation requires **≥2 streams present AND a prior-month baseline**. Without a baseline, magnitude claims are unsupported by definition, so the workflow returns `INSUFFICIENT_EVIDENCE` rather than a plausible guess.

## Numeric grounding

After generation, every number in the model's output is matched against numbers actually computed this run. Unmatched figures are appended to `uncertainty` as `[UNVERIFIED FIGURES: ...]` and confidence is forced to LOW. Verified by `AG-07` (catches a fabricated 999999.99) and `AG-08` (passes a real 212669.87).

## Vocabulary the model must use

`FACT` (value read from the DB) · `EVIDENCE` (retrieved policy or SQL result) · `INFERENCE` (reasoned link, labelled as such) · `UNCERTAINTY` (what is unknown and what would resolve it).

## Measured results — 35 cases, 35 passed

| Suite | Cases | Passed |
|---|---|---|
| Agent behaviour | 8 | 8 |
| Approval & idempotency | 5 | 5 |
| Security | 16 | 16 |
| Failure handling | 6 | 6 |
