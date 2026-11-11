"""Test core/store.py — doc du lieu that (ten thu muc tieng Viet, BOM, ...)."""
from pathlib import Path

from gui.core import store


def test_list_page_dirs_tieng_viet(fake_tool_root):
    dirs = store.list_page_dirs(fake_tool_root["root"])
    names = [d.name for d in dirs]
    assert len(names) == 3
    assert any("Mua_sắm" in n for n in names)
    assert any("Đêm_Bình_Yên" in n for n in names)


def test_parse_info(fake_tool_root):
    info = store.parse_info(fake_tool_root["p1"])
    assert info["name"] == "Mua sắm quanh năm"
    assert info["id"] == "111111111111111"


def test_read_source_channel_chiu_bom(fake_tool_root):
    assert store.read_source_channel(fake_tool_root["p1"]) == "1083489147427179"
    assert store.read_source_channel(fake_tool_root["p2"]) is None


def test_read_source_path(fake_tool_root):
    raw = store.read_source_path(fake_tool_root["p1"])
    assert raw.endswith("1083489147427179\\视频")


def test_page_status(fake_tool_root):
    fx = fake_tool_root
    st = store.page_status(fx["root"], fx["pool"], fx["p1"])
    assert st["name"] == "Mua sắm quanh năm"
    assert st["waiting"] is False
    assert st["pool_count"] == 3
    assert st["edited_count"] == 2
    assert st["has_token"] is True
    assert st["niche"] == "mua sắm"
    st2 = store.page_status(fx["root"], fx["pool"], fx["p2"])
    assert st2["waiting"] is True
    assert st2["pool_count"] == 0
    assert st2["has_token"] is False


def test_all_page_status(fake_tool_root):
    all_st = store.all_page_status(fake_tool_root["root"], fake_tool_root["pool"])
    assert len(all_st) == 3


def test_list_pool_channels_bo_avatar(fake_tool_root):
    chans = store.list_pool_channels(fake_tool_root["pool"])
    ids = [c["id"] for c in chans]
    assert "1083489147427179" in ids
    assert "999999999" in ids
    assert "头像" not in ids
    assert [c for c in chans if c["id"] == "1083489147427179"][0]["video_count"] == 3


def test_channel_assignment(fake_tool_root):
    assign = store.channel_assignment(fake_tool_root["root"], fake_tool_root["pool"])
    assert assign["1083489147427179"].startswith("111111111111111")


def test_read_pool_map(fake_tool_root):
    rows = store.read_pool_map(fake_tool_root["root"])
    assert len(rows) == 3
    assert rows[0]["channel"] == "1083489147427179"
    assert rows[0]["count"] == 3
    assert rows[1]["waiting"] is True and rows[1]["channel"] is None


def test_extract_shopee_links(fake_tool_root):
    comments = store.load_text_lines(fake_tool_root["root"] / "comments.txt")
    counts = store.extract_shopee_links(comments)
    assert counts == {"https://s.shopee.vn/AAAA111": 2, "https://s.shopee.vn/BBBB222": 1}


def test_resolve_captions(fake_tool_root):
    fx = fake_tool_root
    shared, src = store.resolve_captions(fx["root"], fx["p1"], False)
    assert len(shared) == 3 and src == "chung"
    own, src = store.resolve_captions(fx["root"], fx["p1"], True)
    assert len(own) == 2 and src == "riêng của page"
    # page 2: khong co kho rieng, khong tag -> fallback kho chung
    fb, src = store.resolve_captions(fx["root"], fx["p2"], True)
    assert len(fb) == 3 and src.startswith("chung")
    # page 2 + tag pool
    store.write_niche(fx["p2"], "phong cảnh")
    pool_file = Path(fx["root"]) / "gui_data" / "caption_pools" / "phong cảnh.txt"
    store.save_text_lines(pool_file, ["Caption phong cảnh 1"])
    tag_caps, src = store.resolve_captions(fx["root"], fx["p2"], True)
    assert tag_caps == ["Caption phong cảnh 1"]


def test_save_load_text_lines_giu_tieng_viet(tmp_path):
    f = tmp_path / "a.txt"
    store.save_text_lines(f, ["Mua sắm quanh năm", "Đêm Bình Yên", ""])
    assert store.load_text_lines(f) == ["Mua sắm quanh năm", "Đêm Bình Yên"]


def test_list_bgm(fake_tool_root):
    assert store.list_bgm(fake_tool_root["root"]) == []


def test_scan_legacy(fake_tool_root):
    legacy = store.scan_legacy(fake_tool_root["root"])
    assert len(legacy) == 1
    row = legacy[0]
    assert row["folder"].startswith("333333333333333")
    assert row["non_edit"]["exists"] is True
    assert row["non_edit"]["video_count"] == 2
    assert row["non_edit"]["has_data_export"] is True
    assert row["pool_done"]["exists"] is True
    assert row["pool_done"]["lines"] == 3


def test_collect_legacy_videos(fake_tool_root):
    vids = store.collect_legacy_videos(fake_tool_root["p3"])
    assert len(vids) == 2
    assert all(v.suffix == ".mp4" for v in vids)


def test_real_repo_16_pages(real_repo_root):
    """Dashboard load duoc 16 page tu du lieu that trong repo."""
    all_st = store.all_page_status(real_repo_root, r"D:\Video Douyin Pool\data\关注")
    assert len(all_st) == 16
    linked = [s for s in all_st if not s["waiting"]]
    waiting = [s for s in all_st if s["waiting"]]
    assert len(linked) == 6
    assert len(waiting) == 10
    rows = store.read_pool_map(real_repo_root)
    assert len(rows) == 16
    total = sum(r["count"] for r in rows if not r["waiting"])
    assert total == 1375
