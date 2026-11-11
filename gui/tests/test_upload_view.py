"""Test views/upload_view.py — model (headless)."""
from gui.core.runlog import RunLog
from gui.views.upload_view import build_model


def test_build_model_fake(fake_tool_root, tmp_path):
    fx = fake_tool_root
    log = RunLog(tmp_path / "gui_runlog.json")
    m = build_model(fx["root"], log)
    assert len(m["pages"]) == 3
    assert m["pages"][0]["edited_count"] == 2
    assert m["last_pending_run"] is None
    log.record_upload("run-old", "111111111111111", "p1", "/e/a.mp4", "h1",
                      "", "", "", "pending")
    log.record_upload("run-old", "111111111111111", "p1", "/e/b.mp4", "h2",
                      "", "", "5", "ok")
    m2 = build_model(fx["root"], log)
    assert m2["last_pending_run"] == "run-old"
    assert len(m2["pending"]) == 1
