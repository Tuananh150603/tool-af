"""Test views/pool_view.py — model dry-run (headless)."""
from gui.views.pool_view import build_model


def test_build_model_fake(fake_tool_root):
    fx = fake_tool_root
    m = build_model(fx["root"], fx["pool"])
    assert m["kept"]["111111111111111_Mua_sắm_quanh_năm"] == "1083489147427179"
    assert m["kept"]["222222222222222_Đêm_Bình_Yên"] == "999999999"
    assert m["waiting"] == ["333333333333333_HANZ"]
    assert m["free_left"] == []
    assert len(m["pool_map"]) == 3


def test_build_model_real_repo(real_repo_root):
    """Dry-run tren repo that: 6 kenh, 10 page doi — khong ghi file."""
    import subprocess
    import sys
    before = (real_repo_root / "pool_map.txt").read_bytes()
    m = build_model(real_repo_root, r"D:\Video Douyin Pool\data\关注")
    # Pool Windows khong ton tai tren Linux -> khong co kenh trong, giu nguyen 0 map
    assert m["kept"] == {}
    assert len(m["waiting"]) == 16
    assert (real_repo_root / "pool_map.txt").read_bytes() == before
