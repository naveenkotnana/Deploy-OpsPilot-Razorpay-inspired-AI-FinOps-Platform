"""Evidence validator.

The single most important safety component. It answers: does the collected
evidence actually support a root-cause claim? If not, the workflow returns
INSUFFICIENT EVIDENCE instead of letting the model invent one.

Classification vocabulary, enforced downstream:
  FACT        - a value read directly from the database this run
  EVIDENCE    - a retrieved policy statement or SQL result supporting a claim
  INFERENCE   - a reasoned link between facts, explicitly labelled
  UNCERTAINTY - what is not known and what would resolve it
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class EvidenceBundle:
    facts: Dict[str, Any] = field(default_factory=dict)
    sql_results: List[dict] = field(default_factory=list)
    documents: List[dict] = field(default_factory=list)
    analytics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


# A recommendation may only be generated when enough independent evidence
# streams succeeded. Thresholds are deterministic, not model-decided.
MIN_STREAMS = 2
MIN_DOC_SCORE = 0.05


def validate(bundle: EvidenceBundle) -> dict:
    streams, missing, notes = [], [], []

    if bundle.analytics and bundle.analytics.get("revenue"):
        streams.append("ANALYTICS")
    else:
        missing.append("analytics")

    sql_ok = [r for r in bundle.sql_results if r.get("ok") and r.get("row_count", 0) > 0]
    if sql_ok:
        streams.append("SQL")
    else:
        missing.append("sql")

    good_docs = [d for d in bundle.documents
                 if d.get("relevance_score", 0) >= MIN_DOC_SCORE]
    if good_docs:
        streams.append("POLICY")
    else:
        missing.append("policy")
        notes.append("No policy chunk met the relevance floor.")

    # A change percentage is required to claim a revenue root cause at all.
    change = (bundle.analytics or {}).get("change", {})
    has_baseline = change.get("previous") is not None
    if not has_baseline:
        notes.append("No prior-month baseline; magnitude claims are not supported.")

    sufficient = len(streams) >= MIN_STREAMS and has_baseline

    return {
        "sufficient": sufficient,
        "streams_present": streams,
        "streams_missing": missing,
        "document_count": len(good_docs),
        "sql_result_sets": len(sql_ok),
        "has_baseline": has_baseline,
        "notes": notes,
        "verdict": "EVIDENCE_SUFFICIENT" if sufficient else "INSUFFICIENT_EVIDENCE",
    }


def check_grounding(claim_text: str, bundle: EvidenceBundle) -> dict:
    """Cheap numeric grounding check: every number the model states should be
    traceable to a number we actually computed. Catches fabricated figures."""
    import re
    stated = set(re.findall(r"\d[\d,]*\.?\d*", claim_text or ""))
    known = set()

    def collect(o):
        if isinstance(o, dict):
            for v in o.values():
                collect(v)
        elif isinstance(o, list):
            for v in o:
                collect(v)
        elif isinstance(o, (int, float)):
            known.add(f"{o}")
            known.add(f"{round(float(o), 2)}")
            known.add(f"{round(float(o))}")

    collect(bundle.analytics)
    collect([r.get("rows", []) for r in bundle.sql_results])

    def norm(s):
        return s.replace(",", "").rstrip(".")

    known_n = {norm(k) for k in known}
    unmatched = []
    for s in stated:
        n = norm(s)
        if len(n) < 3:          # ignore small ordinals, section numbers, years
            continue
        if n in known_n or any(n in k or k in n for k in known_n):
            continue
        unmatched.append(s)
    return {"numbers_stated": len(stated), "unsupported_numbers": unmatched,
            "grounded": len(unmatched) == 0}
