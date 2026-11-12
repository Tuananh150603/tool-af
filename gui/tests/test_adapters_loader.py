"""Hoi quy: adapter phai load script goc tu tool root bang duong dan tuong minh.

Loi that gap 12/11: Han chi copy thu muc gui/ vao D:\\Tool AF\\, 3 script goc
van la ban thang 10/2026 (khong co clear_api_error, process_one khong co
tham so params) -> AttributeError GIUA CHUNG dot upload. Test cu chi load
script moi trong repo nen khong bat duoc.
"""
import shutil
from pathlib import Path

import pytest

from gui.adapters import pool_adapter, processing_adapter, upload_adapter
from gui.adapters._loader import load_script

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_load_3_script_moi_ok(fake_tool_root):
    root = fake_tool_root["root"]
    m_up = upload_adapter.load(root)
    assert hasattr(m_up, "clear_api_error")
    m_pool = pool_adapter._load(root)
    assert hasattr(m_pool, "auto_link")
    m_proc = processing_adapter.load(root)
    assert "params" in __import__("inspect").signature(m_proc.process_one).parameters


def test_upload_adapter_bao_loi_ro_rang_khi_script_cu(tmp_path):
    """Thieu clear_api_error -> RuntimeError noi ro, KHONG phai AttributeError."""
    root = tmp_path / "Tool AF"
    root.mkdir()
    stub = (
        "def fetch_pages(t):\n    return []\n"
        "def setup_all_pages(t):\n    return []\n"
        "def list_local_pages():\n    return []\n"
        "def up_simple(*a):\n    return None\n"
        "def up_resumable(*a):\n    return None\n"
        "def comment(*a):\n    return False\n"
    )
    (root / "Uploadvideo_multipage.py").write_text(stub, encoding="utf-8")
    with pytest.raises(RuntimeError) as e:
        upload_adapter.load(root)
    assert "clear_api_error" in str(e.value)
    assert "ban cu" in str(e.value)


def test_processing_adapter_bao_loi_khi_process_one_thieu_params(tmp_path):
    """Ban cu co process_one nhung khong co tham so params -> RuntimeError."""
    root = tmp_path / "Tool AF"
    vp = root / "video_processing"
    vp.mkdir(parents=True)
    stub = (
        "def process_one(src, out_dir, overwrite=False):\n    return out_dir\n"
        "def read_source_dir(d):\n    return None\n"
        "def list_videos(d):\n    return []\n"
    )
    (vp / "Processing.py").write_text(stub, encoding="utf-8")
    with pytest.raises(RuntimeError) as e:
        processing_adapter.load(root)
    assert "params" in str(e.value)
    assert "ban cu" in str(e.value)


def test_load_script_thieu_file_bao_loi_ro_rang(tmp_path):
    with pytest.raises(RuntimeError) as e:
        load_script(tmp_path, "Uploadvideo_multipage.py", ("clear_api_error",))
    assert "Khong thay file" in str(e.value)


def test_load_lai_doc_file_moi_khong_dung_cache_cu(tmp_path):
    """Ghi de file giua 2 lan load -> lan 2 thay noi dung moi (chong cache)."""
    root = tmp_path / "Tool AF"
    root.mkdir()
    src = REPO_ROOT / "link_pool.py"
    shutil.copy(src, root / "link_pool.py")
    with open(root / "link_pool.py", "a", encoding="utf-8") as f:
        f.write("\nMARKER_V1 = 1\n")
    m1 = pool_adapter._load(root)
    assert m1.MARKER_V1 == 1
    with open(root / "link_pool.py", "a", encoding="utf-8") as f:
        f.write("MARKER_V1 = 2\n")
    m2 = pool_adapter._load(root)
    assert m2.MARKER_V1 == 2
