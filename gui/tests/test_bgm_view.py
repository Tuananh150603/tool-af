"""Test views/bgm_view.py — model (headless)."""
from gui.core.config import Config
from gui.views.bgm_view import build_model


def test_build_model_trong(fake_tool_root, tmp_path):
    fx = fake_tool_root
    cfg = Config(path=tmp_path / "gui_config.json")
    m = build_model(fx["root"], cfg)
    assert m["files"] == []
    assert m["use_bgm"] is True
    assert m["bgm_vol"] == 0.18


def test_build_model_co_file(fake_tool_root, tmp_path):
    fx = fake_tool_root
    bgm = fx["root"] / "video_processing" / "bgm"
    (bgm / "nhac1.mp3").write_bytes(b"x" * 2048)
    cfg = Config(path=tmp_path / "gui_config.json")
    m = build_model(fx["root"], cfg)
    assert len(m["files"]) == 1
    assert m["files"][0]["name"] == "nhac1.mp3"
