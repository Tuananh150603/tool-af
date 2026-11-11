"""Test views/dashboard.py — model + loc (headless, du lieu that 16 page)."""
from gui.core.runlog import RunLog
from gui.views.dashboard import build_model


def test_build_model_fake(fake_tool_root, tmp_path):
    fx = fake_tool_root
    log = RunLog(tmp_path / "gui_runlog.json")
    m = build_model(fx["root"], fx["pool"], log)
    assert m["total_pages"] == 3
    assert m["linked"] == 1 and m["waiting"] == 2
    assert m["total_pool"] == 3  # tu pool_map.txt gia
    assert m["total_edited"] == 2
    assert m["today_uploads"] == 0
    assert m["backoff_until"] is None
    log.record_upload("r1", "111111111111111", "p1", "/e/a.mp4", "h1",
                      "", "", "5", "ok")
    m2 = build_model(fx["root"], fx["pool"], log)
    assert m2["today_uploads"] == 1
    assert m2["pages"][0]["today"] == 1


def test_build_model_real_repo_16_pages(real_repo_root, tmp_path):
    """Dashboard load duoc 16 page tu du lieu that trong repo."""
    log = RunLog(tmp_path / "gui_runlog.json")
    m = build_model(real_repo_root, r"D:\Video Douyin Pool\data\关注", log)
    assert m["total_pages"] == 16
    assert m["linked"] == 6
    assert m["waiting"] == 10
    assert m["total_pool"] == 1375
    assert m["total_edited"] == 0  # edited/ trong repo chi co .gitkeep


def test_loc_trang_thai_va_tim_kiem(fake_tool_root, tmp_path):
    from gui.core.store import filter_pages
    fx = fake_tool_root
    log = RunLog(tmp_path / "gui_runlog.json")
    m = build_model(fx["root"], fx["pool"], log)
    assert len(filter_pages(m["pages"], "", "all")) == 3
    assert len(filter_pages(m["pages"], "", "linked")) == 1
    assert len(filter_pages(m["pages"], "", "waiting")) == 2
    assert len(filter_pages(m["pages"], "mua sắm", "all")) == 1
    assert len(filter_pages(m["pages"], "111111111111111", "all")) == 1
    assert len(filter_pages(m["pages"], "khong-co", "all")) == 0
    assert len(filter_pages(m["pages"], "", "token_dead",
                           {"111111111111111": "dead"})) == 1
