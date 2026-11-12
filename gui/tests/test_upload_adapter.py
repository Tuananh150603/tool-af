"""Test adapters/upload_adapter.py — chong trung, dung checkpoint/429."""
import random
from pathlib import Path

import pytest

from gui.adapters import upload_adapter
from gui.core import store
from gui.core.runlog import RunLog


class FakeCtx:
    def __init__(self, stop_after_progress=None):
        self.logs = []
        self.progress_calls = []
        self.sleeps = []
        self.rng = random.Random(0)
        self._stop = False
        self.stop_after_progress = stop_after_progress

    def log(self, msg):
        self.logs.append(msg)

    def progress(self, done, total, msg):
        self.progress_calls.append((done, total, msg))
        if self.stop_after_progress is not None and done >= self.stop_after_progress:
            self._stop = True

    def is_stopped(self):
        return self._stop

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        return not self._stop


@pytest.fixture()
def pages_with_token(fake_tool_root):
    fx = fake_tool_root
    pages = [{
        "id": "111111111111111", "name": "Mua sắm quanh năm",
        "folder": "111111111111111_Mua_sắm_quanh_năm",
        "dir": str(fx["p1"]), "token": "TESTTOKEN_" + "x" * 100,
    }]
    return fx, pages


def _patch_upload(monkeypatch, tool_root, behavior):
    """behavior: 'ok' | 'checkpoint' | 'rate_limit' | 'fail'."""
    m = upload_adapter.load(tool_root)

    def fake_up_simple(pid, tok, path, title, desc):
        if behavior == "ok":
            m.LAST_API_ERROR = None
            return "123456789"
        if behavior == "checkpoint":
            m.LAST_API_ERROR = {"status": 400, "code": 190, "subcode": 459,
                                "message": "checkpoint required"}
            return None
        if behavior == "rate_limit":
            m.LAST_API_ERROR = {"status": 429, "code": 613, "subcode": None,
                                "message": "rate limit"}
            return None
        m.LAST_API_ERROR = {"status": 400, "code": 100, "subcode": None,
                            "message": "Invalid parameter"}
        return None

    def fake_up_resumable(pid, tok, path, title, desc):
        return fake_up_simple(pid, tok, path, title, desc)

    monkeypatch.setattr(m, "up_simple", fake_up_simple)
    monkeypatch.setattr(m, "up_resumable", fake_up_resumable)
    monkeypatch.setattr(m, "comment", lambda vid, tok, msg, delay=15: True)
    return m


def _resolver(tool_root):
    def resolve(page_dir):
        caps = store.load_text_lines(Path(tool_root) / "captions.txt")
        cmts = store.load_text_lines(Path(tool_root) / "comments.txt")
        return caps, cmts, "chung"
    return resolve


def _opts(**kw):
    o = {"gap": 0, "comment_delay": 0, "big_first": False, "shuffle": False,
         "stop_on_checkpoint": True,
         "backoff_minutes": 15, "manual_files": {}, "rng": random.Random(0)}
    o.update(kw)
    return o


def test_upload_happy_path_2_video(pages_with_token, monkeypatch, tmp_path):
    fx, pages = pages_with_token
    _patch_upload(monkeypatch, fx["root"], "ok")
    log = RunLog(tmp_path / "gui_runlog.json")
    ctx = FakeCtx()
    s = upload_adapter.run_upload_pages(
        fx["root"], pages, _opts(), log, "run1", ctx, _resolver(fx["root"]))
    assert s["ok"] == 2 and s["failed"] == 0 and s["stopped"] is False
    assert s["total"] == 2
    assert log.uploads_today("111111111111111") == 2
    assert 15 not in ctx.sleeps  # comment_delay=0 trong test
    assert any("Video ID: 123456789" in l for l in ctx.logs)


def test_chong_trung_khong_upload_lai(pages_with_token, monkeypatch, tmp_path):
    fx, pages = pages_with_token
    _patch_upload(monkeypatch, fx["root"], "ok")
    log = RunLog(tmp_path / "gui_runlog.json")
    ctx = FakeCtx()
    upload_adapter.run_upload_pages(fx["root"], pages, _opts(), log, "r1", ctx, _resolver(fx["root"]))
    ctx2 = FakeCtx()
    s = upload_adapter.run_upload_pages(fx["root"], pages, _opts(), log, "r2", ctx2, _resolver(fx["root"]))
    assert s["ok"] == 0 and s["skipped"] == 2
    assert log.uploads_today("111111111111111") == 2  # khong tang


def test_khong_gioi_han_video_ngay(pages_with_token, monkeypatch, tmp_path):
    """Bo gioi han video/ngay: page co 2 video thi dang ca 2 trong 1 dot."""
    fx, pages = pages_with_token
    _patch_upload(monkeypatch, fx["root"], "ok")
    log = RunLog(tmp_path / "gui_runlog.json")
    ctx = FakeCtx()
    s = upload_adapter.run_upload_pages(
        fx["root"], pages, _opts(), log, "r1", ctx, _resolver(fx["root"]))
    assert s["ok"] == 2 and s["skipped"] == 0 and s["failed"] == 0
    assert log.uploads_today("111111111111111") == 2
    assert not any("video hôm nay" in l for l in ctx.logs)


def test_dung_khi_checkpoint(pages_with_token, monkeypatch, tmp_path):
    fx, pages = pages_with_token
    _patch_upload(monkeypatch, fx["root"], "checkpoint")
    log = RunLog(tmp_path / "gui_runlog.json")
    ctx = FakeCtx()
    s = upload_adapter.run_upload_pages(
        fx["root"], pages, _opts(), log, "r1", ctx, _resolver(fx["root"]))
    assert s["stopped"] is True
    assert s["stop_kind"] == "checkpoint"
    assert s["ok"] == 0 and s["failed"] == 1  # dung ngay video dau
    assert s["total"] == 1
    assert any("DỪNG ĐỢT CHẠY" in l for l in ctx.logs)
    assert any(e["type"] == "safety_stop" for e in log.data["events"])
    assert log.get_backoff() is None  # checkpoint khong dat backoff


def test_dung_khi_429_va_dat_backoff(pages_with_token, monkeypatch, tmp_path):
    fx, pages = pages_with_token
    _patch_upload(monkeypatch, fx["root"], "rate_limit")
    log = RunLog(tmp_path / "gui_runlog.json")
    ctx = FakeCtx()
    s = upload_adapter.run_upload_pages(
        fx["root"], pages, _opts(), log, "r1", ctx, _resolver(fx["root"]))
    assert s["stopped"] is True and s["stop_kind"] == "rate_limit"
    assert log.get_backoff() is not None
    assert any("backoff" in l for l in ctx.logs)


def test_loi_thuong_khong_dung_dot(pages_with_token, monkeypatch, tmp_path):
    fx, pages = pages_with_token
    _patch_upload(monkeypatch, fx["root"], "fail")
    log = RunLog(tmp_path / "gui_runlog.json")
    ctx = FakeCtx()
    s = upload_adapter.run_upload_pages(
        fx["root"], pages, _opts(), log, "r1", ctx, _resolver(fx["root"]))
    assert s["stopped"] is False  # loi code 100: ghi failed, chay tiep video sau
    assert s["failed"] == 2


def test_checkpoint_khong_dung_khi_tat_cai_dat(pages_with_token, monkeypatch, tmp_path):
    fx, pages = pages_with_token
    _patch_upload(monkeypatch, fx["root"], "checkpoint")
    log = RunLog(tmp_path / "gui_runlog.json")
    ctx = FakeCtx()
    s = upload_adapter.run_upload_pages(
        fx["root"], pages, _opts(stop_on_checkpoint=False),
        log, "r1", ctx, _resolver(fx["root"]))
    assert s["stopped"] is False and s["failed"] == 2


def test_file_nhap_tay_khi_edited_trong(monkeypatch, tmp_path, fake_tool_root):
    fx = fake_tool_root
    manual = tmp_path / "manual.mp4"
    manual.write_bytes(b"manual")
    pages = [{"id": "222222222222222", "name": "Đêm Bình Yên",
              "folder": "222222222222222_Đêm_Bình_Yên",
              "dir": str(fx["p2"]), "token": "TESTTOKEN_" + "x" * 100}]
    _patch_upload(monkeypatch, fx["root"], "ok")
    log = RunLog(tmp_path / "gui_runlog.json")
    ctx = FakeCtx()
    s = upload_adapter.run_upload_pages(
        fx["root"], pages, _opts(manual_files={"222222222222222_Đêm_Bình_Yên": str(manual)}),
        log, "r1", ctx, _resolver(fx["root"]))
    assert s["ok"] == 1
    assert any("nhập tay" in l for l in ctx.logs)


def test_check_token(monkeypatch):
    class Resp:
        def __init__(self, j, status=200):
            self._j = j
            self.status_code = status

        def json(self):
            return self._j

    monkeypatch.setattr(upload_adapter.requests, "get",
                        lambda url, params=None, timeout=None: Resp({"id": "1", "name": "Test Page"}))
    ok, name, err = upload_adapter.check_token("TESTTOKEN_" + "x" * 100)
    assert ok is True and name == "Test Page"

    monkeypatch.setattr(upload_adapter.requests, "get",
                        lambda url, params=None, timeout=None: Resp(
                            {"error": {"code": 190, "message": "token expired"}}, status=400))
    ok, name, err = upload_adapter.check_token("TESTTOKEN_" + "x" * 100)
    assert ok is False and err["code"] == 190

    ok, _, _ = upload_adapter.check_token("ngan")
    assert ok is False
