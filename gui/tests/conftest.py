"""Fixtures dung chung cho test headless cua GUI Tool AF.

Du lieu gia nam trong tmp_path (thu muc tieng Viet that, file that) — khong
dung du lieu that cua Han, khong dung token that.
"""
import sys
from pathlib import Path

# Cho phep `import gui.core...` (tu tool-af-clean) va `from core...` (tu gui/).
GUI_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = GUI_DIR.parent
for p in (str(REPO_ROOT), str(GUI_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest  # noqa: E402


@pytest.fixture()
def fake_tool_root(tmp_path):
    """Tool root gia: 3 page (1 da gan kenh, 1 WAITING, 1 co Non_edit legacy)."""
    root = tmp_path / "Tool AF"
    pages = root / "pages"
    # Page 1: da gan kenh, co token + 2 video edited
    p1 = pages / "111111111111111_Mua_sắm_quanh_năm"
    (p1 / "edited").mkdir(parents=True)
    (p1 / "info.txt").write_text(
        "Mua sắm quanh năm\nID: 111111111111111\nFolder: 111111111111111_Mua_sắm_quanh_năm\n",
        encoding="utf-8")
    (p1 / "token.txt").write_text("TESTTOKEN_" + "x" * 100, encoding="utf-8")
    (p1 / "source.txt").write_bytes(
        b"\xef\xbb\xbf" + "D:\\Video Douyin Pool\\data\\关注\\1083489147427179\\视频\n".encode("utf-8"))
    (p1 / "niche.txt").write_text("mua sắm", encoding="utf-8")
    (p1 / "edited" / "vid1.mp4").write_bytes(b"fake1")
    (p1 / "edited" / "vid2.mp4").write_bytes(b"fake2")
    (p1 / "captions_gui.txt").write_text("Caption riêng page mua sắm 1\nCaption riêng page mua sắm 2\n",
                                          encoding="utf-8")
    # Page 2: WAITING (khong co source.txt), khong token
    p2 = pages / "222222222222222_Đêm_Bình_Yên"
    (p2 / "edited").mkdir(parents=True)
    (p2 / "info.txt").write_text(
        "Đêm Bình Yên\nID: 222222222222222\nFolder: 222222222222222_Đêm_Bình_Yên\n",
        encoding="utf-8")
    # Page 3: legacy — con Non_edit/ + pool_done.txt
    p3 = pages / "333333333333333_HANZ"
    (p3 / "edited").mkdir(parents=True)
    (p3 / "Non_edit" / "data").mkdir(parents=True)
    (p3 / "info.txt").write_text("HANZ\nID: 333333333333333\nFolder: 333333333333333_HANZ\n",
                                  encoding="utf-8")
    (p3 / "Non_edit" / "raw1.mp4").write_bytes(b"raw1")
    (p3 / "Non_edit" / "raw2.mp4").write_bytes(b"raw2")
    (p3 / "pool_done.txt").write_text("aaa.mp4\nbbb.mp4\nccc.mp4\n", encoding="utf-8")
    # File goc
    (root / "captions.txt").write_text("Caption chung 1\nCaption chung 2\nCaption chung 3\n",
                                       encoding="utf-8")
    (root / "comments.txt").write_text(
        "Hay quá! Săn deal https://s.shopee.vn/AAAA111 #sale\n"
        "Đẹp! Mua ở đây https://s.shopee.vn/AAAA111 #xuhuong\n"
        "Chốt đơn https://s.shopee.vn/BBBB222 #deal\n",
        encoding="utf-8")
    (root / "pool_map.txt").write_text(
        "111111111111111_Mua_sắm_quanh_năm | 1083489147427179 | D:\\Video Douyin Pool\\data\\关注\\1083489147427179\\视频 | 3 video\n"
        "222222222222222_Đêm_Bình_Yên | WAITING | - | doi kenh moi\n"
        "333333333333333_HANZ | WAITING | - | doi kenh moi\n",
        encoding="utf-8")
    (root / "video_processing" / "bgm").mkdir(parents=True)
    # Copy 3 script goc vao tool root gia de adapter load duoc nhu that
    import shutil
    repo = Path(__file__).resolve().parents[2]
    shutil.copy(repo / "Uploadvideo_multipage.py", root / "Uploadvideo_multipage.py")
    shutil.copy(repo / "link_pool.py", root / "link_pool.py")
    (root / "video_processing").mkdir(exist_ok=True)
    shutil.copy(repo / "video_processing" / "Processing.py",
                root / "video_processing" / "Processing.py")
    # Pool gia
    pool = tmp_path / "pool"
    vdir = pool / "1083489147427179" / "视频"
    vdir.mkdir(parents=True)
    for i in range(3):
        (vdir / f"pool{i}.mp4").write_bytes(b"pool")
    (pool / "999999999" / "视频").mkdir(parents=True)
    (pool / "头像" / "a.jpg").parent.mkdir(parents=True, exist_ok=True)
    (pool / "头像" / "a.jpg").write_bytes(b"jpg")
    return {"root": root, "pool": pool, "p1": p1, "p2": p2, "p3": p3}


@pytest.fixture()
def real_repo_root():
    """Duong dan repo that (chi doc) — dung cho test Dashboard 16 page."""
    return REPO_ROOT
