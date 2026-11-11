"""Test adapters/pool_adapter.py — dry-run khong ghi file, FIFO, STRICT 1-1."""
from gui.adapters import pool_adapter


def test_read_source_channel_duong_dan_windows_tren_linux(fake_tool_root):
    """Hoi quy: source.txt ghi duong dan Windows phai doc dung ca tren Linux."""
    import sys
    sys.path.insert(0, str(fake_tool_root["root"]))
    import link_pool
    link_pool.PAGES_DIR = str(fake_tool_root["root"] / "pages")
    assert link_pool.read_source_channel(
        "111111111111111_Mua_sắm_quanh_năm") == "1083489147427179"


def test_preview_giu_map_cu(fake_tool_root):
    """Preview phai GIU map cu hop le (khong phai gan lai FIFO)."""
    fx = fake_tool_root
    kept, waiting, free_left, counts = pool_adapter.preview(fx["root"], fx["pool"])
    assert kept["111111111111111_Mua_sắm_quanh_năm"] == "1083489147427179"
    # p1 giu kenh cu nen kenh trong chi con 999999999 -> p2 (alphabet truoc) nhan
    assert kept["222222222222222_Đêm_Bình_Yên"] == "999999999"
    assert waiting == ["333333333333333_HANZ"]


def test_preview_dry_run_khong_ghi_file(fake_tool_root):
    fx = fake_tool_root
    before = (fx["p2"] / "source.txt").exists()
    kept, waiting, free_left, counts = pool_adapter.preview(fx["root"], fx["pool"])
    # p1 giu kenh cu; p2 (alphabet truoc p3) duoc gán kenh trong 999999999
    assert kept["111111111111111_Mua_sắm_quanh_năm"] == "1083489147427179"
    assert kept["222222222222222_Đêm_Bình_Yên"] == "999999999"
    assert waiting == ["333333333333333_HANZ"]
    assert free_left == []
    assert counts["1083489147427179"] == 3
    # dry-run: KHONG ghi file
    assert (fx["p2"] / "source.txt").exists() is before
    assert (fx["root"] / "pool_map.txt").read_text(encoding="utf-8").count("WAITING") == 2


def test_apply_ghi_that(fake_tool_root):
    fx = fake_tool_root
    kept, waiting, free_left, counts = pool_adapter.apply(fx["root"], fx["pool"])
    assert (fx["p2"] / "source.txt").is_file()
    assert "999999999" in (fx["p2"] / "source.txt").read_text(encoding="utf-8")
    text = (fx["root"] / "pool_map.txt").read_text(encoding="utf-8")
    assert "222222222222222_Đêm_Bình_Yên | 999999999" in text
    assert text.count("WAITING") == 1


def test_assign_chan_kenh_trung(fake_tool_root):
    fx = fake_tool_root
    ok, msg = pool_adapter.assign(fx["root"], fx["pool"],
                                  "222222222222222_Đêm_Bình_Yên", "1083489147427179")
    assert ok is False and "STRICT 1-1" in msg
    assert not (fx["p2"] / "source.txt").exists()


def test_assign_va_unassign(fake_tool_root):
    fx = fake_tool_root
    ok, msg = pool_adapter.assign(fx["root"], fx["pool"],
                                  "222222222222222_Đêm_Bình_Yên", "999999999")
    assert ok is True
    assert (fx["p2"] / "source.txt").is_file()
    assert pool_adapter.unassign(fx["root"], "222222222222222_Đêm_Bình_Yên") is True
    assert not (fx["p2"] / "source.txt").exists()
    assert pool_adapter.unassign(fx["root"], "222222222222222_Đêm_Bình_Yên") is False


def test_assign_kenh_khong_ton_tai(fake_tool_root):
    fx = fake_tool_root
    ok, _ = pool_adapter.assign(fx["root"], fx["pool"],
                                "222222222222222_Đêm_Bình_Yên", "000000")
    assert ok is False


def test_dry_run_link_pool_cli_goc_khong_ghi_file(real_repo_root):
    """Duong chay demo-critical: link_pool.py --dry-run tren repo that."""
    import subprocess
    import sys
    before = (real_repo_root / "pool_map.txt").read_bytes()
    r = subprocess.run([sys.executable, "link_pool.py", "--dry-run"],
                       cwd=str(real_repo_root), capture_output=True, text=True, timeout=60)
    assert r.returncode == 0
    assert "DRY-RUN" in r.stdout
    assert (real_repo_root / "pool_map.txt").read_bytes() == before
