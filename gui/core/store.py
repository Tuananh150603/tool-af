"""Doc/ghi du lieu that cua Tool AF (pages/, pool, captions, comments, bgm).

CHI dung Python (pathlib / os.listdir) de thao tac file — khong dung shell
glob, vi ten thu muc co dau tieng Viet (shell lam hong ten).
KHONG goi retrofit_all_pages() o day: GUI chi tao thu muc edited/ khi thieu,
khong xoa Non_edit/, videos/ hay captions.txt/comments.txt cua page.
"""
import re
import shutil
from datetime import datetime
from pathlib import Path

VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".avi")
BGM_EXTS = (".mp3", ".wav", ".m4a")
VIDEO_SUB = "视频"
POOL_SKIP_DIRS = {"头像"}
SHOPEE_RE = re.compile(r"https?://s\.shopee\.vn/[A-Za-z0-9]+")
GUI_CAPTIONS_FILENAME = "captions_gui.txt"   # kho caption rieng cua page
NICHE_FILENAME = "niche.txt"                # tag ngach cua page
POOL_DIRNAME = "caption_pools"              # gui_data/caption_pools/<tag>.txt


# ---------- Doc file text ----------
def load_text_lines(path):
    """Doc file text, chiu BOM (source.txt co BOM). Tra list dong khong rong."""
    try:
        lines = [l.strip() for l in Path(path).read_text(encoding="utf-8-sig").splitlines()]
        return [x for x in lines if x]
    except Exception:
        return []


def save_text_lines(path, lines):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(l.rstrip("\n") for l in lines if str(l).strip())
    path.write_text(text + ("\n" if text else ""), encoding="utf-8")


# ---------- Pages ----------
def list_page_dirs(tool_root):
    pages_dir = Path(tool_root) / "pages"
    if not pages_dir.is_dir():
        return []
    return sorted([p for p in pages_dir.iterdir() if p.is_dir()], key=lambda p: p.name)


def parse_info(page_dir):
    """info.txt: dong 1 = ten page, dong 'ID: <so>'. Tra {"name","id"}."""
    page_dir = Path(page_dir)
    name = page_dir.name
    pid = page_dir.name.split("_")[0]
    info = page_dir / "info.txt"
    if info.is_file():
        try:
            lines = [l.strip() for l in info.read_text(encoding="utf-8").splitlines() if l.strip()]
            if lines:
                name = lines[0]
            for l in lines:
                if l.startswith("ID:"):
                    pid = l[3:].strip()
        except Exception:
            pass
    return {"name": name, "id": pid}


def read_source_path(page_dir):
    """Duong dan pool trong source.txt (1 dong dau tien, chiu BOM)."""
    sf = Path(page_dir) / "source.txt"
    if not sf.is_file():
        return None
    for raw in load_text_lines(sf):
        if raw.startswith("#"):
            continue
        return raw.strip('"').strip("'")
    return None


def read_source_channel(page_dir):
    """ID kenh Douyin tu source.txt (phan tu ap chot truoc '视频')."""
    raw = read_source_path(page_dir)
    if not raw:
        return None
    parts = raw.replace("/", "\\").split("\\")
    if len(parts) >= 2 and parts[-1] == VIDEO_SUB:
        return parts[-2] or None
    return parts[-1] or None


def count_videos(folder):
    folder = Path(folder)
    if not folder.is_dir():
        return 0
    try:
        return len([f for f in folder.iterdir()
                    if f.is_file() and f.suffix.lower() in VIDEO_EXTS])
    except Exception:
        return 0


def list_videos(folder):
    folder = Path(folder)
    if not folder.is_dir():
        return []
    try:
        return sorted([f for f in folder.iterdir()
                       if f.is_file() and f.suffix.lower() in VIDEO_EXTS],
                      key=lambda p: p.name)
    except Exception:
        return []


def read_niche(page_dir):
    f = Path(page_dir) / NICHE_FILENAME
    if f.is_file():
        try:
            return f.read_text(encoding="utf-8").strip()
        except Exception:
            return ""
    return ""


def write_niche(page_dir, tag):
    f = Path(page_dir) / NICHE_FILENAME
    f.write_text((tag or "").strip(), encoding="utf-8")


def delete_page(tool_root, folder):
    """Chuyen thu muc pages/<folder> sang pages_deleted/<folder>_<YYYYMMDD-HHMMSS>.

    Chi DI CHUYEN, khong xoa vinh vien — muon khoi phuc thi chuyen thu muc
    do ve lai pages/. Vi page khong con trong pages/ nen tu bien khoi
    Dashboard, Upload, Link Pool, Xử lý video (cac man nay deu quet pages/).
    Tra duong dan dich (Path). Raise ValueError neu ten folder khong hop le
    hoac thu muc page khong ton tai."""
    if not folder or folder in (".", "..") or "/" in folder or "\\" in folder:
        raise ValueError(f"Tên page không hợp lệ: {folder!r}")
    src = Path(tool_root) / "pages" / folder
    if not src.is_dir():
        raise ValueError(f"Không tìm thấy page: {folder}")
    trash = Path(tool_root) / "pages_deleted"
    trash.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = trash / f"{folder}_{stamp}"
    i = 2
    while dest.exists():
        dest = trash / f"{folder}_{stamp}_{i}"
        i += 1
    shutil.move(str(src), str(dest))
    return dest


def page_status(tool_root, pool_root, page_dir):
    """Tong hop 1 page cho Dashboard: pool / edited / kenh / token."""
    page_dir = Path(page_dir)
    info = parse_info(page_dir)
    channel = read_source_channel(page_dir)
    pool_count = 0
    if channel:
        pool_count = count_videos(Path(pool_root) / channel / VIDEO_SUB)
    edited_dir = page_dir / "edited"
    edited_count = count_videos(edited_dir) if edited_dir.is_dir() else 0
    token_file = page_dir / "token.txt"
    has_token = token_file.is_file() and len(token_file.read_text(encoding="utf-8", errors="ignore").strip()) > 50
    return {
        "folder": page_dir.name,
        "dir": str(page_dir),
        "id": info["id"],
        "name": info["name"],
        "niche": read_niche(page_dir),
        "channel": channel,
        "waiting": channel is None,
        "pool_count": pool_count,
        "edited_count": edited_count,
        "has_token": has_token,
        "token_status": "unknown",  # unknown | alive | dead (cap nhat khi kiem tra)
    }


def all_page_status(tool_root, pool_root):
    return [page_status(tool_root, pool_root, d) for d in list_page_dirs(tool_root)]


def filter_pages(pages, query="", status_filter="all", token_status=None):
    """Loc page cho Dashboard/Page (muc tieu 50 page): tim theo ten/ID,
    loc theo trang thai (all/linked/waiting/token_dead).
    token_status: {page_id: 'alive'|'dead'|'unknown'} (neu co)."""
    q = (query or "").strip().lower()
    token_status = token_status or {}
    out = []
    for p in pages:
        if q and q not in p["name"].lower() and q not in p["id"] \
                and q not in p["folder"].lower():
            continue
        if status_filter == "linked" and p["waiting"]:
            continue
        if status_filter == "waiting" and not p["waiting"]:
            continue
        if status_filter == "token_dead" and token_status.get(p["id"]) != "dead":
            continue
        out.append(p)
    return out


# ---------- Pool Douyin ----------
def list_pool_channels(pool_root):
    """[{id, video_count}] — bo qua thu muc avatar 头像."""
    pool_root = Path(pool_root)
    if not pool_root.is_dir():
        return []
    out = []
    for d in sorted(pool_root.iterdir(), key=lambda p: p.name):
        if not d.is_dir() or d.name in POOL_SKIP_DIRS:
            continue
        out.append({"id": d.name, "video_count": count_videos(d / VIDEO_SUB)})
    return out


def channel_assignment(tool_root, pool_root):
    """Map kenh -> ten thu muc page dang dung (de biet kenh nao chua gan)."""
    assign = {}
    for p in list_page_dirs(tool_root):
        ch = read_source_channel(p)
        if ch:
            assign[ch] = p.name
    return assign


def read_pool_map(tool_root):
    """Parse pool_map.txt -> [{folder, channel|None, path, count, waiting}]."""
    rows = []
    f = Path(tool_root) / "pool_map.txt"
    if not f.is_file():
        return rows
    for line in load_text_lines(f):
        parts = [x.strip() for x in line.split("|")]
        if len(parts) < 4:
            continue
        folder, channel = parts[0], parts[1]
        waiting = channel.upper() == "WAITING"
        try:
            count = int(parts[3].split()[0])
        except Exception:
            count = 0
        rows.append({"folder": folder, "channel": None if waiting else channel,
                     "path": parts[2], "count": count, "waiting": waiting})
    return rows


# ---------- Caption / Comment / Shopee link ----------
def extract_shopee_links(comments):
    """Dem so lan xuat hien tung link Shopee trong kho comment."""
    counts = {}
    for c in comments:
        for link in SHOPEE_RE.findall(c):
            counts[link] = counts.get(link, 0) + 1
    return counts


def resolve_captions(tool_root, page_dir, per_page_enabled):
    """Kho caption dung cho 1 page (khi bat caption rieng theo page/ngach):
    1) file captions_gui.txt trong thu muc page
    2) gui_data/caption_pools/<tag ngach>.txt
    3) fallback kho chung captions.txt o goc.
    Khi tat tinh nang -> luon kho chung (dung hanh vi goc)."""
    shared = load_text_lines(Path(tool_root) / "captions.txt")
    if not per_page_enabled:
        return shared, "chung"
    page_dir = Path(page_dir)
    own = load_text_lines(page_dir / GUI_CAPTIONS_FILENAME)
    if own:
        return own, "riêng của page"
    tag = read_niche(page_dir)
    if tag:
        pool_file = Path(tool_root) / "gui_data" / POOL_DIRNAME / f"{tag}.txt"
        pooled = load_text_lines(pool_file)
        if pooled:
            return pooled, f"theo ngách '{tag}'"
    return shared, "chung (chưa có kho riêng)"


def list_caption_pools(tool_root):
    """Cac file kho caption theo tag trong gui_data/caption_pools/."""
    d = Path(tool_root) / "gui_data" / POOL_DIRNAME
    if not d.is_dir():
        return []
    return sorted([f.stem for f in d.iterdir() if f.is_file() and f.suffix == ".txt"])


# ---------- Nhac nen ----------
def list_bgm(tool_root):
    bgm_dir = Path(tool_root) / "video_processing" / "bgm"
    if not bgm_dir.is_dir():
        return []
    try:
        return sorted([f for f in bgm_dir.iterdir()
                       if f.is_file() and f.suffix.lower() in BGM_EXTS],
                      key=lambda p: p.name)
    except Exception:
        return []


# ---------- Du lieu cu (legacy) ----------
def scan_legacy(tool_root):
    """Liet ke Non_edit/ + pool_done.txt con sot o cac page.
    Tra [{folder, dir, non_edit: {exists, video_count, total_bytes, has_data_export},
          pool_done: {exists, lines}}]."""
    out = []
    for p in list_page_dirs(tool_root):
        ne = p / "Non_edit"
        ne_info = {"exists": False, "video_count": 0, "total_bytes": 0, "has_data_export": False}
        if ne.is_dir():
            ne_info["exists"] = True
            try:
                vids = [f for f in ne.rglob("*")
                        if f.is_file() and f.suffix.lower() in VIDEO_EXTS]
                ne_info["video_count"] = len(vids)
                ne_info["total_bytes"] = sum(f.stat().st_size for f in vids)
                ne_info["has_data_export"] = (ne / "data").is_dir()
            except Exception:
                pass
        pd = p / "pool_done.txt"
        pd_info = {"exists": pd.is_file(), "lines": len(load_text_lines(pd)) if pd.is_file() else 0}
        if ne_info["exists"] or pd_info["exists"]:
            out.append({"folder": p.name, "dir": str(p),
                        "non_edit": ne_info, "pool_done": pd_info})
    return out


def collect_legacy_videos(page_dir):
    """Tat ca file video trong Non_edit/ (de quy, ke ca trong data/ ... /视频/)."""
    ne = Path(page_dir) / "Non_edit"
    if not ne.is_dir():
        return []
    try:
        return sorted([f for f in ne.rglob("*")
                       if f.is_file() and f.suffix.lower() in VIDEO_EXTS],
                      key=lambda p: p.name)
    except Exception:
        return []
