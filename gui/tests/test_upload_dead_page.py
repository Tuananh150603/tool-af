"""Test bo qua page chet luc upload: helper live ids + run_upload_pages.

Khong mang that: m.fetch_pages duoc patch; up_simple/comment gia lap.
"""
import random
from pathlib import Path

import pytest

from gui.adapters import upload_adapter
from gui.core import store
from gui.core.runlog import RunLog


class FakeCtx:
    def __init__(self):
        self.logs = []
        self.progress_calls = []
        self.sleeps = []
        self.rng = random.Random(0)
        self._stop = False

    def log(self, msg):
        self.logs.append(msg)

    def progress(self, done, total, msg):
        self.progress_calls.append((done, total, msg))

    def is_stopped(self):
        return self._stop

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        return not self._stop


@pytest.fixture()
def two_pages(fake_tool_root):
    """p1: 2 video; p2: 1 video (them tay vao edited/)."""
    fx = fake_tool_root
    (fx["p2"] / "edited" / "p2vid.mp4").write_bytes(b"p2video")
    pages = [
        {"id": "111111111111111", "name": "Mua sắm quanh năm",
         "folder": "111111111111111_Mua_sắm_quanh_năm",
         "dir": str(fx["p1"]), "token": "TESTTOKEN_" + "x" * 100},
        {"id": "222222222222222", "name": "Đêm Bình Yên",
         "folder": "222222222222222_Đêm_Bình_Yên",
         "dir": str(fx["p2"]), "token": "TESTTOKEN_" + "x" * 100},
    ]
    return fx, pages


def _patch(monkeypatch, tool_root, behavior="ok", live_ids=None):
    """Patch up_simple/resumable/comment + fetch_pages goc tren module that."""
    m = upload_adapter.load(tool_root)
    calls = {"up_simple": []}

    def fake_up_simple(pid, tok, path, title, desc):
        calls["up_simple"].append(path)
        if behavior == "ok":
            m.LAST_API_ERROR = None
            return "123456789"
        if behavior == "checkpoint":
            m.LAST_API_ERROR = {"status": 400, "code": 190, "subcode": 459,
                                "message": "checkpoint required"}
            return None
        m.LAST_API_ERROR = {"status": 400, "code": 100, "subcode": None,
                            "message": "Invalid parameter"}
        return None

    def fake_fetch_pages(user_token):
        return [{"id": pid, "name": pid, "access_token": "tok"}
                for pid in (live_ids or [])]

    monkeypatch.setattr(m, "up_simple", fake_up_simple)
    monkeypatch.setattr(m, "up_resumable", fake_up_simple)
    monkeypatch.setattr(m, "comment", lambda vid, tok, msg, delay=15: True)
    monkeypatch.setattr(m, "fetch_pages", fake_fetch_pages)
    return m, calls


def _resolver(tool_root):
    def resolve(page_dir):
        caps = store.load_text_lines(Path(tool_root) / "captions.txt")
        cmts = store.load_text_lines(Path(tool_root) / "comments.txt")
        return caps, cmts, "chung"
    return resolve


def _opts(**kw):
    o = {"gap": 0, "comment_delay": 0, "big_first": False, "shuffle": False,
         "stop_on_checkpoint": True, "backoff_minutes": 15,
         "manual_files": {}, "rng": random.Random(0)}
    o.update(kw)
    return o


# ---- helper fetch_live_page_ids ----
def test_fetch_live_page_ids_tra_set_id(two_pages, monkeypatch):
    fx, _pages = two_pages
    _patch(monkeypatch, fx["root"], live_ids=["111111111111111", "222222222222222"])
    ids = upload_adapter.fetch_live_page_ids(fx["root"], "USERTOKEN_" + "x" * 100)
    assert ids == {"111111111111111", "222222222222222"}


def test_fetch_live_page_ids_khong_token_thi_none(two_pages, monkeypatch):
    fx, _pages = two_pages

    def boom(*a, **k):
        raise AssertionError("khong duoc goi API khi khong co token")

    m = upload_adapter.load(fx["root"])
    monkeypatch.setattr(m, "fetch_pages", boom)
    assert upload_adapter.fetch_live_page_ids(fx["root"], "") is None
    assert upload_adapter.fetch_live_page_ids(fx["root"], "ngan") is None


def test_fetch_live_page_ids_loi_api_hoac_mang_thi_none(two_pages, monkeypatch):
    fx, _pages = two_pages
    m = upload_adapter.load(fx["root"])

    def err_api(user_token):
        m.LAST_API_ERROR = {"status": 400, "code": 190, "subcode": None,
                            "message": "Error validating access token"}
        return []

    monkeypatch.setattr(m, "fetch_pages", err_api)
    assert upload_adapter.fetch_live_page_ids(fx["root"], "USERTOKEN_" + "x" * 100) is None

    def boom(user_token):
        raise RuntimeError("mat mang")

    monkeypatch.setattr(m, "fetch_pages", boom)
    assert upload_adapter.fetch_live_page_ids(fx["root"], "USERTOKEN_" + "x" * 100) is None

    def empty(user_token):
        return []

    monkeypatch.setattr(m, "fetch_pages", empty)
    assert upload_adapter.fetch_live_page_ids(fx["root"], "USERTOKEN_" + "x" * 100) is None


# ---- (a) page chet bi bo qua, page song van dang ----
def test_page_chet_bo_qua_page_song_van_dang(two_pages, monkeypatch, tmp_path):
    fx, pages = two_pages
    _m, calls = _patch(monkeypatch, fx["root"], "ok",
                       live_ids=["111111111111111"])
    log = RunLog(tmp_path / "gui_runlog.json")
    ctx = FakeCtx()
    s = upload_adapter.run_upload_pages(
        fx["root"], pages,
        _opts(live_page_ids={"111111111111111"}),
        log, "r1", ctx, _resolver(fx["root"]))
    assert s["ok"] == 2 and s["failed"] == 0 and s["stopped"] is False
    assert s["total"] == 3 and s["skipped"] == 1
    # Video cua page chet khong bao gio dua len API
    assert all("p2vid.mp4" not in p for p in calls["up_simple"])
    dead = [u for u in log.data["uploads"] if u["status"] == "skipped_dead_page"]
    assert len(dead) == 1 and dead[0]["page_id"] == "222222222222222"
    # Log noi ro page chet + goi y xoa page
    assert any("không còn trong tài khoản" in l for l in ctx.logs)
    assert any("Xóa page" in l for l in ctx.logs)
    # Plan cung ghi ly do dead_page
    plan = upload_adapter.plan_upload_pages(
        fx["root"], pages, _opts(live_page_ids={"111111111111111"}),
        RunLog(tmp_path / "gui_runlog2.json"), _resolver(fx["root"]))
    assert plan["counts"]["dead_page"] == 1
    assert plan["skipped"][0]["reason"] == "dead_page"


# ---- (b) page song loi token -> dung dot nhu cu ----
def test_page_song_loi_token_van_dung_dot(two_pages, monkeypatch, tmp_path):
    fx, pages = two_pages
    _patch(monkeypatch, fx["root"], "checkpoint",
           live_ids=["111111111111111", "222222222222222"])
    log = RunLog(tmp_path / "gui_runlog.json")
    ctx = FakeCtx()
    s = upload_adapter.run_upload_pages(
        fx["root"], pages,
        _opts(live_page_ids={"111111111111111", "222222222222222"}),
        log, "r1", ctx, _resolver(fx["root"]))
    assert s["stopped"] is True and s["stop_kind"] == "checkpoint"
    assert s["failed"] == 1 and s["ok"] == 0


# ---- (c) live_page_ids=None -> hanh vi dung nhu cu ----
def test_khong_co_live_set_loi_token_van_dung_dot(two_pages, monkeypatch, tmp_path):
    fx, pages = two_pages
    _patch(monkeypatch, fx["root"], "checkpoint",
           live_ids=["111111111111111", "222222222222222"])
    log = RunLog(tmp_path / "gui_runlog.json")
    ctx = FakeCtx()
    s = upload_adapter.run_upload_pages(
        fx["root"], pages, _opts(),
        log, "r1", ctx, _resolver(fx["root"]))
    assert s["stopped"] is True and s["stop_kind"] == "checkpoint"
