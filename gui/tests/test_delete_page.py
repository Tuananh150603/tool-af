"""Test xoa page chet: store.delete_page + man Page (Xvfb)."""
from pathlib import Path

import pytest

from gui.core import store
from gui.core.runlog import RunLog


def test_delete_page_chuyen_vao_pages_deleted(fake_tool_root):
    fx = fake_tool_root
    root = fx["root"]
    folder = "222222222222222_Đêm_Bình_Yên"
    src = root / "pages" / folder
    assert src.is_dir()
    dest = store.delete_page(root, folder)
    assert not src.exists()
    assert dest.parent == root / "pages_deleted"
    assert dest.name.startswith(folder + "_")
    # File trong page duoc giu nguyen
    assert (dest / "info.txt").is_file()
    assert (dest / "edited").is_dir()
    # Page bien khoi danh sach, page khac khong dong toi
    names = [p.name for p in store.list_page_dirs(root)]
    assert folder not in names
    assert "111111111111111_Mua_sắm_quanh_năm" in names
    assert "333333333333333_HANZ" in names
    assert (root / "pages" / "111111111111111_Mua_sắm_quanh_năm" / "edited" / "vid1.mp4").is_file()


def test_delete_page_ten_sai_hoac_thieu_bao_loi(fake_tool_root):
    fx = fake_tool_root
    root = fx["root"]
    for bad in ("", ".", "..", "a/b", "a\\b", "khong-co-page-nay"):
        with pytest.raises(ValueError):
            store.delete_page(root, bad)
    # Khong co thu muc nao bi dong toi
    assert len(store.list_page_dirs(root)) == 3
    assert not (root / "pages_deleted").exists()


@pytest.fixture()
def tk_pages_view(fake_tool_root, tmp_path):
    """App that + man Page (pattern nhu test_upload_view.py)."""
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
    app.show_view("pages")
    app.update()
    yield app
    try:
        app.destroy()
    except Exception:
        pass


def _folders(view):
    return [r["folder"] for r in view._rows]


def test_nut_xoa_page_xac_nhan_roi_chuyen_vao_trash(tk_pages_view, monkeypatch):
    app = tk_pages_view
    view = app.views["pages"]
    assert len(view._rows) == 3
    folder = "222222222222222_Đêm_Bình_Yên"
    assert any(r["folder"] == folder for r in view._rows)
    # Nut Xoa page mau do (danger), co mat o tung dong
    row = [r for r in view._rows if r["folder"] == folder][0]
    assert row["delete_button"] is not None
    monkeypatch.setattr("tkinter.messagebox.askyesno", lambda *a, **k: True)
    view.on_delete_page(folder, "Đêm Bình Yên")
    app.update()
    root = Path(app.config.tool_root)
    assert not (root / "pages" / folder).exists()
    trashed = list((root / "pages_deleted").glob(folder + "_*"))
    assert len(trashed) == 1
    assert (trashed[0] / "info.txt").is_file()
    # Ghi su kien vao run-log + bang lam moi khong con page do
    events = [e for e in app.runlog.data["events"] if e.get("type") == "page_delete"]
    assert len(events) == 1
    assert events[0]["data"]["page"] == folder
    assert folder not in _folders(view)
    assert len(view._rows) == 2


def test_xoa_page_bam_huy_thi_khong_lam_gi(tk_pages_view):
    import tkinter.messagebox as mb
    app = tk_pages_view
    view = app.views["pages"]
    folder = "222222222222222_Đêm_Bình_Yên"
    real = mb.askyesno
    try:
        mb.askyesno = lambda *a, **k: False
        view.on_delete_page(folder, "Đêm Bình Yên")
    finally:
        mb.askyesno = real
    app.update()
    root = Path(app.config.tool_root)
    assert (root / "pages" / folder).is_dir()
    assert not (root / "pages_deleted").exists()
    assert not [e for e in app.runlog.data["events"] if e.get("type") == "page_delete"]
    assert folder in _folders(view)
