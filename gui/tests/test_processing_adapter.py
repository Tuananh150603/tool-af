"""Test adapters/processing_adapter.py — edit xoay vong, chong trung, xoa nguon."""
import random
from pathlib import Path

import pytest

from gui.adapters import processing_adapter
from gui.core.runlog import RunLog


class FakeCtx:
    def __init__(self, stopped=False):
        self.logs = []
        self.progress_calls = []
        self._stopped = stopped
        self.rng = random.Random(0)

    def log(self, msg):
        self.logs.append(msg)

    def progress(self, done, total, msg):
        self.progress_calls.append((done, total, msg))

    def is_stopped(self):
        return self._stopped


@pytest.fixture()
def pool_linked(fake_tool_root, monkeypatch):
    """Gan source.txt cua p1 sang pool gia tren Linux de doc duoc video."""
    fx = fake_tool_root
    pool_vdir = fx["pool"] / "1083489147427179" / "视频"
    (fx["p1"] / "source.txt").write_text(str(pool_vdir) + "\n", encoding="utf-8")
    return fx


def _fake_process_one(monkeypatch, tool_root):
    m = processing_adapter.load(tool_root)

    def fake(src, out_dir, params=None, overwrite=False):
        name = Path(src).stem + "_edit_TEST.mp4"
        out = Path(out_dir) / name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"edited")
        return str(out)

    monkeypatch.setattr(m, "process_one", fake)
    return m


def test_collect_round_robin_1_video_moi_page(pool_linked):
    fx = pool_linked
    items = processing_adapter.collect_round_robin(fx["root"], per_page=1)
    assert len(items) == 1  # chi p1 co kenh; p2/p3 WAITING
    assert items[0][0]["folder"].startswith("111111111111111")
    assert items[0][1].endswith("pool0.mp4")  # lay theo thu tu ten file


def test_edit_one_ok_khong_xoa_nguon(pool_linked, monkeypatch, tmp_path):
    fx = pool_linked
    _fake_process_one(monkeypatch, fx["root"])
    log = RunLog(tmp_path / "gui_runlog.json")
    pg = processing_adapter.page_dicts(fx["root"])[0]
    src = fx["pool"] / "1083489147427179" / "视频" / "pool0.mp4"
    ok, out, err = processing_adapter.edit_one(
        fx["root"], pg, src, {"speed": 1.045}, False, log, "run1", lambda m: None)
    assert ok is True and err == ""
    assert Path(out).is_file()
    assert src.is_file()  # mac dinh KHONG xoa nguon
    assert log.is_source_edited(__import__("gui.core.runlog", fromlist=["file_hash"]).file_hash(src))


def test_edit_one_chong_trung_bo_qua(pool_linked, monkeypatch, tmp_path):
    fx = pool_linked
    _fake_process_one(monkeypatch, fx["root"])
    log = RunLog(tmp_path / "gui_runlog.json")
    pg = processing_adapter.page_dicts(fx["root"])[0]
    src = fx["pool"] / "1083489147427179" / "视频" / "pool0.mp4"
    logs = []
    processing_adapter.edit_one(fx["root"], pg, src, {"speed": 1.045}, False, log, "r1", logs.append)
    ok, out, err = processing_adapter.edit_one(
        fx["root"], pg, src, {"speed": 1.045}, False, log, "r2", logs.append)
    assert ok is False and err == "da-edit"


def test_edit_one_xoa_nguon_khi_bat_tuy_chon(pool_linked, monkeypatch, tmp_path):
    fx = pool_linked
    _fake_process_one(monkeypatch, fx["root"])
    log = RunLog(tmp_path / "gui_runlog.json")
    pg = processing_adapter.page_dicts(fx["root"])[0]
    src = fx["pool"] / "1083489147427179" / "视频" / "pool1.mp4"
    ok, _, _ = processing_adapter.edit_one(
        fx["root"], pg, src, {"speed": 1.045}, True, log, "r1", lambda m: None)
    assert ok is True
    assert not src.exists()


def test_edit_one_loi_ghi_runlog(pool_linked, monkeypatch, tmp_path):
    fx = pool_linked
    m = processing_adapter.load(fx["root"])
    monkeypatch.setattr(m, "process_one",
                        lambda src, out_dir, params=None, overwrite=False: (_ for _ in ()).throw(RuntimeError("ffmpeg lỗi")))
    log = RunLog(tmp_path / "gui_runlog.json")
    pg = processing_adapter.page_dicts(fx["root"])[0]
    src = fx["pool"] / "1083489147427179" / "视频" / "pool0.mp4"
    ok, _, err = processing_adapter.edit_one(
        fx["root"], pg, src, {"speed": 1.045}, False, log, "r1", lambda m: None)
    assert ok is False
    assert log.run_summary("r1")["edits_failed"] == 1


def test_run_edit_round_va_dung_giua_chung(pool_linked, monkeypatch, tmp_path):
    fx = pool_linked
    _fake_process_one(monkeypatch, fx["root"])
    log = RunLog(tmp_path / "gui_runlog.json")
    ctx = FakeCtx()
    s = processing_adapter.run_edit_round(
        fx["root"], None, 1, {"speed": 1.045}, False, {}, False, log, "r1", ctx)
    assert s == {"total": 1, "ok": 1, "failed": 0, "skipped": 0, "stopped": False}
    ctx2 = FakeCtx(stopped=True)
    s2 = processing_adapter.run_edit_round(
        fx["root"], None, 1, {"speed": 1.045}, False, {}, False, log, "r2", ctx2)
    assert s2["stopped"] is True and s2["ok"] == 0
