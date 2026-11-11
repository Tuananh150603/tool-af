"""Smoke test cua so chinh — chay tren Xvfb (xvfb-run -a pytest).
Neu khong co man hinh thi skip, khong fail.
"""
import pytest

from gui.core.config import Config
from gui.core.runlog import RunLog


@pytest.fixture()
def tk_app(fake_tool_root, tmp_path):
    try:
        from gui.app import App, VIEWS
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
    yield app, VIEWS
    try:
        app.destroy()
    except Exception:
        pass


def test_app_khoi_dong_du_12_man_hinh(tk_app):
    app, views = tk_app
    assert len(views) == 12
    assert app.current_view == "dashboard"
    assert "Tool AF" in app.title()
    assert len(app.views) == 12


def test_chuyen_qua_tat_ca_man_hinh_khong_loi(tk_app):
    app, views = tk_app
    for key, label, _cls in views:
        app.show_view(key)
        app.update()
        assert app.current_view == key
        assert app.views[key].winfo_ismapped()


def test_dashboard_hien_3_page_fake(tk_app):
    app, _ = tk_app
    app.show_view("dashboard")
    app.update()
    text = " ".join(w.cget("text") for w in app.views["dashboard"].cards_frame.winfo_children()
                    for w in w.winfo_children() if hasattr(w, "cget"))
    assert "3" in text  # the so lieu: 3 page


def test_moi_o_nhap_deu_hien_thi_duoc(tk_app):
    """Hoi quy: labeled_entry phai pack FRAME nhan (khong phai entry) —
    neu khong, o nhap ton tai nhung khong bao gio hien tren man hinh."""
    import customtkinter as ctk
    app, views = tk_app
    for key, _label, _cls in views:
        app.show_view(key)
        app.update()
        view = app.views[key]
        entries = [w for w in view.winfo_children() if isinstance(w, ctk.CTkEntry)]
        # quet de quy vi entry nam sau trong card/frame con
        stack = list(view.winfo_children())
        all_entries = []
        while stack:
            w = stack.pop()
            if isinstance(w, ctk.CTkEntry):
                all_entries.append(w)
            stack.extend(w.winfo_children())
        assert all(e.winfo_ismapped() for e in all_entries), \
            f"{key}: co o nhap ton tai nhung khong hien"


def test_log_va_banner(tk_app):
    app, _ = tk_app
    app.log("hello-log")
    app.update()
    assert "hello-log" in app.log_box.get("1.0", "end")
    app.show_safety_banner({"stop_kind": "checkpoint", "stop_page": "p1",
                            "stop_video": "v.mp4"})
    app.update()
    assert app.banner.winfo_ismapped()
    assert "checkpoint" in app.banner_label.cget("text").lower()
    app.hide_banner()
    app.update()
    assert not app.banner.winfo_ismapped()


def test_run_task_qua_runner(tk_app):
    import time
    app, _ = tk_app
    assert app.run_task("test-job", lambda ctx: {"ok": 1}) is True
    # doi task xong qua poll loop cua app
    end = time.monotonic() + 5
    while time.monotonic() < end:
        app.update()
        if not app.runner.running:
            break
        time.sleep(0.05)
    app._poll_runner()  # drain event 'done' ngay, khong doi tick after(100ms)
    app.update()
    assert "Xong: test-job" in app.log_box.get("1.0", "end")
