"""Adapter mong cho Uploadvideo_multipage.py goc + dieu phoi dot upload.

An toan (mac dinh BAT, theo cai dat):
- Dung TOAN BO dot chay khi Facebook tra checkpoint / khoa / 429 / token
  het han; ghi su kien vao run-log + dat backoff (voi 429); KHONG tu chay
  lai — chi chay tiep khi Han bam tay.
- Gioi han video/ngay: mac dinh 1 video/page/ngay (nhip cua Han).
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


def run_upload_pages(tool_root, pages, opts, runlog, run_id, ctx, caption_resolver):
    """Dieu phoi dot upload nhieu page.
    pages: [{id, name, folder, dir, token}] (token da lam moi truoc).
    opts: gap, comment_delay, big_first, shuffle, cap_enabled, cap_per_page,
          stop_on_checkpoint, backoff_minutes, manual_files {folder: path}, rng.
    caption_resolver(page_dir) -> (captions, comments, nguon_caption).
    Tra summary dict (co stopped/stop_kind/stop_page/stop_video khi dung khan)."""
    import random
    m = load(tool_root)
    rng = opts.get("rng") or random
    gap = int(opts.get("gap", 10))
    comment_delay = int(opts.get("comment_delay", 15))
    big_first = bool(opts.get("big_first", False))
    shuffle = bool(opts.get("shuffle", True))
    cap_enabled = bool(opts.get("cap_enabled", True))
    cap_per_page = int(opts.get("cap_per_page", 1))
    stop_on_checkpoint = bool(opts.get("stop_on_checkpoint", True))
    backoff_minutes = int(opts.get("backoff_minutes", 15))
    manual_files = opts.get("manual_files") or {}
    comments_all = store.load_text_lines(Path(tool_root) / "comments.txt")

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

    for page in pages:
        if stopped or ctx.is_stopped():
            break
        vdir = Path(page["dir"]) / "edited"
        vids = [str(p) for p in store.list_videos(vdir)]
        if not vids and manual_files.get(page["folder"]):
            manual = manual_files[page["folder"]]
            if os.path.isfile(manual):
                vids = [manual]
                ctx.log(f"[{page['name']}] edited/ trống — dùng file nhập tay: {Path(manual).name}")
        if not vids:
            ctx.log(f"[{page['name']}] Không có video trong edited/ — bỏ qua page.")
            continue
        if shuffle:
            rng.shuffle(vids)
        captions, comments, cap_src = caption_resolver(page["dir"])
        captions = captions or store.load_text_lines(Path(tool_root) / "captions.txt")
        comments = comments or comments_all
        for i, vp in enumerate(vids, 1):
            if stopped or ctx.is_stopped():
                break
            total += 1
            ctx.progress(total - 1, None, f"Đang upload {Path(vp).name} ({page['name']})")
            fh = file_hash(vp)
            if runlog.is_file_uploaded(fh):
                skipped += 1
                ctx.log(f"[BỎ QUA] {Path(vp).name}: đã đăng rồi (chống trùng).")
                runlog.record_upload(run_id, page["id"], page["folder"], vp, fh,
                                    "", "", "", "skipped_dup")
                continue
            if cap_enabled and runlog.uploads_today(page["id"]) >= cap_per_page:
                skipped += 1
                ctx.log(f"[BỎ QUA] {page['name']}: đã đủ {cap_per_page} video hôm nay.")
                runlog.record_upload(run_id, page["id"], page["folder"], vp, fh,
                                    "", "", "", "skipped_cap")
                break  # het tran ngay cua page nay -> sang page khac
            cap = rng.choice(captions) if captions else ""
            cmt = rng.choice(comments) if comments else ""
            ctx.log(f"[{page['name']}] ({i}/{len(vids)}) {Path(vp).name} — caption: {cap[:60]}")
            runlog.record_upload(run_id, page["id"], page["folder"], vp, fh,
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
                ctx.log(f"[!] Upload thất bại: {Path(vp).name}")
            if kind and should_stop(kind, stop_on_checkpoint):
                _stop(kind, page, vp, getattr(m, "LAST_API_ERROR", None))
                break
            if i < len(vids) and gap > 0:
                if not ctx.sleep(gap):
                    stopped = True
                    ctx.log("[DỪNG] Người dùng dừng trong lúc nghỉ giữa video.")
                    break
    return {"total": total, "ok": ok, "failed": failed, "skipped": skipped,
            "stopped": stopped or ctx.is_stopped(),
            "stop_kind": stop_info["kind"], "stop_page": stop_info["page"],
            "stop_video": stop_info["video"], "run_id": run_id}
