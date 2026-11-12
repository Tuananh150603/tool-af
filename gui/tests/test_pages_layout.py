"""Hoi quy layout man Page: nut Xoa page phai thay duoc khong can keo ngang.

Bang cu rong hon cua so (~1258px trong viewport ~1026px) nen nut Xoa page
o cot cuoi bi ket ngoai man hinh, khong co thanh cuon ngang de keo toi.
Sau sua: nut Xoa page o cot 1 (ngay sau cot Page), bang gon lai, co thanh
cuon ngang lam luoi an toan.
"""
import pytest

from gui.core.config import Config
from gui.core.runlog import RunLog


@pytest.fixture()
def tk_pages_view(fake_tool_root, tmp_path):
    """App that + man Page (pattern nhu test_delete_page.py)."""
    try:
        from gui.app import App
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


def test_nut_xoa_page_nam_trong_vung_nhin_thay(tk_pages_view):
    """Nut Xoa page o cot 1, canh phai cua nut phai nam trong viewport
    cua bang — khong can keo ngang van bam duoc."""
    app = tk_pages_view
    view = app.views["pages"]
    view.update_idletasks()
    canvas = view._table_canvas
    assert view._rows, "bang Page phai co dong"
    x0 = canvas.winfo_rootx()
    x1 = x0 + canvas.winfo_width()
    for row in view._rows:
        btn = row["delete_button"]
        assert btn.grid_info()["column"] == 1, "nut Xoa page phai o cot 1"
        bx0 = btn.winfo_rootx()
        bx1 = bx0 + btn.winfo_width()
        assert bx0 >= x0, f"nut Xoa page cua {row['folder']} bi ket ben trai"
        assert bx1 <= x1, f"nut Xoa page cua {row['folder']} bi ket ben phai"


def test_bang_co_thanh_cuon_ngang(tk_pages_view):
    """Thanh cuon ngang ton tai va hien thi — luoi an toan khi cua so hep."""
    app = tk_pages_view
    view = app.views["pages"]
    view.update_idletasks()
    assert view._table_hbar is not None
    assert view._table_hbar.winfo_ismapped()
    # Canvas noi bang phai rong bang viewport (khong bi cat doc): chieu cao
    # canvas = dung chieu cao noi dung, tat ca dong deu nam trong vung cuon.
    assert view._table_canvas.winfo_height() >= view._table_inner.winfo_reqheight() - 2

