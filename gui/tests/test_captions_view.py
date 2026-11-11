"""Test views/captions_view.py — model (headless)."""
from gui.views.captions_view import build_model


def test_build_model_fake(fake_tool_root):
    fx = fake_tool_root
    m = build_model(fx["root"])
    assert len(m["captions"]) == 3
    assert len(m["comments"]) == 3
    assert m["links"] == {"https://s.shopee.vn/AAAA111": 2,
                          "https://s.shopee.vn/BBBB222": 1}
    by_folder = {p["folder"]: p for p in m["per_page"]}
    assert by_folder["111111111111111_Mua_sắm_quanh_năm"]["own_count"] == 2
    assert by_folder["111111111111111_Mua_sắm_quanh_năm"]["niche"] == "mua sắm"
    assert by_folder["222222222222222_Đêm_Bình_Yên"]["own_count"] == 0
