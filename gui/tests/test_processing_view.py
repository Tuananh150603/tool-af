"""Test views/processing_view.py — model (headless)."""
from gui.views.processing_view import build_model


def test_build_model_fake(fake_tool_root):
    fx = fake_tool_root
    m = build_model(fx["root"], fx["pool"])
    assert m["total_edited"] == 2
    by_id = {p["folder"]: p for p in m["pages"]}
    # p1 source.txt tro duong dan Windows (khong ton tai tren Linux) -> pool 0
    assert by_id["111111111111111_Mua_sắm_quanh_năm"]["edited_count"] == 2
    assert by_id["222222222222222_Đêm_Bình_Yên"]["waiting"] is True


def test_build_model_pool_linux(fake_tool_root):
    """Khi source.txt tro toi pool Linux that thi dem dung so video."""
    fx = fake_tool_root
    pool_vdir = fx["pool"] / "1083489147427179" / "视频"
    (fx["p1"] / "source.txt").write_text(str(pool_vdir) + "\n", encoding="utf-8")
    m = build_model(fx["root"], fx["pool"])
    assert m["total_pool"] == 3
