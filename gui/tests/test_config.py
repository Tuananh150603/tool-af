"""Test core/config.py — luu/load + mac dinh an toan."""
from gui.core.config import Config, DEFAULTS


def test_defaults_giu_dung_hanh_vi_goc(tmp_path):
    cfg = Config(path=tmp_path / "gui_config.json")
    assert cfg.get("delete_source_after_edit") is False
    assert cfg.get("per_page_captions_enabled") is False
    assert cfg.get("jitter_enabled") is False
    assert cfg.pipeline_params["speed"] == 1.045
    assert cfg.pipeline_params["noise"] == 6


def test_defaults_an_toan_bat(tmp_path):
    cfg = Config(path=tmp_path / "gui_config.json")
    assert cfg.get("stop_on_checkpoint") is True
    assert cfg.get("daily_cap_enabled") is True
    assert cfg.get("daily_cap_per_page") == 1
    assert cfg.get("rate_limit_backoff_minutes") == 15


def test_config_khong_nhiem_defaults_chung(tmp_path):
    """Hoi quy: sua 1 Config khong duoc lam doi DEFAULTS / Config khac."""
    from gui.core.config import DEFAULTS
    c1 = Config(path=tmp_path / "a.json")
    c1.data["schedule"]["enabled"] = True
    c1.data["pipeline"]["speed"] = 9.99
    c2 = Config(path=tmp_path / "b.json")
    assert c2.data["schedule"]["enabled"] is False
    assert c2.pipeline_params["speed"] == 1.045
    assert DEFAULTS["schedule"]["enabled"] is False
    assert DEFAULTS["pipeline"]["speed"] == 1.045


def test_save_load_roundtrip(tmp_path):
    path = tmp_path / "gui_config.json"
    cfg = Config(path=path)
    cfg.set("pool_root", r"E:\Pool moi\data\关注")
    cfg.set("user_token", "TESTTOKEN_" + "y" * 60)
    cfg.set("daily_cap_per_page", 3)
    cfg.data["schedule"]["enabled"] = True
    cfg.data["schedule"]["time"] = "07:30"
    cfg.save()
    cfg2 = Config.load(tmp_path)
    assert cfg2.get("pool_root") == r"E:\Pool moi\data\关注"
    assert cfg2.get("user_token") == "TESTTOKEN_" + "y" * 60
    assert cfg2.get("daily_cap_per_page") == 3
    assert cfg2.data["schedule"]["enabled"] is True
    assert cfg2.data["schedule"]["time"] == "07:30"
    # gia tri khong doi van giu mac dinh
    assert cfg2.pipeline_params["speed"] == 1.045


def test_load_khi_chua_co_file(tmp_path):
    cfg = Config.load(tmp_path)
    assert cfg.tool_root == str(tmp_path)
    assert cfg.get("pool_root") == DEFAULTS["pool_root"]


def test_pipeline_params_merge(tmp_path):
    cfg = Config(path=tmp_path / "gui_config.json")
    cfg.data["pipeline"]["speed"] = 1.06
    assert cfg.pipeline_params["speed"] == 1.06
    assert cfg.pipeline_params["crop_w"] == 0.94  # phan con lai giu mac dinh
