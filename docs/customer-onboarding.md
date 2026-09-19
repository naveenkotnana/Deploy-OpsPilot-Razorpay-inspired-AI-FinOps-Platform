# Customer Onboarding

Lightweight FDE-style configuration. **One codebase, many configurations.** Nothing in `config/customers.yaml` forks the core system — it selects data sources, tools, and policy thresholds at runtime.

## Configuration shape

`customer_id`, `data_sources`, `schemas`, `allowed_tools`, `policies` (severity thresholds, ML severity cap), `workflow_rules`, `approval_rules` (which actions need approval, which roles may approve), `notification_channels`.

## The three synthetic configurations

| | Customer A | Customer B | Customer C |
|---|---|---|---|
| Domain | Subscription/device revenue | Customer support ops | Internal IT ops |
| Entity grain | `location_code` | `queue` | `service` |
| Alert floor | MEDIUM | HIGH | MEDIUM |
| Severity ladder | 8/15/25/40 | 15/30/50/75 | 5/10/20/30 |
| ML-only cap | LOW | LOW | MEDIUM |
| Actions | incident, ticket, notification | ticket only | incident, notification |
| Approvers | Manager, Admin | Manager, Admin | **Admin only** |

The thresholds differ because the domains differ: support volume swings more before it means anything, IT incidents escalate faster.

## Usage

```python
from app.core.customer_config import get_customer, tool_allowed, requires_approval

tool_allowed("customer_b", "create_incident")        # False
requires_approval("customer_c", "create_incident")   # True
get_customer("customer_b")["policies"]["severity_thresholds"]
```

## Onboarding a new customer

1. Add a block to `config/customers.yaml`.
2. Map data sources to the ingestion loaders.
3. Set severity thresholds for the domain's volatility.
4. Restrict `allowed_tools` to what that customer permits.
5. Set `approval_rules` to match their governance.
6. Add policy documents to `data/documents/` with correct `ACCESS_LEVEL` headers.
7. Re-run `setup_all.py`.

No code change. No second codebase.

**Current state, stated honestly:** the config loader and its accessors are implemented and tested, but the runtime severity ladder in `app/ml/anomaly.py` still reads its module-level constants rather than the per-customer config. Wiring that through is listed in future work.
