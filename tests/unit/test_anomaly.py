from app.ml.anomaly import severity_from_pct, severity_from_exceptions


def test_severity_ladder_is_deterministic():
    assert severity_from_pct(45) == "CRITICAL"
    assert severity_from_pct(30) == "HIGH"
    assert severity_from_pct(18) == "MEDIUM"
    assert severity_from_pct(9) == "LOW"
    assert severity_from_pct(2) == "INFO"


def test_severity_is_symmetric_for_drops():
    assert severity_from_pct(-45) == "CRITICAL"
    assert severity_from_pct(-9) == "LOW"


def test_exception_count_ladder():
    assert severity_from_exceptions(25) == "CRITICAL"
    assert severity_from_exceptions(12) == "HIGH"
    assert severity_from_exceptions(6) == "MEDIUM"
    assert severity_from_exceptions(1) == "LOW"
    assert severity_from_exceptions(0) == "INFO"
