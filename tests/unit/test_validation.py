import pandas as pd
from app.services import validation as V


def test_schema_match_detects_missing_column():
    df = pd.DataFrame({"a": [1]})
    assert V.schema_match(df, ["a", "b"]).status == "FAIL"


def test_duplicate_rate_flags_duplicates():
    df = pd.DataFrame({"id": [1, 1, 2]})
    assert V.duplicate_rate(df, ["id"]).status == "FAIL"


def test_null_rate_passes_clean_frame():
    df = pd.DataFrame({"a": [1, 2, 3]})
    assert V.null_rate(df, ["a"]).status == "PASS"


def test_value_range_detects_negative():
    df = pd.DataFrame({"v": [-1, 5]})
    assert V.value_range(df, "v", lo=0).status == "FAIL"


def test_referential_integrity_detects_orphan():
    child = pd.DataFrame({"fk": ["A", "Z"]})
    assert V.referential_integrity(child, "fk", {"A"}, "t").status == "FAIL"


def test_date_validity_detects_bad_date():
    df = pd.DataFrame({"d": ["2026-01-01", "banana"]})
    assert V.date_validity(df, ["d"]).status == "FAIL"


def test_rollup_precedence():
    mk = lambda s: V.CheckResult("X", s, "", "")
    assert V.rollup([mk("PASS"), mk("WARN"), mk("FAIL")]) == "FAIL"
    assert V.rollup([mk("PASS"), mk("WARN")]) == "WARN"
    assert V.rollup([mk("PASS")]) == "PASS"
