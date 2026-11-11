"""Test views/legacy_view.py — model + chuyen video vao pool (headless)."""
from gui.views.legacy_view import build_model, move_legacy_videos_to_pool


def test_build_model_fake(fake_tool_root):
    fx = fake_tool_root
    m = build_model(fx["root"])
    assert len(m["legacy"]) == 1
    assert m["legacy"][0]["folder"].startswith("333333333333333")


def test_move_legacy_videos_vao_pool(fake_tool_root):
    fx = fake_tool_root
    # Gan kenh cho p3 truoc (de biet copy vao kenh nao)
    (fx["p3"] / "source.txt").write_text(
        str(fx["pool"] / "999999999" / "视频") + "\n", encoding="utf-8")
    n, msg = move_legacy_videos_to_pool(fx["root"], fx["pool"],
                                        "333333333333333_HANZ")
    assert n == 2
    dest = fx["pool"] / "999999999" / "视频"
    assert (dest / "raw1.mp4").is_file()
    assert (dest / "raw2.mp4").is_file()
    # Chay lai: trung ten -> bo qua, khong copy them
    n2, _ = move_legacy_videos_to_pool(fx["root"], fx["pool"],
                                       "333333333333333_HANZ")
    assert n2 == 0


def test_move_khi_page_chua_gan_kenh(fake_tool_root):
    fx = fake_tool_root
    n, msg = move_legacy_videos_to_pool(fx["root"], fx["pool"],
                                        "333333333333333_HANZ")
    assert n == 0 and "chưa gắn kênh" in msg
