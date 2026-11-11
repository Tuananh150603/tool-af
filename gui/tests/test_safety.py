"""Test core/safety.py — phan loai loi Facebook API."""
from datetime import datetime, timedelta

from gui.core.safety import (backoff_remaining_seconds, backoff_until,
                             classify_fb_error, should_stop)


def test_rate_limit_429():
    assert classify_fb_error({"status": 429, "code": None, "subcode": None, "message": ""}) == "rate_limit"


def test_rate_limit_code_613():
    assert classify_fb_error({"status": 400, "code": 613, "subcode": None, "message": "Calls to this api have exceeded the rate limit."}) == "rate_limit"


def test_checkpoint_subcode():
    err = {"status": 400, "code": 190, "subcode": 459,
           "message": "The session has been invalidated because the user changed their password or Facebook has changed the session for security reasons."}
    assert classify_fb_error(err) == "checkpoint"


def test_checkpoint_message():
    err = {"status": 400, "code": 405, "subcode": None,
           "message": "User must complete checkpoint before using this API."}
    assert classify_fb_error(err) == "checkpoint"


def test_blocked_368():
    assert classify_fb_error({"status": 403, "code": 368, "subcode": None, "message": "blocked"}) == "blocked"


def test_token_expired():
    assert classify_fb_error({"status": 400, "code": 190, "subcode": None, "message": "Error validating access token"}) == "token"


def test_other_error():
    assert classify_fb_error({"status": 400, "code": 100, "subcode": None, "message": "Invalid parameter"}) == "other"


def test_no_error():
    assert classify_fb_error(None) is None
    assert classify_fb_error({}) is None


def test_should_stop_mac_dinh_bat():
    assert should_stop("checkpoint", True) is True
    assert should_stop("rate_limit", True) is True
    assert should_stop("blocked", True) is True
    assert should_stop("token", True) is True
    assert should_stop("other", True) is False
    assert should_stop(None, True) is False


def test_should_stop_khi_tat_cai_dat():
    assert should_stop("checkpoint", False) is False
    assert should_stop("rate_limit", False) is False


def test_backoff():
    now = datetime(2026, 11, 12, 8, 0, 0)
    until = backoff_until(now, 15)
    assert until == now + timedelta(minutes=15)
    assert backoff_remaining_seconds(now, until.isoformat()) == 900
    past = (now - timedelta(minutes=1)).isoformat()
    assert backoff_remaining_seconds(now, past) <= 0
    assert backoff_remaining_seconds(now, None) == 0
