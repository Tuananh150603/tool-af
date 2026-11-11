"""Test views/settings_view.py — model FFmpeg (headless)."""
from gui.core.config import Config
from gui.views.settings_view import build_model


def test_build_model_ffmpeg_he_thong(tmp_path):
    import shutil
    cfg = Config(path=tmp_path / "gui_config.json")
    m = build_model(cfg)
    if shutil.which("ffmpeg"):
        assert m["ffmpeg_source"] == "PATH"
        assert m["ffmpeg_version"].startswith("ffmpeg version")
    else:
        assert m["ffmpeg_source"] == "not-found"


def test_build_model_ffmpeg_chi_tay(tmp_path):
    cfg = Config(path=tmp_path / "gui_config.json")
    cfg.set("ffmpeg_bin", "/khong/tontai/ffmpeg")
    m = build_model(cfg)
    assert m["ffmpeg_source"] in ("PATH", "imageio-ffmpeg", "not-found")
    assert m["ffmpeg_path"] != "/khong/tontai/ffmpeg"
