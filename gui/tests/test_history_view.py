"""Test views/history_view.py — model (headless)."""
from gui.core.runlog import RunLog
from gui.views.history_view import build_model


def test_build_model(tmp_path):
    log = RunLog(tmp_path / "gui_runlog.json")
    log.record_upload("r1", "111", "p1", "/e/a.mp4", "h1", "", "", "5", "ok")
    log.record_edit("r1", "111", "p1", "/s.mp4", "hh", "/o.mp4", {}, "ok")
    log.record_event("safety_stop", "Dừng do checkpoint")
    m = build_model(log)
    assert len(m["items"]) == 3
    assert m["runs"]["r1"]["uploads_ok"] == 1
    assert m["runs"]["r1"]["edits_ok"] == 1
