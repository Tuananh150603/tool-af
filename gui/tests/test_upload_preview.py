"""Test xem truoc upload: plan + override + bo qua (khong mang that)."""
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


def _patch_upload(monkeypatch, tool_root, behavior="ok"):
    """Nhu test_upload_adapter, them dem so lan goi up_simple/comment."""
    m = upload_adapter.load(tool_root)
    calls = {"up_simple": [], "comment": []}

    def fake_up_simple(pid, tok, path, title, desc):
        calls["up_simple"].append((path, title, desc))
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

    def fake_up_resumable(pid, tok, path, title, desc):
        return fake_up_simple(pid, tok, path, title, desc)

    def fake_comment(vid, tok, msg, delay=15):
        calls["comment"].append((vid, msg))
        return True

    monkeypatch.setattr(m, "up_simple", fake_up_simple)
    monkeypatch.setattr(m, "up_resumable", fake_up_resumable)
    monkeypatch.setattr(m, "comment", fake_comment)
    return m, calls


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


# ---- (a) plan tra dung video run se dang (khong gioi han so video) ----
def test_plan_khong_gioi_han_video(pages_with_token, monkeypatch, tmp_path):
    """Bo gioi han video/ngay: plan gom ca 2 video, run dang ca 2."""
    fx, pages = pages_with_token
    _patch_upload(monkeypatch, fx["root"])
    log = RunLog(tmp_path / "gui_runlog.json")
    plan = upload_adapter.plan_upload_pages(
        fx["root"], pages, _opts(), log, _resolver(fx["root"]))
    assert len(plan["items"]) == 2
    assert [i["video_name"] for i in plan["items"]] == ["vid1.mp4", "vid2.mp4"]
    assert plan["counts"] == {"dup": 0}
    assert plan["total"] == 2
    ctx = FakeCtx()
    s = upload_adapter.run_upload_pages(
        fx["root"], pages, _opts(), log, "r1", ctx, _resolver(fx["root"]))
    assert s["ok"] == 2 and s["skipped"] == 0 and s["total"] == 2
    ok_entry = [u for u in log.data["uploads"] if u["status"] == "ok"][0]
    assert ok_entry["file_path"] == plan["items"][0]["video_path"]
    assert not any(u["status"] == "skipped_cap" for u in log.data["uploads"])


def test_plan_dedup_video_da_dang(pages_with_token, monkeypatch, tmp_path):
    fx, pages = pages_with_token
    _patch_upload(monkeypatch, fx["root"])
    log = RunLog(tmp_path / "gui_runlog.json")
    ctx = FakeCtx()
    upload_adapter.run_upload_pages(
        fx["root"], pages, _opts(), log, "r1", ctx, _resolver(fx["root"]))
    assert log.uploads_today("111111111111111") == 2
    before = len(log.data["uploads"])
    plan = upload_adapter.plan_upload_pages(
        fx["root"], pages, _opts(), log, _resolver(fx["root"]))
    assert plan["items"] == []
    assert plan["counts"] == {"dup": 2}
    assert plan["total"] == 2
    assert len(log.data["uploads"]) == before  # plan khong ghi run-log


def test_plan_xao_tron_xac_dinh_theo_seed(pages_with_token, tmp_path):
    fx, pages = pages_with_token
    log = RunLog(tmp_path / "gui_runlog.json")
    p1 = upload_adapter.plan_upload_pages(
        fx["root"], pages, _opts(shuffle=True, rng=random.Random(7)),
        log, _resolver(fx["root"]))
    p2 = upload_adapter.plan_upload_pages(
        fx["root"], pages, _opts(shuffle=True, rng=random.Random(7)),
        log, _resolver(fx["root"]))
    assert [i["video_name"] for i in p1["items"]] == [i["video_name"] for i in p2["items"]]
    assert len(p1["items"]) == 2


def test_plan_khong_upload_khong_goi_mang(pages_with_token, tmp_path):
    """Plan chay ma khong patch ham upload nao — khong goi API, khong ghi log."""
    fx, pages = pages_with_token
    log = RunLog(tmp_path / "gui_runlog.json")
    plan = upload_adapter.plan_upload_pages(
        fx["root"], pages, _opts(), log, _resolver(fx["root"]))
    assert len(plan["items"]) == 2
    assert log.data["uploads"] == []
    # Page khong co video -> plan rong, khong loi
    p2 = [{"id": "222222222222222", "name": "Đêm Bình Yên",
           "folder": "222222222222222_Đêm_Bình_Yên",
           "dir": str(fx["p2"]), "token": "TESTTOKEN_" + "x" * 100}]
    plan2 = upload_adapter.plan_upload_pages(
        fx["root"], p2, _opts(), log, _resolver(fx["root"]))
    assert plan2["items"] == [] and plan2["total"] == 0


# ---- (b) override duoc ton trong ----
def test_override_caption_comment_duoc_ghi_runlog(pages_with_token, monkeypatch, tmp_path):
    fx, pages = pages_with_token
    _, calls = _patch_upload(monkeypatch, fx["root"])
    log = RunLog(tmp_path / "gui_runlog.json")
    plan = upload_adapter.plan_upload_pages(
        fx["root"], pages, _opts(), log, _resolver(fx["root"]))
    assert len(plan["items"]) == 2
    first = plan["items"][0]
    key = (first["page_id"], first["video_path"])
    overrides = {key: ("CAP MOI SUA TAY", "CMT MOI SUA TAY")}
    ctx = FakeCtx()
    s = upload_adapter.run_upload_pages(
        fx["root"], pages, _opts(), log, "r1", ctx, _resolver(fx["root"]),
        overrides=overrides, plan=plan)
    assert s["ok"] == 2 and s["failed"] == 0
    edited = [u for u in log.data["uploads"]
              if u["status"] == "ok" and u["file_path"] == first["video_path"]][0]
    assert edited["caption"] == "CAP MOI SUA TAY"
    assert edited["comment"] == "CMT MOI SUA TAY"
    # Ham upload goc nhan dung caption da sua (title = caption cat 90 ky tu)
    sent = [c for c in calls["up_simple"] if c[0] == first["video_path"]][0]
    assert sent[1] == "CAP MOI SUA TAY" and sent[2] == "CAP MOI SUA TAY"
    # Video con lai van dung caption ngau nhien tu kho, khong bi override
    other = [u for u in log.data["uploads"]
             if u["status"] == "ok" and u["file_path"] != first["video_path"]][0]
    assert other["caption"] != "CAP MOI SUA TAY"


def test_override_ngoai_ke_hoach_bi_bo_qua(pages_with_token, monkeypatch, tmp_path):
    fx, pages = pages_with_token
    _patch_upload(monkeypatch, fx["root"])
    log = RunLog(tmp_path / "gui_runlog.json")
    ctx = FakeCtx()
    s = upload_adapter.run_upload_pages(
        fx["root"], pages, _opts(), log, "r1", ctx, _resolver(fx["root"]),
        overrides={("111111111111111", "/khong/co/file.mp4"): ("X", "Y")})
    assert s["ok"] == 2 and s["failed"] == 0


# ---- (c) bo qua hang ----
def test_bo_qua_hang_khong_upload(pages_with_token, monkeypatch, tmp_path):
    fx, pages = pages_with_token
    _, calls = _patch_upload(monkeypatch, fx["root"])
    log = RunLog(tmp_path / "gui_runlog.json")
    plan = upload_adapter.plan_upload_pages(
        fx["root"], pages, _opts(), log, _resolver(fx["root"]))
    first = plan["items"][0]
    key = (first["page_id"], first["video_path"])
    ctx = FakeCtx()
    s = upload_adapter.run_upload_pages(
        fx["root"], pages, _opts(), log, "r1", ctx, _resolver(fx["root"]),
        skip={key}, plan=plan)
    assert s["ok"] == 1 and s["failed"] == 0 and s["skipped"] == 1 and s["total"] == 2
    assert len(calls["up_simple"]) == 1  # chi upload video con lai
    assert calls["up_simple"][0][0] != first["video_path"]
    skipped = [u for u in log.data["uploads"] if u["status"] == "skipped_user"]
    assert len(skipped) == 1 and skipped[0]["file_path"] == first["video_path"]


# ---- (d) file nhap tay xuat hien trong plan ----
def test_plan_co_file_nhap_tay_khi_edited_trong(monkeypatch, tmp_path, fake_tool_root):
    fx = fake_tool_root
    manual = tmp_path / "manual.mp4"
    manual.write_bytes(b"manual")
    pages = [{"id": "222222222222222", "name": "Đêm Bình Yên",
              "folder": "222222222222222_Đêm_Bình_Yên",
              "dir": str(fx["p2"]), "token": "TESTTOKEN_" + "x" * 100}]
    log = RunLog(tmp_path / "gui_runlog.json")
    plan = upload_adapter.plan_upload_pages(
        fx["root"], pages,
        _opts(manual_files={"222222222222222_Đêm_Bình_Yên": str(manual)}),
        log, _resolver(fx["root"]))
    assert len(plan["items"]) == 1
    assert plan["items"][0]["video_path"] == str(manual)
    assert plan["items"][0]["page_id"] == "222222222222222"
    _patch_upload(monkeypatch, fx["root"])
    ctx = FakeCtx()
    s = upload_adapter.run_upload_pages(
        fx["root"], pages,
        _opts(manual_files={"222222222222222_Đêm_Bình_Yên": str(manual)}),
        log, "r1", ctx, _resolver(fx["root"]))
    assert s["ok"] == 1
