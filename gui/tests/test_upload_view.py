"""Test views/upload_view.py — model (headless) + bang inline (can Xvfb)."""
import pytest

from gui.core.runlog import RunLog, file_hash
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


@pytest.fixture()
def tk_upload_view(fake_tool_root, tmp_path):
    """App that + man Upload (pattern nhu test_app.py)."""
    try:
        from gui.app import App
        from gui.core.config import Config
    except Exception as e:
        pytest.skip(f"Không import được app: {e}")
    fx = fake_tool_root
    cfg = Config(data={"tool_root": str(fx["root"]), "pool_root": str(fx["pool"])},
                 path=tmp_path / "gui_config.json")
    log = RunLog(tmp_path / "gui_runlog.json")
    try:
        app = App(config=cfg, runlog=log)
    except Exception as e:
        pytest.skip(f"Không mở được cửa sổ GUI (cần màn hình/Xvfb): {e}")
    app.update()
    app.show_view("upload")
    app.update()
    yield app
    try:
        app.destroy()
    except Exception:
        pass


def _rows_by_folder(view):
    return {r["folder"]: r for r in view._rows}


def test_bang_inline_dien_san_caption_comment(tk_upload_view):
    app = tk_upload_view
    view = app.views["upload"]
    assert len(view._rows) == 3
    rows = _rows_by_folder(view)
    p1 = rows["111111111111111_Mua_sắm_quanh_năm"]
    assert p1["video_path"] is not None
    assert p1["video_path"].endswith(".mp4")
    assert p1["status"] == "Sẽ đăng"
    # Gia tri dien san lay tu dung kho caption/comment chung
    assert p1["cap_entry"].get() in ("Caption chung 1", "Caption chung 2",
                                     "Caption chung 3")
    assert p1["cmt_entry"].get() in (
        "Hay quá! Săn deal https://s.shopee.vn/AAAA111 #sale",
        "Đẹp! Mua ở đây https://s.shopee.vn/AAAA111 #xuhuong",
        "Chốt đơn https://s.shopee.vn/BBBB222 #deal")
    # Page khong co video se dang -> o nhap bi khoa, khong co video_path
    for folder in ("222222222222222_Đêm_Bình_Yên", "333333333333333_HANZ"):
        r = rows[folder]
        assert r["video_path"] is None
        assert r["cap_entry"].cget("state") == "disabled"
        assert r["cmt_entry"].cget("state") == "disabled"


def test_doi_boc_lai_caption_comment(tk_upload_view, monkeypatch):
    app = tk_upload_view
    view = app.views["upload"]
    rows = _rows_by_folder(view)
    p1 = rows["111111111111111_Mua_sắm_quanh_năm"]
    # Khoa random.choice -> lay phan tu cuoi kho (xac dinh, khong hen xui)
    monkeypatch.setattr("gui.views.upload_view.random.choice",
                        lambda seq: seq[-1])
    view._reroll_row(p1)
    assert p1["cap_entry"].get() == "Caption chung 3"
    assert p1["cmt_entry"].get() == "Chốt đơn https://s.shopee.vn/BBBB222 #deal"
    # Dong khong co video -> Doi khong lam gi, khong loi
    p2 = rows["222222222222222_Đêm_Bình_Yên"]
    view._reroll_row(p2)
    assert p2["cap_entry"].get() == ""


def test_upload_dung_gia_tri_trong_bang(tk_upload_view, monkeypatch):
    app = tk_upload_view
    view = app.views["upload"]
    rows = _rows_by_folder(view)
    p1 = rows["111111111111111_Mua_sắm_quanh_năm"]
    # Sua tay gia tri trong bang
    p1["cap_entry"].delete(0, "end")
    p1["cap_entry"].insert(0, "CAP BANG")
    p1["cmt_entry"].delete(0, "end")
    p1["cmt_entry"].insert(0, "CMT BANG")
    captured = {}

    def fake_run_task(name, fn, *args, **kwargs):
        captured["name"] = name
        captured["fn"] = fn
        captured["args"] = args
        return True

    monkeypatch.setattr(app, "run_task", fake_run_task)
    view.on_upload()
    assert captured["name"] == "upload"
    pages, opts, overrides = captured["args"]
    assert len(pages) == 3
    assert overrides == {(p1["page_id"], p1["video_path"]): ("CAP BANG", "CMT BANG")}


def test_dong_video_da_dang_hien_ly_do_dup(tk_upload_view, fake_tool_root):
    """(a) Ca 2 video cua page da co trong run-log (hash khop) -> dong hien
    'Video này đã đăng rồi', o nhap bi khoa."""
    app = tk_upload_view
    view = app.views["upload"]
    fx = fake_tool_root
    for name in ("vid1.mp4", "vid2.mp4"):
        p = fx["p1"] / "edited" / name
        app.runlog.record_upload("run-old", "111111111111111",
                                 "111111111111111_Mua_sắm_quanh_năm",
                                 str(p), file_hash(p), "", "", "123", "ok")
    view.refresh()
    app.update()
    rows = _rows_by_folder(view)
    r = rows["111111111111111_Mua_sắm_quanh_năm"]
    assert r["video_path"] is None
    assert r["status"] == "Video này đã đăng rồi"
    assert r["cap_entry"].cget("state") == "disabled"
    assert r["cmt_entry"].cget("state") == "disabled"


def test_dong_da_dang_hom_nay_van_dang_duoc(tk_upload_view):
    """Bo gioi han video/ngay: page da dang 1 video hom nay (hash khac,
    khong phai dup) thi video tiep theo van dang duoc -> 'Sẽ đăng', o nhap
    mo."""
    app = tk_upload_view
    view = app.views["upload"]
    app.runlog.record_upload("run-old", "111111111111111",
                             "111111111111111_Mua_sắm_quanh_năm",
                             "/e/khac.mp4", "hash-khac-khong-trung", "", "",
                             "999", "ok")
    assert app.runlog.uploads_today("111111111111111") == 1
    view.refresh()
    app.update()
    rows = _rows_by_folder(view)
    r = rows["111111111111111_Mua_sắm_quanh_năm"]
    assert r["video_path"] is not None
    assert r["status"] == "Sẽ đăng"
    assert r["cap_entry"].cget("state") == "normal"
    assert r["cmt_entry"].cget("state") == "normal"


def test_dong_khong_co_video_hien_ly_do(tk_upload_view):
    """(c) Page khong co video trong edited/ -> 'Không có video'."""
    app = tk_upload_view
    view = app.views["upload"]
    rows = _rows_by_folder(view)
    for folder in ("222222222222222_Đêm_Bình_Yên", "333333333333333_HANZ"):
        r = rows[folder]
        assert r["video_path"] is None
        assert r["status"] == "Không có video"
        assert r["cap_entry"].cget("state") == "disabled"
        assert r["cmt_entry"].cget("state") == "disabled"


def test_loi_lap_ke_hoach_hien_dong_loi_tren_man_hinh(tk_upload_view, monkeypatch):
    """(d) Planner loi -> dong loi do hien ngay tren man Upload (khong chi
    trong log), bang van hien du dong voi trang thai 'Lỗi kế hoạch'."""
    app = tk_upload_view
    view = app.views["upload"]

    def boom(*a, **k):
        raise RuntimeError("boom test")

    monkeypatch.setattr("gui.adapters.upload_adapter.plan_upload_pages", boom)
    view.refresh()
    app.update()
    assert view._plan_error_label is not None
    text = view._plan_error_label.cget("text")
    assert "Không lập được kế hoạch upload" in text
    assert "boom test" in text
    rows = _rows_by_folder(view)
    assert len(rows) == 3
    for r in rows.values():
        assert r["status"] == "Lỗi kế hoạch"
        assert r["cap_entry"].cget("state") == "disabled"
