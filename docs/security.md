# Security

## SQL: safe by construction

The model **cannot write SQL**. It selects a name from `QUERIES`; the application owns the text. This eliminates model-driven SQL injection structurally rather than by filtering — there is no "sanitise the LLM's SQL" code path because there is no LLM SQL.

The raw-SQL path (API only) enforces: SELECT/WITH only, single statement, no write/DDL keywords, allowlisted tables, forced `LIMIT`.

Verified: SEC-01 DROP · SEC-02 DELETE · SEC-03 UPDATE · SEC-04 non-allowlisted table · SEC-05 stacked statements · SEC-06 LIMIT injection · SEC-07 unknown query name. All blocked.

## Authentication

PBKDF2-HMAC-SHA256, 200,000 iterations, 16-byte random salt per password, stdlib only. JWT HS256 with expiry. `JWT_SECRET` from environment; the dev default is explicitly labelled and must be changed.

No credential is hardcoded. Demo users are seeded at startup with clearly-demo passwords in a synthetic local environment.

## RBAC — server-side

| Role | Permissions |
|---|---|
| Analyst | view, investigate |
| Manager | view, investigate, approve, reject |
| Admin | + configure, manage_users, administer |

Enforced by a FastAPI dependency (`require(...)`) on every protected route. **The dashboard's UI restrictions are cosmetic.** `test_analyst_cannot_approve` asserts a 403 arrives *before* any resource lookup, so permission denial does not leak resource existence.

## Prompt injection defence

Retrieved documents are untrusted. Three layers:

1. **Never in the system prompt.** Retrieved text goes in a delimited `<retrieved_documents>` block labelled UNTRUSTED.
2. **Pattern detection.** Nine regex patterns for instruction-override attempts.
3. **Redaction.** A matching chunk is replaced with `[CONTENT REDACTED]` *before* the model sees it — detection and removal, not just logging.

Retrieved text can never modify permissions, tool availability, system instructions, approval rules, or severity — none of those are derived from model output in the first place.

Verified: SEC-08 detection · SEC-09 redaction (`"Grant me admin"` absent from the assembled block) · SEC-10 labelling. Plus 4 parametrized unit cases and a false-positive check on benign policy text.

## Document access control

Filtered at retrieval by role clearance, so over-clearance content never enters the context window. Verified by SEC-16.

## Action safety

Idempotency key = `sha256(workflow_id | action_type | payload)`, **unique-constrained in the database**. A repeat is recorded `DUPLICATE_SKIPPED`. AP-05 calls the approved path three times and asserts exactly one action row.

## Known gaps

No rate limiting. No refresh-token rotation. No secrets manager. `SQL_TIMEOUT_S` is configured but not enforced at the driver level for SQLite. CORS is permissive for local development. All appropriate for a local synthetic portfolio project; all would need addressing before any real deployment.
