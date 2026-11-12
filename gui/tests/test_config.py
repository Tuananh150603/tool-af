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
    cfg.set("rate_limit_backoff_minutes", 30)
    cfg.data["schedule"]["enabled"] = True
    cfg.data["schedule"]["time"] = "07:30"
    cfg.save()
    cfg2 = Config.load(tmp_path)
    assert cfg2.get("pool_root") == r"E:\Pool moi\data\关注"
    assert cfg2.get("user_token") == "TESTTOKEN_" + "y" * 60
    assert cfg2.get("rate_limit_backoff_minutes") == 30
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


# --- Hoi quy: .exe dong goi (PyInstaller onefile) phai tim dung tool root ---
# Truoc day default_tool_root() dung __file__ -> trong .exe __file__ nam trong
# thu muc tam _MEI (bi xoa khi thoat) nen app khong thay pages/ + token.
import sys
from pathlib import Path
from gui.core.config import default_tool_root


def _fake_frozen(monkeypatch, exe_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe_path), raising=False)


def test_frozen_exe_dat_trong_tool_root(monkeypatch, tmp_path):
    (tmp_path / "Uploadvideo_multipage.py").write_text("x", encoding="utf-8")
    (tmp_path / "pages").mkdir()
    exe = tmp_path / "ToolAF.exe"
    exe.write_text("fake exe", encoding="utf-8")
    _fake_frozen(monkeypatch, exe)
    assert default_tool_root() == str(tmp_path)


def test_frozen_exe_trong_gui_dist_di_nguoc_len_tim_tool_root(monkeypatch, tmp_path):
    (tmp_path / "Uploadvideo_multipage.py").write_text("x", encoding="utf-8")
    dist = tmp_path / "gui" / "dist"
    dist.mkdir(parents=True)
    exe = dist / "ToolAF.exe"
    exe.write_text("fake exe", encoding="utf-8")
    _fake_frozen(monkeypatch, exe)
    assert default_tool_root() == str(tmp_path)


def test_frozen_exe_khong_tim_thay_tool_root_tra_ve_thu_muc_exe(monkeypatch, tmp_path):
    exe = tmp_path / "ToolAF.exe"
    exe.write_text("fake exe", encoding="utf-8")
    _fake_frozen(monkeypatch, exe)
    assert default_tool_root() == str(tmp_path)


def test_load_ton_trong_tool_root_da_luu(tmp_path):
    import json
    root_a = tmp_path / "A"
    (root_a / "pages").mkdir(parents=True)
    root_b = tmp_path / "B"
    root_b.mkdir()
    (root_b / "gui_config.json").write_text(
        json.dumps({"tool_root": str(root_a)}), encoding="utf-8")
    cfg = Config.load(root_b)
    assert cfg.tool_root == str(root_a)


def test_save_ghi_vao_tool_root_moi(tmp_path):
    root_a = tmp_path / "A"
    root_a.mkdir()
    root_b = tmp_path / "B"
    root_b.mkdir()
    cfg = Config(path=root_a / "gui_config.json")
    cfg.set("tool_root", str(root_b))
    cfg.save()
    assert (root_b / "gui_config.json").is_file()
    cfg2 = Config.load(root_b)
    assert cfg2.tool_root == str(root_b)
