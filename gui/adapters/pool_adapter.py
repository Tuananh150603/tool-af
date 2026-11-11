"""Adapter mong cho link_pool.py goc.

Chi doi POOL_BASE / PAGES_DIR / BASE theo cau hinh (duong dan Windows tren
may Han), KHONG doi logic gan 1-1 / FIFO / dry-run cua script goc.
"""
import sys
from pathlib import Path


def _load(tool_root):
    root = str(Path(tool_root))
    if root not in sys.path:
        sys.path.insert(0, root)
    import link_pool
    return link_pool


def apply_roots(tool_root, pool_root):
    m = _load(tool_root)
    m.POOL_BASE = str(pool_root)
    m.PAGES_DIR = str(Path(tool_root) / "pages")
    m.BASE = str(tool_root)
    return m


def preview(tool_root, pool_root):
    """Dry-run: (kept, waiting, free_left, counts). KHONG ghi file nao."""
    m = apply_roots(tool_root, pool_root)
    return m.auto_link(dry=True)


def apply(tool_root, pool_root):
    """Ghi that: source.txt moi + pool_map.txt."""
    m = apply_roots(tool_root, pool_root)
    return m.auto_link(dry=False)


def assign(tool_root, pool_root, page_folder, channel_id):
    """Gan tay 1 kenh cho 1 page, kiem tra STRICT 1-1. Tra (ok, message)."""
    m = apply_roots(tool_root, pool_root)
    pages = m.list_pages()
    if page_folder not in pages:
        return False, f"Không tìm thấy page {page_folder}"
    if channel_id not in m.list_pool_ids():
        return False, f"Kênh {channel_id} không có trong pool"
    for pg in pages:
        if pg != page_folder and m.read_source_channel(pg) == channel_id:
            return False, f"Kênh {channel_id} đang được page {pg} dùng (STRICT 1-1)"
    m.write_source(page_folder, channel_id)
    return True, f"Đã gán {page_folder} ← {channel_id}"


def unassign(tool_root, page_folder):
    """Go gan kenh cua 1 page (xoa source.txt). Tra True neu file ton tai."""
    p = Path(tool_root) / "pages" / page_folder / "source.txt"
    if p.is_file():
        p.unlink()
        return True
    return False
