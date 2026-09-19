"""Revenue engine edge cases. These are the rules money depends on."""
import datetime as dt
import pytest
from app.services.revenue import active_days, month_bounds, _money, _as_date


def test_month_bounds_30_day():
    s, e, n = month_bounds("2026-09")
    assert (s, e, n) == (dt.date(2026, 9, 1), dt.date(2026, 9, 30), 30)


def test_month_bounds_february_leap():
    assert month_bounds("2028-02")[2] == 29


def test_full_month_active():
    assert active_days(dt.date(2026, 1, 1), None, dt.date(2026, 9, 1), dt.date(2026, 9, 30)) == 30


def test_mid_month_activation_is_inclusive():
    # activated on the 15th of a 30-day month -> 16 days, both endpoints counted
    assert active_days(dt.date(2026, 9, 15), None, dt.date(2026, 9, 1), dt.date(2026, 9, 30)) == 16


def test_deactivation_mid_month():
    assert active_days(dt.date(2026, 1, 1), dt.date(2026, 9, 10),
                       dt.date(2026, 9, 1), dt.date(2026, 9, 30)) == 10


def test_zero_active_days_when_activated_after_month():
    assert active_days(dt.date(2026, 10, 5), None, dt.date(2026, 9, 1), dt.date(2026, 9, 30)) == 0


def test_zero_active_days_when_deactivated_before_month():
    assert active_days(dt.date(2026, 1, 1), dt.date(2026, 8, 1),
                       dt.date(2026, 9, 1), dt.date(2026, 9, 30)) == 0


def test_missing_activation_date_yields_zero_not_guess():
    assert active_days(None, None, dt.date(2026, 9, 1), dt.date(2026, 9, 30)) == 0


def test_invalid_date_string_parses_to_none():
    assert _as_date("not-a-date") is None
    assert _as_date("") is None


def test_money_rounds_half_up():
    assert str(_money(1.005)) == "1.01"
    assert str(_money(2.344)) == "2.34"
