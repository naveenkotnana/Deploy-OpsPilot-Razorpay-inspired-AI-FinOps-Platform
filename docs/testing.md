# Testing

## Results

| Suite | Command | Result |
|---|---|---|
| Unit | `pytest tests/unit -q` | **38 passed** |
| Integration | `pytest tests/integration -q` | **27 passed** |
| Full | `pytest tests/ -q` | **65 passed** |
| RAG eval | `python scripts/run_rag_eval.py` | **22/22** |
| Agent/security eval | `python scripts/run_agent_eval.py` | **35/35** |

## Edge cases covered explicitly

Every case the spec called out, as a named test:

| Edge case | Test |
|---|---|
| Missing installation date | `test_missing_activation_date_yields_zero_not_guess` |
| Duplicate usage | `test_duplicate_rate_flags_duplicates`, `duplicate_usage` query |
| Multiple plans | `MULTIPLE_ACTIVE_PLANS` check, `multiple_active_plans` query |
| Missing usage | `MISSING_USAGE` exception code (6 real occurrences in 2026-04) |
| Invalid plan | `INVALID_PLAN` check, `INVALID_WATER_PLAN` code |
| Zero active days | `test_zero_active_days_when_activated_after_month`, `..._deactivated_before_month` |
| Invalid dates | `test_invalid_date_string_parses_to_none`, `test_date_validity_detects_bad_date` |
| Leap year | `test_month_bounds_february_leap` |
| Mid-month proration | `test_mid_month_activation_is_inclusive` (16 days, not 15) |
| Rounding | `test_money_rounds_half_up` |

## Failure paths, not just happy paths

SQL failure, malformed SQL, non-allowlisted table, stacked statements, Ollama unavailable, Ollama timeout, malformed LLM JSON, empty retrieval, no prior-month baseline, unknown workflow, unknown alert, missing approval, rejected approval, duplicate action, invalid JWT, missing credentials, insufficient permissions.

## Determinism

`test_revenue_computation_is_reproducible` computes 2026-09 twice and asserts identical totals. Isolation Forest uses `random_state=42`.

## What is not tested

LLM generation quality — Ollama was unavailable in the build environment. The degradation path is fully tested; narrative quality is not. No load or concurrency testing. No browser testing of the Streamlit UI.
