"""Link pool Douyin -> pages/*/source.txt (STRICT 1-1, khong share kenh).
- Pool: D:\\Video Douyin Pool\\data\\关注 , moi ID 1 folder video: <ID>\\视频.
- Quy tac: 1 page = 1 kenh duy nhat, 1 kenh chi giao cho 1 page.
- Giu nguyen map cu hop le. Page thieu kenh (moi) xep hang doi (FIFO alphabet).
- Khi co kenh moi duoc them vao pool: lan chay tool ke tiep tu dong gan kenh
  trong cho page dang doi (theo thu tu alphabet), khong can lam tay.
- Page doi se khong co source.txt (Processing tu bo qua).
Chay tay: python link_pool.py [--dry-run]
"""
import os, sys, re
POOL_BASE = r"D:\Video Douyin Pool\data\关注"
BASE = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(BASE, "pages")
VIDEO_SUB = "视频"
SKIP = {"头像"}
EXTS = (".mp4", ".mov", ".mkv", ".avi")

def list_pool_ids():
    if not os.path.isdir(POOL_BASE):
        return []
    return sorted([d for d in os.listdir(POOL_BASE) if os.path.isdir(os.path.join(POOL_BASE, d)) and d not in SKIP])

def list_pages():
    if not os.path.isdir(PAGES_DIR):
        return []
    return sorted([d for d in os.listdir(PAGES_DIR) if os.path.isdir(os.path.join(PAGES_DIR, d))])

def count_videos(folder):
    if not os.path.isdir(folder):
        return 0
    try:
        return len([f for f in os.listdir(folder) if f.lower().endswith(EXTS) and os.path.isfile(os.path.join(folder, f))])
    except Exception:
        return 0

def read_source_channel(pg):
    sf = os.path.join(PAGES_DIR, pg, "source.txt")
    if not os.path.isfile(sf):
        return None
    try:
        for raw in open(sf, encoding="utf-8-sig"):
            l = raw.strip().strip('"').strip("'")
            if not l or l.startswith("#"):
                continue
            # Tach ca '\' (Windows) va '/' de doc duoc source.txt Windows
            # tren moi he dieu hanh (truoc day chi tach os.sep nen tren
            # Linux doc sai duong dan D:\... thanh 1 chuoi duy nhat).
            parts = [p for p in re.split(r"[\\/]+", l) if p]
            cid = parts[-2] if len(parts) >= 2 and parts[-1] == VIDEO_SUB else parts[-1]
            return cid if cid else None
    except Exception:
        return None
    return None

def write_source(pg, cid):
    vdir = os.path.join(POOL_BASE, cid, VIDEO_SUB)
    open(os.path.join(PAGES_DIR, pg, "source.txt"), "w", encoding="utf-8").write(vdir + "\n")
    return vdir

def auto_link(dry=False):
    """Giu map cu hop le + tu gan kenh trong cho page doi. Tra (map, doi, kenh_trong)."""
    pool_ids = list_pool_ids()
    pages = list_pages()
    counts = {c: count_videos(os.path.join(POOL_BASE, c, VIDEO_SUB)) for c in pool_ids}
    cur = {}
    for pg in pages:
        cid = read_source_channel(pg)
        if cid:
            cur[pg] = cid
    # loc map cu: kenh phai con ton tai + co folder video + khong trung
    kept, seen = {}, set()
    for pg in sorted(cur):
        cid = cur[pg]
        vdir = os.path.join(POOL_BASE, cid, VIDEO_SUB)
        if cid not in pool_ids or not os.path.isdir(vdir):
            continue  # kenh bi xoa -> page quay lai hang doi
        if cid in seen:
            continue  # trung kenh -> page sau ve hang doi
        kept[pg] = cid
        seen.add(cid)
    free = [c for c in pool_ids if c not in seen]
    waiting = [p for p in pages if p not in kept]
    # gan FIFO: page doi (alphabet) <- kenh trong (sorted)
    newly = {}
    for pg, cid in zip(waiting, sorted(free)):
        if not dry:
            write_source(pg, cid)
        kept[pg] = cid
        newly[pg] = cid
    still_waiting = [p for p in waiting if p not in newly]
    # xoa source.txt rac cua page doi (tranh Processing keo nham kenh trung/xoa)
    if not dry:
        for pg in still_waiting:
            sf = os.path.join(PAGES_DIR, pg, "source.txt")
            cid = cur.get(pg)
            # chi xoa neu file dang tro toi kenh trung / kenh da mat
            if os.path.isfile(sf) and (cid in seen and kept.get(pg) != cid or (cid and cid not in pool_ids)):
                try:
                    os.remove(sf)
                except Exception:
                    pass
        mf = os.path.join(BASE, "pool_map.txt")
        lines = []
        for pg in sorted(kept):
            cid = kept[pg]
            lines.append(f"{pg} | {cid} | {os.path.join(POOL_BASE, cid, VIDEO_SUB)} | {counts.get(cid, 0)} video")
        for pg in sorted(still_waiting):
            lines.append(f"{pg} | WAITING | - | doi kenh moi")
        open(mf, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return kept, still_waiting, sorted(free)[len(newly):], counts

def main():
    dry = "--dry-run" in set(sys.argv[1:])
    pool_ids = list_pool_ids()
    pages = list_pages()
    print(f"[+] Pool: {len(pool_ids)} kenh: {pool_ids}")
    print(f"[+] Pages: {len(pages)} page")
    kept, waiting, free_left, counts = auto_link(dry=dry)
    print(f"[+] Da gan 1-1: {len([p for p in kept if p not in waiting])} page co kenh rieng")
    for pg in sorted(kept):
        print(f"  - {pg} <- {kept[pg]} ({counts.get(kept[pg], 0)} video)")
    if waiting:
        print(f"[!] {len(waiting)} page DOI kenh (thieu kenh, khong share): {waiting}")
        print("    -> them ID kenh moi vao data\\关注\\<ID>\\视频 roi chay lai tool se tu gan.")
    if free_left:
        print(f"[+] {len(free_left)} kenh trong chua dung: {free_left}")
    print("[DRY-RUN] chua ghi file." if dry else "[+] Da luu source.txt + pool_map.txt")

if __name__ == "__main__":
    main()
