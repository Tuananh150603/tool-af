"""Test core/scheduler.py — gio hen chay tu dong."""
from datetime import datetime

from gui.core.scheduler import is_due, next_run_datetime, parse_hhmm


def test_parse_hhmm():
    assert parse_hhmm("08:00").hour == 8
    assert parse_hhmm("23:59").minute == 59
    assert parse_hhmm("8:00") is not None
    assert parse_hhmm("24:00") is None
    assert parse_hhmm("abc") is None
    assert parse_hhmm("") is None


def test_next_run_trong_ngay():
    now = datetime(2026, 11, 12, 7, 0, 0)
    assert next_run_datetime(now, "08:00") == datetime(2026, 11, 12, 8, 0, 0)


def test_next_run_gio_da_qua_sang_ngay_mai():
    now = datetime(2026, 11, 12, 9, 0, 0)
    assert next_run_datetime(now, "08:00") == datetime(2026, 11, 13, 8, 0, 0)


def test_is_due():
    assert is_due(datetime(2026, 11, 12, 8, 5, 0), "08:00", None) is True
    assert is_due(datetime(2026, 11, 12, 8, 5, 0), "08:00", "2026-11-12") is False
    assert is_due(datetime(2026, 11, 12, 7, 59, 0), "08:00", None) is False
    assert is_due(datetime(2026, 11, 12, 8, 5, 0), "08:00", "2026-11-11") is True
