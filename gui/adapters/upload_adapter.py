"""Adapter mong cho Uploadvideo_multipage.py goc + dieu phoi dot upload.

An toan (mac dinh BAT, theo cai dat):
- Dung TOAN BO dot chay khi Facebook tra checkpoint / khoa / 429 / token
  het han; ghi su kien vao run-log + dat backoff (voi 429); KHONG tu chay
  lai — chi chay tiep khi Han bam tay.
- Chong trung: khong upload lai file da co fb_video_id trong run-log.
- Tiep tuc: ghi entry 'pending' truoc khi upload, cap nhat sau.
"""
import contextlib
import io
import os
from pathlib import Path

import requests

from gui.adapters._loader import load_script
from gui.core import store
from gui.core.runlog import file_hash
from gui.core.safety import (backoff_until, classify_fb_error, should_stop)


def load(tool_root):
    m = load_script(tool_root, "Uploadvideo_multipage.py",
                    ("clear_api_error", "fetch_pages", "setup_all_pages",
                     "list_local_pages", "up_simple", "up_resumable",
                     "comment"))
    root = str(Path(tool_root))
    m.BASE = root
    m.PAGES_DIR = str(Path(tool_root) / "pages")
    m.CAPF = str(Path(tool_root) / "captions.txt")
    m.CMTF = str(Path(tool_root) / "comments.txt")
    m.VDIR = str(Path(tool_root) / "videos")
    return m


class _LogWriter(io.TextIOBase):
    """Chuyen print() cua ham goc sang log cua GUI (theo dong)."""

    def __init__(self, log_fn):
        self.log_fn = log_fn
        self._buf = ""

    def write(self, s):
        self._buf += s
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            if line.strip():
                self.log_fn(line.rstrip())
        return len(s)

    def flush(self):
        if self._buf.strip():
            self.log_fn(self._buf.rstrip())
        self._buf = ""


def check_token(token, ver="v21.0"):
    """GET /me: (ok, ten_hien_thi, err_dict|None). Khong raise."""
    if not token or len(token.strip()) < 20:
        return False, "", {"code": None, "message": "Token trống hoặc quá ngắn"}
    try:
        r = requests.get(f"https://graph.facebook.com/{ver}/me",
                         params={"access_token": token.strip(), "fields": "id,name"},
                         timeout=20)
        j = r.json()
    except Exception as e:
        return False, "", {"code": None, "message": f"Lỗi kết nối: {e}"}
    if isinstance(j, dict) and "error" in j:
        err = j["error"] or {}
        return False, "", {"status": r.status_code, "code": err.get("code"),
                           "subcode": err.get("error_subcode"),
                           "message": str(err.get("message", ""))}
    if isinstance(j, dict) and "id" in j:
        return True, j.get("name", ""), None
    return False, "", {"code": None, "message": f"Phản hồi lạ: {str(j)[:200]}"}


def fetch_pages(tool_root, user_token):
    """(pages, err_dict|None) — dung ham goc fetch_pages."""
    m = load(tool_root)
    m.clear_api_error()
    pages = m.fetch_pages(user_token)
    return pages, getattr(m, "LAST_API_ERROR", None)


def fetch_live_page_ids(tool_root, user_token):
    """Set id cac page CON SONG theo /me/accounts, hoac None neu khong kiem
    tra duoc (khong co user token / mat mang / API loi / khong co page nao).
    Tra None de giu hanh vi cu — an toan: khong bo qua nham page song khi
    khong xac minh duoc."""
    if not user_token or len(str(user_token).strip()) < 20:
        return None
    try:
        pages, err = fetch_pages(tool_root, user_token)
    except Exception:
        return None
    if err or not isinstance(pages, list) or not pages:
        return None
    ids = {str(p.get("id")) for p in pages if isinstance(p, dict) and p.get("id")}
    return ids or None


def setup_pages(tool_root, user_token):
    """Quet page tu user token + tao thu muc page (ham goc setup_all_pages)."""
    m = load(tool_root)
    m.clear_api_error()
    pages = m.setup_all_pages(user_token)
    return pages, getattr(m, "LAST_API_ERROR", None)


def refresh_page_tokens(tool_root):
    """list_local_pages goc: fetch token page moi (neu co user token),
    fallback token.txt. Khong goi retrofit (khong xoa gi)."""
    m = load(tool_root)
    return m.list_local_pages()


def upload_one(m, page, video_path, caption, comment_text,
               big_first, comment_delay, ctx):
    """Upload 1 video (simple <-> resumable tu doi khi loi) + comment sau
    comment_delay giay (ngat duoc bang nut Dung).
    Tra (fb_video_id|None, kind|None, stopped_bool)."""
    pid, tok = page["id"], page["token"]
    title = (caption or "")[:90]
    m.clear_api_error()
    vid = None
    try:
        with contextlib.redirect_stdout(_LogWriter(ctx.log)):
            if big_first:
                vid = (m.up_resumable(pid, tok, video_path, title, caption)
                       or m.up_simple(pid, tok, video_path, title, caption))
            else:
                vid = (m.up_simple(pid, tok, video_path, title, caption)
                       or m.up_resumable(pid, tok, video_path, title, caption))
    except Exception as e:
        ctx.log(f"Lỗi upload: {e}")
    err = getattr(m, "LAST_API_ERROR", None)
    kind = classify_fb_error(err)
    if vid and comment_text:
        if not ctx.sleep(comment_delay):
            return vid, kind, True  # dung trong luc cho comment
        m.clear_api_error()
        try:
            with contextlib.redirect_stdout(_LogWriter(ctx.log)):
                m.comment(vid, tok, comment_text, delay=0)
        except Exception as e:
            ctx.log(f"Lỗi comment: {e}")
        err2 = getattr(m, "LAST_API_ERROR", None)
        kind2 = classify_fb_error(err2)
        if kind2:
            kind = kind2
    return vid, kind, False


def plan_upload_pages(tool_root, pages, opts, runlog, caption_resolver, log=None):
    """Lap ke hoach upload (KHONG upload, KHONG ghi run-log).

    Day la DUONG CHON DUY NHAT: run_upload_pages cung chay qua ham nay, nen
    video xem truoc thay dung la video se dang (cung thu tu, cung dedup).
    pages: [{id, name, folder, dir, token}].
    opts: gap, comment_delay, big_first, shuffle,
          manual_files {folder: path}, rng.
    caption_resolver(page_dir) -> (captions, comments, nguon_caption).
    opts co the co live_page_ids (set id page con song theo /me/accounts,
    hoac None): page khong nam trong set thi toan bo video cua no duoc
    ghi skipped ly do "dead_page" — de run bo qua ma khong dung dot.
    Tra {"items", "skipped", "queue", "total", "counts"}:
    - items: [{page_id, page_name, folder, page_dir, video_path, video_name,
               caption, comment, file_hash, caption_pool, comment_pool}]
    - skipped: [{page_id, page_name, folder, video_path, video_name,
                 reason ("dup"|"dead_page"), file_hash}]
    - queue: cac quyet dinh "upload"/"skip" theo dung thu tu run xu ly.
    - total: so video xet (items + skipped); counts: {"dup": n, "dead_page": n}.
    """
    import random
    rng = opts.get("rng") or random
    shuffle = bool(opts.get("shuffle", True))
    manual_files = opts.get("manual_files") or {}
    live_ids = opts.get("live_page_ids")  # set | None
    comments_all = store.load_text_lines(Path(tool_root) / "comments.txt")
    _log = log or (lambda *a, **k: None)

    items, skipped, queue = [], [], []
    for page in pages:
        vdir = Path(page["dir"]) / "edited"
        vids = [str(p) for p in store.list_videos(vdir)]
        if not vids and manual_files.get(page["folder"]):
            manual = manual_files[page["folder"]]
            if os.path.isfile(manual):
                vids = [manual]
                _log(f"[{page['name']}] edited/ trống — dùng file nhập tay: {Path(manual).name}")
        if not vids:
            _log(f"[{page['name']}] Không có video trong edited/ — bỏ qua page.")
            continue
        # Page chet (khong con trong /me/accounts): bo qua toan bo video,
        # khong thu upload — de run tiep tuc page khac, khong dung dot.
        if live_ids is not None and str(page["id"]) not in live_ids:
            for vp in vids:
                fh = file_hash(vp)
                entry = {"page_id": page["id"], "page_name": page["name"],
                         "folder": page["folder"], "video_path": vp,
                         "video_name": Path(vp).name, "file_hash": fh,
                         "reason": "dead_page"}
                skipped.append(entry)
                queue.append(dict(entry, action="skip"))
            continue
        if shuffle:
            rng.shuffle(vids)
        captions, comments, cap_src = caption_resolver(page["dir"])
        captions = captions or store.load_text_lines(Path(tool_root) / "captions.txt")
        comments = comments or comments_all
        for vp in vids:
            fh = file_hash(vp)
            base = {"page_id": page["id"], "page_name": page["name"],
                    "folder": page["folder"], "video_path": vp,
                    "video_name": Path(vp).name, "file_hash": fh}
            if runlog.is_file_uploaded(fh):
                entry = dict(base, reason="dup")
                skipped.append(entry)
                queue.append(dict(entry, action="skip"))
                continue
            cap = rng.choice(captions) if captions else ""
            cmt = rng.choice(comments) if comments else ""
            item = dict(base, page_dir=page["dir"], caption=cap, comment=cmt,
                        caption_pool=list(captions), comment_pool=list(comments))
            items.append(item)
            queue.append(dict(item, action="upload"))
    counts = {"dup": sum(1 for s in skipped if s["reason"] == "dup"),
              "dead_page": sum(1 for s in skipped if s["reason"] == "dead_page")}
    return {"items": items, "skipped": skipped, "queue": queue,
            "total": len(queue), "counts": counts}


def run_upload_pages(tool_root, pages, opts, runlog, run_id, ctx, caption_resolver,
                     overrides=None, skip=None, plan=None):
    """Dieu phoi dot upload nhieu page.
    pages: [{id, name, folder, dir, token}] (token da lam moi truoc).
    opts: gap, comment_delay, big_first, shuffle,
          stop_on_checkpoint, backoff_minutes, manual_files {folder: path}, rng,
          live_page_ids (set id page con song, hoac None = khong kiem tra).
    caption_resolver(page_dir) -> (captions, comments, nguon_caption).
    overrides: {(page_id, video_path): (caption, comment)} — dung dung gia tri
          da sua o man Xem truoc thay vi boc ngau nhien (mac dinh: khong co).
    skip: {(page_id, video_path)} — bo qua theo lua chon Xem truoc: khong
          upload, khong tinh loi, ghi run-log "skipped_user".
    plan: ke hoach co san tu plan_upload_pages (man Xem truoc truyen vao de
          thu tu + caption hien dung nhu da xem; mac dinh: lap moi).
    Page chet (khong nam trong live_page_ids) thi video cua no duoc ghi
    "skipped_dead_page" va dot chay TIEP TUC page khac — khong dung dot,
    khong dat backoff. Page song ma loi token/checkpoint/429 thi van DUNG
    dot nhu cu.
    Tra summary dict (co stopped/stop_kind/stop_page/stop_video khi dung khan)."""
    import random
    m = load(tool_root)
    rng = opts.get("rng") or random
    gap = int(opts.get("gap", 10))
    comment_delay = int(opts.get("comment_delay", 15))
    big_first = bool(opts.get("big_first", False))
    stop_on_checkpoint = bool(opts.get("stop_on_checkpoint", True))
    backoff_minutes = int(opts.get("backoff_minutes", 15))
    overrides = overrides or {}
    skip = skip or set()
    pages_by_id = {p["id"]: p for p in pages}

    total = ok = failed = skipped = 0
    stopped = False
    stop_info = {"kind": None, "page": None, "video": None}

    def _stop(kind, page, video, err):
        nonlocal stopped
        stopped = True
        stop_info.update({"kind": kind, "page": page.get("folder") if page else None,
                          "video": Path(video).name if video else None})
        from gui.core.safety import KIND_LABELS
        label = KIND_LABELS.get(kind, kind)
        msg = f"DỪNG ĐỢT CHẠY — {label} (page {page.get('name') if page else '?'}, video {stop_info['video']})"
        ctx.log(msg)
        runlog.record_event("safety_stop", msg,
                            {"kind": kind, "page_id": page.get("id") if page else None,
                             "video": stop_info["video"], "error": err or {}})
        if kind == "rate_limit":
            until = backoff_until(None, backoff_minutes)
            runlog.set_backoff(until.isoformat(timespec="seconds"))
            ctx.log(f"Đã đặt backoff đến {until.strftime('%H:%M %d/%m')} — không tự chạy lại.")

    # Canh bao neu dang trong thoi gian backoff (Han bam tay thi van cho chay)
    backoff_left = 0
    try:
        from gui.core.safety import backoff_remaining_seconds
        backoff_left = backoff_remaining_seconds(None, runlog.get_backoff())
    except Exception:
        backoff_left = 0
    if backoff_left > 0:
        ctx.log(f"[CẢNH BÁO] Đang trong thời gian backoff sau 429 "
                f"(còn {int(backoff_left // 60)} phút) — chạy theo lệnh tay.")

    if plan is None:
        plan = plan_upload_pages(tool_root, pages, opts, runlog, caption_resolver,
                                 log=ctx.log)
    queue = plan["queue"]
    dead_logged = set()  # chi log 1 dong cho moi page chet (khong spam theo video)
    for qi, entry in enumerate(queue):
        if stopped or ctx.is_stopped():
            break
        page = pages_by_id[entry["page_id"]]
        vp = entry["video_path"]
        fh = entry["file_hash"]
        key = (entry["page_id"], vp)
        total += 1
        if entry["action"] == "skip":
            skipped += 1
            if entry.get("reason") == "dead_page":
                if entry["page_id"] not in dead_logged:
                    dead_logged.add(entry["page_id"])
                    ctx.log(f"[BỎ QUA] {entry['page_name']}: page không còn trong tài khoản "
                            f"Facebook — bỏ qua, đợt chạy tiếp tục. Nên xóa page này khỏi "
                            f"tool (màn Page → Xóa page).")
                runlog.record_upload(run_id, entry["page_id"], entry["folder"], vp, fh,
                                    "", "", "", "skipped_dead_page")
            else:
                ctx.progress(total - 1, None, f"Đang upload {entry['video_name']} ({entry['page_name']})")
                ctx.log(f"[BỎ QUA] {entry['video_name']}: đã đăng rồi (chống trùng).")
                runlog.record_upload(run_id, entry["page_id"], entry["folder"], vp, fh,
                                    "", "", "", "skipped_dup")
            continue
        # Video trong ke hoach: co the bi bo qua / sua caption-comment o man Xem truoc
        cap, cmt = overrides.get(key, (entry["caption"], entry["comment"]))
        if key in skip:
            skipped += 1
            ctx.progress(total - 1, None, f"Bỏ qua {entry['video_name']} ({entry['page_name']})")
            ctx.log(f"[BỎ QUA] {entry['video_name']}: đã bỏ qua theo lựa chọn xem trước.")
            runlog.record_upload(run_id, entry["page_id"], entry["folder"], vp, fh,
                                cap, cmt, "", "skipped_user")
            continue
        ctx.progress(total - 1, None, f"Đang upload {entry['video_name']} ({entry['page_name']})")
        ctx.log(f"[{entry['page_name']}] {entry['video_name']} — caption: {cap[:60]}")
        runlog.record_upload(run_id, entry["page_id"], entry["folder"], vp, fh,
                            cap, cmt, "", "pending")
        vid, kind, was_stopped = upload_one(m, page, vp, cap, cmt,
                                            big_first, comment_delay, ctx)
        if was_stopped:
            stopped = True
            ctx.log("[DỪNG] Người dùng dừng trong lúc chờ comment.")
            break
        if vid:
            ok += 1
            runlog.mark_upload(run_id, fh, "ok", fb_video_id=vid)
            ctx.log(f"[+] Video ID: {vid}")
        else:
            failed += 1
            err = getattr(m, "LAST_API_ERROR", None)
            runlog.mark_upload(run_id, fh, "failed",
                              error=str((err or {}).get("message", "upload thất bại"))[:200],
                              kind=kind or "")
            ctx.log(f"[!] Upload thất bại: {entry['video_name']}")
        if kind and should_stop(kind, stop_on_checkpoint):
            _stop(kind, page, vp, getattr(m, "LAST_API_ERROR", None))
            break
        # Nghi giua cac video CUNG page (nhu cu: sau moi video tru video cuoi cua page)
        if gap > 0 and qi + 1 < len(queue) and queue[qi + 1]["page_id"] == entry["page_id"]:
            if not ctx.sleep(gap):
                stopped = True
                ctx.log("[DỪNG] Người dùng dừng trong lúc nghỉ giữa video.")
                break
    return {"total": total, "ok": ok, "failed": failed, "skipped": skipped,
            "stopped": stopped or ctx.is_stopped(),
            "stop_kind": stop_info["kind"], "stop_page": stop_info["page"],
            "stop_video": stop_info["video"], "run_id": run_id}
