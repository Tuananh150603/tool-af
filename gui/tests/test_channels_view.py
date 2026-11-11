"""Test views/channels_view.py — model (headless)."""
from gui.views.channels_view import build_model


def test_build_model_fake(fake_tool_root):
    fx = fake_tool_root
    m = build_model(fx["root"], fx["pool"])
    assert len(m["channels"]) == 2
    by_id = {c["id"]: c for c in m["channels"]}
    assert by_id["1083489147427179"]["assigned_to"].startswith("111111111111111")
    assert by_id["1083489147427179"]["status"] == "linked"
    assert by_id["999999999"]["assigned_to"] is None
    assert by_id["999999999"]["status"] == "waiting"
    assert len(m["unassigned"]) == 1


def test_build_model_pool_trong(tmp_path):
    m = build_model(tmp_path, tmp_path / "khong-co")
    assert m["channels"] == [] and m["unassigned"] == []
