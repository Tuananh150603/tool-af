"""Adapter mong cho video_processing/Processing.py goc.

- Dung ham goc read_source_dir / list_videos / process_one (khong qua
  pages_info de tranh fetch token mang khi chi can trang thai).
- Mac dinh KHONG xoa video goc sau edit (khac CLI goc): chong trung bang
  run-log (hash nguon). Chi xoa khi Han bat tuy chon trong Cai dat.
"""
import os
import sys
from pathlib import Path

from gui.core import store
from gui.core.pipeline import effective_params
from gui.core.runlog import file_hash


def load(tool_root, ffmpeg_bin=""):
    root = str(Path(tool_root))
    vp = str(Path(tool_root) / "video_processing")
    for p in (vp, root):
        if p not in sys.path:
            sys.path.insert(0, p)
    import Processing
    Processing.PAGES_DIR = str(Path(tool_root) / "pages")
    Processing.BGM_DIR = str(Path(tool_root) / "video_processing" / "bgm")
    if ffmpeg_bin:
        Processing.FFMPEG = ffmpeg_bin
    return Processing


def page_dicts(tool_root):
    out = []
    for d in store.list_page_dirs(tool_root):
        info = store.parse_info(d)
        out.append({"id": info["id"], "name": info["name"],
                    "folder": d.name, "dir": str(d)})
    return out


def collect_round_robin(tool_root, target_folders=None, per_page=1):
    """[(page_dict, src_path)] — moi page toi da per_page video (xoay vong)."""
    m = load(tool_root)
    items = []
    for pg in page_dicts(tool_root):
        if target_folders is not None and pg["folder"] not in target_folders:
            continue
        sdir = m.read_source_dir(pg["dir"])
        pool_list = []
        if sdir:
            if os.path.isfile(sdir) and sdir.lower().endswith(store.VIDEO_EXTS):
                pool_list = [sdir]
            elif os.path.isdir(sdir):
                pool_list = m.list_videos(sdir)
        for v in pool_list[:max(1, per_page)]:
            items.append((pg, v))
    return items


def edit_one(tool_root, page, src, params, delete_source, runlog, run_id, log):
    """Edit 1 video bang ham goc process_one. Tra (ok, out_path, error).
    error == 'da-edit' nghia la video nay da edit roi (bo qua, khong loi)."""
    m = load(tool_root)
    src_hash = file_hash(src)
    if runlog.is_source_edited(src_hash):
        log(f"[BỎ QUA] {Path(src).name}: đã edit rồi (chống trùng bằng run-log)")
        return False, "", "da-edit"
    edited_dir = Path(page["dir"]) / "edited"
    edited_dir.mkdir(parents=True, exist_ok=True)
    try:
        out = m.process_one(str(src), str(edited_dir), params=params)
    except Exception as e:
        runlog.record_edit(run_id, page["id"], page["folder"], src, src_hash,
                           "", params, "failed", str(e)[-400:])
        return False, "", str(e)
    runlog.record_edit(run_id, page["id"], page["folder"], src, src_hash,
                       out, params, "ok")
    if delete_source:
        try:
            os.remove(src)
            log(f"  (đã xóa nguồn theo tùy chọn: {Path(src).name})")
        except Exception as e:
            log(f"[!] Không xóa được nguồn {src}: {e}")
    return True, out, ""


def run_edit_round(tool_root, target_folders, per_page, base_params,
                   jitter_enabled, jitter_cfg, delete_source,
                   runlog, run_id, ctx):
    """Chay 1 luot edit xoay vong. ctx: log/progress/is_stopped/rng.
    Tra summary {total, ok, failed, skipped, stopped}."""
    import random
    rng = getattr(ctx, "rng", None) or random
    items = collect_round_robin(tool_root, target_folders, per_page)
    total = len(items)
    ok = failed = skipped = 0
    for i, (pg, src) in enumerate(items, 1):
        if ctx.is_stopped():
            ctx.log("[DỪNG] Người dùng dừng đợt edit.")
            break
        params = effective_params(base_params, jitter_enabled, jitter_cfg, rng=rng)
        ctx.progress(i - 1, total, f"Đang edit {i}/{total}: {Path(src).name}")
        ctx.log(f"[{i}/{total}] {pg['folder']}: {Path(src).name} "
                f"(speed={params.get('speed')}, contrast={params.get('contrast')})")
        good, out, err = edit_one(tool_root, pg, src, params, delete_source,
                                  runlog, run_id, ctx.log)
        if good:
            ok += 1
        elif err == "da-edit":
            skipped += 1
        else:
            failed += 1
            ctx.log(f"  LỖI: {str(err)[-200:]}")
        ctx.progress(i, total, f"Xong {i}/{total}")
    return {"total": total, "ok": ok, "failed": failed, "skipped": skipped,
            "stopped": ctx.is_stopped()}
