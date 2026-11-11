"""Test views/pages_view.py — model (headless)."""
from gui.views.pages_view import build_model


def test_build_model(fake_tool_root):
    fx = fake_tool_root
    m = build_model(fx["root"], fx["pool"])
    assert len(m["pages"]) == 3
    assert m["pages"][0]["token_status"] == "unknown"
    m2 = build_model(fx["root"], fx["pool"], {"111111111111111": "alive"})
    assert m2["pages"][0]["token_status"] == "alive"
