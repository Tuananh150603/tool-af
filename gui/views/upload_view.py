"""Upload: chon page, tuy chon (nghi/comment/resumable), tiep tuc dot do."""
import random
from pathlib import Path

import customtkinter as ctk

from gui.adapters import upload_adapter
from gui.core import store
from gui.theme import COLORS, PAD
from gui.views.common import (BaseView, clear_frame, data_table, ghost_button,
                              heading, labeled_entry, muted, primary_button,
                              title)


def build_model(tool_root, runlog):
    """Page + edited + da dang hom nay + dot chay do gan nhat (de Tiep tuc)."""
    pages = []
    for d in store.list_page_dirs(tool_root):
        info = store.parse_info(d)
        edited = store.list_videos(d / "edited")
        pages.append({"folder": d.name, "dir": str(d), "id": info["id"],
                      "name": info["name"], "edited_count": len(edited),
                      "today": runlog.uploads_today(info["id"])})
    last_pending_run = None
    for u in sorted(runlog.data["uploads"], key=lambda x: x.get("ts", ""), reverse=True):
        if u.get("status") in ("pending", "failed"):
            last_pending_run = u.get("run_id")
            break
    pending = runlog.pending_uploads(last_pending_run) if last_pending_run else []
    return {"pages": pages, "last_pending_run": last_pending_run,
            "pending": pending}


def resolve_captions_for_page(tool_root, per_page_enabled):
    def resolver(page_dir):
        caps, src = store.resolve_captions(tool_root, page_dir, per_page_enabled)
        cmts = store.load_text_lines(Path(tool_root) / "comments.txt")
        return caps, cmts, src
    return resolver


class UploadView(BaseView):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        title(self, "Upload lên Facebook").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        muted(self, "Caption + comment ngẫu nhiên cho mỗi video. Tự dừng khi gặp "
                     "checkpoint/rate-limit — không tự chạy lại.").pack(
            anchor="w", padx=PAD, pady=(0, PAD))
        opts = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        opts.pack(fill="x", padx=PAD, pady=(0, PAD))
        heading(opts, "Tùy chọn đợt upload").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        row = ctk.CTkFrame(opts, fg_color="transparent")
        row.pack(fill="x", padx=PAD, pady=(0, 4))
        gap_frame, self.gap_entry = labeled_entry(row, "Nghỉ giữa các video (giây)", "10")
        self.gap_entry.configure(width=120)
        gap_frame.pack(side="left", padx=(0, 10))
        delay_frame, self.delay_entry = labeled_entry(row, "Chờ trước khi comment (giây)", "15")
        self.delay_entry.configure(width=140)
        delay_frame.pack(side="left")
        self.big_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(row, text="File lớn: resumable trước",
                        variable=self.big_var, fg_color=COLORS["accent"],
                        text_color=COLORS["text"]).pack(side="left", padx=(16, 0), pady=(18, 0))
        self.shuffle_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(row, text="Xáo trộn thứ tự video",
                        variable=self.shuffle_var, fg_color=COLORS["accent"],
                        text_color=COLORS["text"]).pack(side="left", padx=(16, 0), pady=(18, 0))
        row2 = ctk.CTkFrame(opts, fg_color="transparent")
        row2.pack(fill="x", padx=PAD, pady=(0, PAD))
        self.target_var = ctk.StringVar(value="all")
        self.target_menu = ctk.CTkOptionMenu(row2, values=["all"], variable=self.target_var,
                                             fg_color=COLORS["bg_input"],
                                             button_color=COLORS["border"],
                                             text_color=COLORS["text"], width=320, height=36)
        self.target_menu.pack(side="left")
        manual_frame, self.manual_entry = labeled_entry(row2, "", "File nhập tay khi edited/ trống (tùy chọn)...")
        self.manual_entry.configure(width=300)
        manual_frame.pack(side="left")
        ghost_button(row2, "Duyệt file...", self.on_browse_manual).pack(side="left", padx=(10, 0))
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=PAD, pady=(0, PAD))
        primary_button(bar, "Upload", self.on_upload).pack(side="left")
        ghost_button(bar, "Tiếp tục đợt dở", self.on_resume).pack(side="left", padx=(10, 0))
        self.resume_label = muted(bar, "")
        self.resume_label.pack(side="left", padx=(10, 0))
        self.table_wrap = ctk.CTkFrame(self, fg_color="transparent")
        self.table_wrap.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))
        self._fill_opts()

    def _fill_opts(self):
        up = self.app.config.get("upload", {})
        self.gap_entry.delete(0, "end")
        self.gap_entry.insert(0, str(up.get("gap_seconds", 10)))
        self.delay_entry.delete(0, "end")
        self.delay_entry.insert(0, str(up.get("comment_delay", 15)))
        self.big_var.set(bool(up.get("big_first", False)))
        self.shuffle_var.set(bool(up.get("shuffle", True)))

    def _read_opts(self):
        try:
            gap = int(self.gap_entry.get() or 10)
        except Exception:
            gap = 10
        try:
            delay = int(self.delay_entry.get() or 15)
        except Exception:
            delay = 15
        return {"gap": gap, "comment_delay": delay,
                "big_first": self.big_var.get(), "shuffle": self.shuffle_var.get(),
                "cap_enabled": self.app.config.get("daily_cap_enabled", True),
                "cap_per_page": self.app.config.get("daily_cap_per_page", 1),
                "stop_on_checkpoint": self.app.config.get("stop_on_checkpoint", True),
                "backoff_minutes": self.app.config.get("rate_limit_backoff_minutes", 15),
                "manual_files": {}, "rng": random.Random()}

    def refresh(self):
        model = build_model(self.app.config.tool_root, self.app.runlog)
        folders = ["all"] + [p["folder"] for p in model["pages"]]
        self.target_menu.configure(values=folders)
        if model["last_pending_run"]:
            self.resume_label.configure(
                text=f"Đợt {model['last_pending_run']} còn {len(model['pending'])} video dở.")
        else:
            self.resume_label.configure(text="")
        clear_frame(self.table_wrap)
        cap = self.app.config.get("daily_cap_per_page", 1)
        heading(self.table_wrap, f"Video chờ upload (trần {cap} video/page/ngày)").pack(
            anchor="w", pady=(0, 8))
        cols = [("Page", 300), ("Video đã edit", 120), ("Đã đăng hôm nay", 140)]
        rows = [[p["name"], str(p["edited_count"]), f"{p['today']}/{cap}"]
                for p in model["pages"]]
        if rows:
            data_table(self.table_wrap, cols, rows).pack(fill="both", expand=True)
        else:
            muted(self.table_wrap, "Chưa có page nào.").pack(anchor="w")

    def _selected_pages(self):
        pages = upload_adapter.refresh_page_tokens(self.app.config.tool_root)
        target = self.target_var.get()
        if target != "all":
            pages = [p for p in pages if p["folder"] == target]
        manual = self.manual_entry.get().strip().strip('"')
        return pages, manual

    def on_browse_manual(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Chọn 1 file video để upload",
            filetypes=[("Video", "*.mp4 *.mov *.mkv *.avi")])
        if path:
            self.manual_entry.delete(0, "end")
            self.manual_entry.insert(0, path)

    def on_upload(self):
        pages, manual = self._selected_pages()
        if not pages:
            self.app.log("Chưa có page nào.")
            return
        opts = self._read_opts()
        if manual:
            for p in pages:
                opts["manual_files"][p["folder"]] = manual
        self.app.config.data["upload"] = {
            "gap_seconds": opts["gap"], "comment_delay": opts["comment_delay"],
            "big_first": opts["big_first"], "shuffle": opts["shuffle"]}
        self.app.config.save()
        self.app.run_task("upload", self._do_upload, pages, opts)

    def _do_upload(self, ctx, pages, opts):
        summary = upload_adapter.run_upload_pages(
            self.app.config.tool_root, pages, opts, self.app.runlog,
            ctx.run_id, ctx,
            resolve_captions_for_page(self.app.config.tool_root,
                                      self.app.config.get("per_page_captions_enabled", False)))
        ctx.log(f"TỔNG: {summary['ok']}/{summary['total']} video OK, "
                f"{summary['failed']} lỗi, {summary['skipped']} bỏ qua.")
        return summary

    def on_resume(self):
        model = build_model(self.app.config.tool_root, self.app.runlog)
        if not model["pending"]:
            self.app.log("Không có đợt dở nào để tiếp tục.")
            return
        self.app.log(f"Tiếp tục đợt {model['last_pending_run']}: "
                     f"{len(model['pending'])} video dở (chỉ chạy lại video chưa đăng).")
        self.on_upload()
