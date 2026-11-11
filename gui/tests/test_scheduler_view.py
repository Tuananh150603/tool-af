"""Test views/scheduler_view.py — model (headless)."""
from datetime import datetime

from gui.core.config import Config
from gui.core.runlog import RunLog
from gui.views.scheduler_view import build_model


def test_build_model_tat_mac_dinh(tmp_path):
    cfg = Config(path=tmp_path / "gui_config.json")
    log = RunLog(tmp_path / "gui_runlog.json")
    m = build_model(cfg, log, now=datetime(2026, 11, 12, 7, 0, 0))
    assert m["enabled"] is False
    assert m["next_run"] is None
    assert m["due"] is False


def test_build_model_bat_tinh_lan_chay_ke(tmp_path):
    cfg = Config(path=tmp_path / "gui_config.json")
    cfg.data["schedule"] = {"enabled": True, "time": "08:00",
                            "run_edit": True, "run_upload": True}
    log = RunLog(tmp_path / "gui_runlog.json")
    m = build_model(cfg, log, now=datetime(2026, 11, 12, 7, 0, 0))
    assert m["enabled"] is True
    assert m["next_run"] == datetime(2026, 11, 12, 8, 0, 0)
    assert m["due"] is False
    m2 = build_model(cfg, log, now=datetime(2026, 11, 12, 8, 5, 0))
    assert m2["due"] is True
    log.set_last_schedule_date("2026-11-12")
    m3 = build_model(cfg, log, now=datetime(2026, 11, 12, 8, 5, 0))
    assert m3["due"] is False
