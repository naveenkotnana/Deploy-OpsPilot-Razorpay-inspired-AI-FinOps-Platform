"""Data quality checks. Bad data is FLAGGED, never silently repaired."""
from dataclasses import dataclass
from typing import List
import pandas as pd


@dataclass
class CheckResult:
    check_name: str
    status: str      # PASS | WARN | FAIL
    observed: str
    threshold: str
    detail: str = ""


def schema_match(df: pd.DataFrame, expected: List[str]) -> CheckResult:
    missing = [c for c in expected if c not in df.columns]
    return CheckResult("SCHEMA_MATCH", "FAIL" if missing else "PASS",
                       f"missing={missing}", "missing=[]",
                       "Required columns absent" if missing else "")


def null_rate(df: pd.DataFrame, cols: List[str], max_rate=0.0) -> CheckResult:
    cols = [c for c in cols if c in df.columns]
    if not cols or df.empty:
        return CheckResult("NULL_RATE", "PASS", "0.0000", f"<={max_rate}")
    rate = float(df[cols].isna().mean().max())
    status = "PASS" if rate <= max_rate else ("WARN" if rate <= max_rate + 0.05 else "FAIL")
    worst = df[cols].isna().mean().idxmax()
    return CheckResult("NULL_RATE", status, f"{rate:.4f}", f"<={max_rate}",
                       f"worst column: {worst}")


def duplicate_rate(df: pd.DataFrame, keys: List[str], max_rate=0.0) -> CheckResult:
    keys = [c for c in keys if c in df.columns]
    if not keys or df.empty:
        return CheckResult("DUPLICATE_RATE", "PASS", "0.0000", f"<={max_rate}")
    dupes = int(df.duplicated(subset=keys).sum())
    rate = dupes / len(df)
    status = "PASS" if rate <= max_rate else "FAIL"
    return CheckResult("DUPLICATE_RATE", status, f"{rate:.4f} ({dupes} rows)",
                       f"<={max_rate}", f"keys={keys}")


def row_count(df: pd.DataFrame, min_rows=1) -> CheckResult:
    n = len(df)
    return CheckResult("ROW_COUNT", "PASS" if n >= min_rows else "FAIL",
                       str(n), f">={min_rows}")


def value_range(df: pd.DataFrame, col: str, lo=None, hi=None) -> CheckResult:
    if col not in df.columns or df.empty:
        return CheckResult("VALUE_RANGE", "PASS", "n/a", f"[{lo},{hi}]")
    s = pd.to_numeric(df[col], errors="coerce")
    bad = 0
    if lo is not None:
        bad += int((s < lo).sum())
    if hi is not None:
        bad += int((s > hi).sum())
    return CheckResult("VALUE_RANGE", "PASS" if bad == 0 else "FAIL",
                       f"{bad} out-of-range", f"{col} in [{lo},{hi}]")


def date_validity(df: pd.DataFrame, cols: List[str]) -> CheckResult:
    cols = [c for c in cols if c in df.columns]
    bad = 0
    for c in cols:
        parsed = pd.to_datetime(df[c], errors="coerce")
        bad += int((parsed.isna() & df[c].notna() & (df[c].astype(str) != "")).sum())
    return CheckResult("DATE_VALIDITY", "PASS" if bad == 0 else "FAIL",
                       f"{bad} unparseable", "0", f"cols={cols}")


def referential_integrity(child: pd.DataFrame, child_col: str,
                          parent_keys: set, label: str) -> CheckResult:
    if child_col not in child.columns:
        return CheckResult("REFERENTIAL_INTEGRITY", "FAIL", "column missing", "0 orphans", label)
    orphans = int((~child[child_col].isin(parent_keys)).sum())
    return CheckResult("REFERENTIAL_INTEGRITY", "PASS" if orphans == 0 else "FAIL",
                       f"{orphans} orphans", "0 orphans", label)


def freshness(df: pd.DataFrame, date_col: str, expected_month: str) -> CheckResult:
    if date_col not in df.columns or df.empty:
        return CheckResult("FRESHNESS", "WARN", "no data", expected_month)
    latest = pd.to_datetime(df[date_col], errors="coerce").max()
    obs = "" if pd.isna(latest) else latest.strftime("%Y-%m")
    return CheckResult("FRESHNESS", "PASS" if obs >= expected_month else "WARN",
                       obs, f">={expected_month}")


def rollup(results: List[CheckResult]) -> str:
    if any(r.status == "FAIL" for r in results):
        return "FAIL"
    if any(r.status == "WARN" for r in results):
        return "WARN"
    return "PASS"
