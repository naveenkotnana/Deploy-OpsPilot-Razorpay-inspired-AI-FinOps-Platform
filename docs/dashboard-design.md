# OpsPilot Dashboard Design — Fintech Analytics Redesign

## 1. Design Inspiration
The OpsPilot operations dashboard is visually and structurally inspired by modern Indian payment analytics platforms (specifically Razorpay's merchant and operations command centers). The objective is to present complex operational telemetry—utility meter readings, apartment plan assignments, deterministic revenue proration, and statistical anomaly detection—with the clean visual hierarchy, density, and clarity of an enterprise payment gateway.

Key design principles borrowed from top-tier fintech interfaces:
- **Dark Navy Navigation Anchor**: A high-contrast, distraction-free sidebar (`#0B1F3A`) that establishes a stable operational anchor.
- **Light Slate Workspace**: A clean, light-gray canvas (`#F7F9FC`) that maximizes contrast and readability for dense data tables and charts.
- **Razorpay Blue Primary Accent**: Vibrant blue (`#2F5BFF`) used purposefully for primary actions, active indicators, and headline line trends without visual clutter.
- **Restrained Semantic Palette**: Emerald green for positive trends/healthy status (`#16A34A`), amber for warnings (`#F59E0B`), and crimson for critical anomalies (`#DC2626`).

---

## 2. Information Architecture
The dashboard maps the entire OpsPilot lifecycle into a progressive disclosure model:

```text
At-a-glance Metrics (Executive KPI Row)
          ↓
Macro Trend Analysis (Revenue Overview Area Chart)
          ↓
Segmentation & Plan Mix (Building Location & Plan Distribution)
          ↓
Drill-down (Operational Records / Transactions Ledger)
          ↓
Exception & Anomaly Detection (Triage Queue & Statistical Deviations)
          ↓
Autonomous Root-Cause Investigation (LangGraph AI Multi-Stream Evidence)
          ↓
Human Governance (Approval Center Gate)
          ↓
Traceability (Cryptographic Audit Trail)
```

---

## 3. Navigation
The sidebar groups the platform's capabilities into four logical operational layers:

```text
OPSPILOT (Operations Command Center)

🏠 Overview

OPERATIONS
  💰 Revenue
  📑 Transactions (Operational Records)
  ⚠️ Exceptions
  🚨 Anomalies

INTELLIGENCE
  📊 Analytics (11 Verified SQL Models)
  ✦ AI Investigation (LangGraph Root Cause Synthesis)

WORKFLOW
  ✓ Approvals (Human-in-the-Loop Gate)
  ⏱ Audit Trail (Cryptographic Execution Ledger)

SYSTEM
  🛡️ Data Quality (Ingestion Runs & Check Matrices)
  ⚙️ Settings (RBAC Persona Switcher & Telemetry)
```

---

## 4. KPI Design
Executive cards follow fintech conventions:
- **Card 1 (Monthly Revenue)**: Large headline figure (`₹10.58L` / `₹1,057,858`) with percentage delta (`-1.1% vs previous month`) and 3-month rolling average context.
- **Card 2 (Active Devices)**: Exact device count (`1,000`) across water meters and appliance controllers with 100% telemetry uptime.
- **Card 3 (Open Exceptions)**: Count of records flagged by deterministic validation rules requiring operational review.
- **Card 4 (Operational Health)**: Overall data pipeline and workflow execution score (`99.8%`).

Each card features a subtle top accent strip, crisp uppercase label, 28px bold value, and semantic trend indicators.

---

## 5. Analytics
- **Primary Trend**: Line/area chart plotting monthly revenue against the 3-month rolling average.
- **Two-Column Segmentation**:
  - **Left**: Revenue by Building Location (`HYD-NORTH`, `HYD-EAST`, `HYD-WEST`, `HYD-CENTRAL`, `HYD-SOUTH`).
  - **Right**: Plan mix breakdown between Water meter tiers and Rental appliance models.
- **Fintech Distribution Bar**: Visual proportion bar showing the split between Water consumption revenue and hardware rental fees.

---

## 6. AI Investigation UX
The AI Investigation interface solves the "black-box chatbot" problem for mission-critical enterprise operations:
1. **Interactive Prompt**: Operator selects an active anomaly ticket and enters an investigative query.
2. **Deterministic Agent Execution**: The 10-node LangGraph agent runs locally via Ollama (`qwen2.5:3b-instruct`).
3. **Transparent Evidence Drawers**:
   - **SQL Telemetry**: Verified database rows showing exactly which numbers were computed.
   - **RAG Policy Documents**: Grounded SOP citations with exact paragraph references.
   - **Confidence & Grounding**: Explicit uncertainty reporting ensuring zero hallucinations.
4. **Action Proposal**: Recommends a concrete remediation action without autonomously executing sensitive side effects.

---

## 7. Approval UX
Sensitive actions (e.g. creating incidents, adjusting billing, dispatching field technicians) hit an immutable **Human Approval Gate**:
- **RBAC Enforcement**: The UI verifies user clearance. Analysts are notified that they can investigate but cannot approve. Managers and Admins are granted execution authority.
- **Audit Justification**: Approvers must enter a justification note before executing.
- **State Transition**: Workflows transition from `PENDING` to `APPROVED` or `REJECTED`, immutably captured in the incident ledger.

---

## 8. Audit UX
Every tool call, user action, decision justification, latency measurement, and SHA-256 input hash is recorded in the **Audit Ledger**. Operators can filter by workflow ID, user persona, or date range to maintain regulatory compliance and operational accountability.

---

## 9. Color System
| Token | Hex | Role |
|---|---|---|
| Sidebar Navy | `#0B1F3A` | Navigation background |
| Primary Blue | `#2F5BFF` | Brand accent, primary buttons, line chart |
| Workspace Canvas | `#F7F9FC` | Page background |
| Card Surface | `#FFFFFF` | Metric panels, tables |
| Subtle Border | `#E6EAF0` | Card borders, dividers |
| Success / Trend Up | `#16A34A` | Positive delta, healthy status |
| Warning / Amber | `#F59E0B` | Medium anomalies, review flags |
| Danger / Critical | `#DC2626` | Critical alerts, negative delta |
| Secondary Cyan | `#06B6D4` | Water telemetry, secondary metrics |

---

## 10. Accessibility
- High-contrast text compliance (minimum 4.5:1 on all surfaces).
- Standardized tabular layouts compatible with screen readers.
- Double encoding for all alert states (color badge + text label).

---

## 11. Razorpay Interview Relevance
During an interview, this redesigned dashboard demonstrates:
1. **Fintech Product Thinking**: Understanding how operations analysts and finance teams monitor transactional velocity, detect leakages, and reconcile exceptions.
2. **Separation of Concerns**: Financial math is calculated deterministically via SQL window functions and Python revenue engines—never generated unpredictably by an LLM.
3. **Enterprise Governance**: Demonstrating that autonomous AI agents must be bounded by deterministic validation, grounding checks, and human approval gates before affecting production systems.
4. **Local / Cost-Aware Engineering**: The entire system runs locally with zero external API fees, 100% data privacy, and optimized memory footprints suitable for real-world edge deployment.
