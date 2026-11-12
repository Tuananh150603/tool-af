"""Upload: chon page, tuy chon (nghi/comment/resumable), tiep tuc dot do.

Bang "Video chờ upload" sua duoc ngay trong bang: moi dong page co o nhap
Caption + Comment dien san gia tri planner se dung cho video tiep theo cua
page do, nut "Đổi" boc lai ngau nhien tu dung kho cua page do. Nut Upload
chay voi dung gia tri dang hien trong bang (qua overrides). Cot "Trạng thái"
luon ghi ro ly do dong nao khong dang duoc (video da dang roi / khong co
video); loi lap ke hoach hien ngay tren man hinh."""
import random
from pathlib import Path

import customtkinter as ctk

from gui.adapters import upload_adapter
from gui.core import store
from gui.theme import COLORS, FONTS, PAD, PAD_SMALL
from gui.views.common import (BaseView, clear_frame, ghost_button, heading,
                              labeled_entry, muted, primary_button, title)


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
        muted(self, "Sửa caption/comment ngay trong bảng rồi bấm Upload. "
                     "Tự dừng khi gặp checkpoint/rate-limit — không tự chạy lại.").pack(
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
        # Moi dong bang: {page_id, folder, video_path|None, item|None,
        #                cap_entry, cmt_entry, status}
        self._rows = []
        self._plan = None
        self._plan_error = None
        self._plan_error_label = None
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
                "stop_on_checkpoint": self.app.config.get("stop_on_checkpoint", True),
                "backoff_minutes": self.app.config.get("rate_limit_backoff_minutes", 15),
                "manual_files": {}, "rng": random.Random()}

    def refresh(self):
        self._rows = []
        self._plan = None
        self._plan_error = None
        self._plan_error_label = None
        model = build_model(self.app.config.tool_root, self.app.runlog)
        folders = ["all"] + [p["folder"] for p in model["pages"]]
        self.target_menu.configure(values=folders)
        if model["last_pending_run"]:
            self.resume_label.configure(
                text=f"Đợt {model['last_pending_run']} còn {len(model['pending'])} video dở.")
        else:
            self.resume_label.configure(text="")
        clear_frame(self.table_wrap)
        heading(self.table_wrap, "Video chờ upload").pack(
            anchor="w", pady=(0, 8))
        if not model["pages"]:
            muted(self.table_wrap, "Chưa có page nào.").pack(anchor="w")
            return
        plan = self._build_plan(model["pages"])
        self._plan = plan
        if self._plan_error:
            # Loi lap ke hoach phai thay NGAY tren man hinh, khong chi trong log
            self._plan_error_label = ctk.CTkLabel(
                self.table_wrap,
                text=f"Không lập được kế hoạch upload: {self._plan_error}",
                font=ctk.CTkFont(*FONTS["small_bold"]),
                text_color=COLORS["danger"], anchor="w")
            self._plan_error_label.pack(anchor="w", pady=(0, 8))
        by_page = {}
        for item in plan["items"]:
            by_page.setdefault(item["page_id"], item)
        skipped_by_page = {}
        for s in plan["skipped"]:
            skipped_by_page.setdefault(s["page_id"], s["reason"])
        self._render_table(model["pages"], by_page, skipped_by_page)

    def _build_plan(self, pages):
        """Ke hoach upload de dien san caption/comment cho video tiep theo
        cua moi page. Chi doc file + run-log, khong upload, khong ghi gi."""
        opts = self._read_opts()
        manual = self.manual_entry.get().strip().strip('"')
        if manual:
            for p in pages:
                opts["manual_files"][p["folder"]] = manual
        try:
            plan = upload_adapter.plan_upload_pages(
                self.app.config.tool_root, pages, opts, self.app.runlog,
                resolve_captions_for_page(self.app.config.tool_root,
                                          self.app.config.get("per_page_captions_enabled", False)))
            self._plan_error = None
            return plan
        except Exception as e:
            self._plan_error = str(e)
            self.app.log(f"Không lập được kế hoạch upload: {e}")
            return {"items": [], "skipped": [], "queue": [], "total": 0,
                    "counts": {"dup": 0, "dead_page": 0}}

    def _row_status(self, page, item, skip_reason):
        """(text, mau) cho cot Trang thai cua 1 dong — ly do o nhap bi khoa
        (neu co) phai nhin thay ngay, khong doan mo."""
        if self._plan_error:
            return "Lỗi kế hoạch", COLORS["danger"]
        if item:
            return "Sẽ đăng", COLORS["success"]
        if skip_reason == "dup":
            return "Video này đã đăng rồi", COLORS["text_muted"]
        if skip_reason == "dead_page":
            return "Page đã chết — sẽ bỏ qua", COLORS["warning"]
        return "Không có video", COLORS["text_muted"]

    def _render_table(self, pages, by_page, skipped_by_page):
        """Bang sua duoc: Page | Video da edit | Da dang hom nay | Trang thai |
        Caption | Comment | Đổi. Chi page co video se dang moi sua duoc;
        dong khong dang duoc luon hien ly do o cot Trang thai."""
        cols = [("Page", 180), ("Video đã edit", 90), ("Đã đăng hôm nay", 110),
                ("Trạng thái", 170), ("Caption", 0), ("Comment", 0), ("", 64)]
        header = ctk.CTkFrame(self.table_wrap, fg_color=COLORS["bg_hover"], corner_radius=6)
        header.pack(fill="x", pady=2)
        for ci, (text, w) in enumerate(cols):
            ctk.CTkLabel(header, text=text, font=ctk.CTkFont(*FONTS["small_bold"]),
                         text_color=COLORS["text"], width=w, anchor="w").grid(
                             row=0, column=ci, padx=PAD_SMALL, pady=6, sticky="w")
        header.grid_columnconfigure(4, weight=1)
        header.grid_columnconfigure(5, weight=1)
        for ri, p in enumerate(pages):
            bg = COLORS["bg_row_alt"] if ri % 2 else COLORS["bg_card"]
            fr = ctk.CTkFrame(self.table_wrap, fg_color=bg, corner_radius=6)
            fr.pack(fill="x", pady=2)
            fr.grid_columnconfigure(4, weight=1)
            fr.grid_columnconfigure(5, weight=1)
            ctk.CTkLabel(fr, text=p["name"], font=ctk.CTkFont(*FONTS["body"]),
                         text_color=COLORS["text"], width=180, anchor="w").grid(
                             row=0, column=0, padx=PAD_SMALL, pady=6, sticky="w")
            ctk.CTkLabel(fr, text=str(p["edited_count"]),
                         font=ctk.CTkFont(*FONTS["body"]),
                         text_color=COLORS["text"], width=90, anchor="w").grid(
                             row=0, column=1, padx=PAD_SMALL, pady=6, sticky="w")
            ctk.CTkLabel(fr, text=str(p["today"]),
                         font=ctk.CTkFont(*FONTS["body"]),
                         text_color=COLORS["text"], width=110, anchor="w").grid(
                             row=0, column=2, padx=PAD_SMALL, pady=6, sticky="w")
            item = by_page.get(p["id"])
            status_text, status_color = self._row_status(
                p, item, skipped_by_page.get(p["id"]))
            ctk.CTkLabel(fr, text=status_text, font=ctk.CTkFont(*FONTS["body"]),
                         text_color=status_color, width=170, anchor="w").grid(
                             row=0, column=3, padx=PAD_SMALL, pady=6, sticky="w")
            cap_entry = ctk.CTkEntry(fr, placeholder_text="Caption...",
                                     fg_color=COLORS["bg_input"],
                                     border_color=COLORS["border"],
                                     text_color=COLORS["text"],
                                     placeholder_text_color=COLORS["text_muted"],
                                     font=ctk.CTkFont(*FONTS["body"]),
                                     height=36, corner_radius=8)
            cap_entry.grid(row=0, column=4, padx=PAD_SMALL, pady=6, sticky="ew")
            cmt_entry = ctk.CTkEntry(fr, placeholder_text="Comment (kèm link Shopee)...",
                                     fg_color=COLORS["bg_input"],
                                     border_color=COLORS["border"],
                                     text_color=COLORS["text"],
                                     placeholder_text_color=COLORS["text_muted"],
                                     font=ctk.CTkFont(*FONTS["body"]),
                                     height=36, corner_radius=8)
            cmt_entry.grid(row=0, column=5, padx=PAD_SMALL, pady=6, sticky="ew")
            row = {"page_id": p["id"], "folder": p["folder"],
                   "video_path": item["video_path"] if item else None,
                   "item": item, "cap_entry": cap_entry, "cmt_entry": cmt_entry,
                   "status": status_text}
            doi_btn = ghost_button(fr, "Đổi", lambda r=row: self._reroll_row(r))
            doi_btn.grid(row=0, column=6, padx=PAD_SMALL, pady=6)
            if item:
                cap_entry.insert(0, item["caption"])
                cmt_entry.insert(0, item["comment"])
            else:
                cap_entry.configure(state="disabled")
                cmt_entry.configure(state="disabled")
                doi_btn.configure(state="disabled")
            self._rows.append(row)

    def _reroll_row(self, row):
        """Boc lai caption/comment cua 1 dong tu dung kho cua page do."""
        item = row.get("item")
        if not item:
            return
        caps = item.get("caption_pool") or []
        cmts = item.get("comment_pool") or []
        if caps:
            row["cap_entry"].delete(0, "end")
            row["cap_entry"].insert(0, random.choice(caps))
        if cmts:
            row["cmt_entry"].delete(0, "end")
            row["cmt_entry"].insert(0, random.choice(cmts))

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

    def _collect_run_inputs(self):
        """(pages, opts) chung cho Upload — doc lai trang thai moi nhat."""
        pages, manual = self._selected_pages()
        opts = self._read_opts()
        if manual:
            for p in pages:
                opts["manual_files"][p["folder"]] = manual
        self.app.config.data["upload"] = {
            "gap_seconds": opts["gap"], "comment_delay": opts["comment_delay"],
            "big_first": opts["big_first"], "shuffle": opts["shuffle"]}
        self.app.config.save()
        return pages, opts

    def on_upload(self):
        pages, opts = self._collect_run_inputs()
        if not pages:
            self.app.log("Chưa có page nào.")
            return
        # Dung dung gia tri dang hien trong bang cho video tiep theo cua moi page
        overrides = {}
        for row in self._rows:
            if row.get("video_path"):
                overrides[(row["page_id"], row["video_path"])] = (
                    row["cap_entry"].get(), row["cmt_entry"].get())
        self.app.run_task("upload", self._do_upload, pages, opts, overrides)

    def _do_upload(self, ctx, pages, opts, overrides=None):
        # Kiem tra page nao con song theo /me/accounts (chay tren worker
        # thread de khong dong bang UI). Page chet se bi bo qua, dot chay
        # tiep tuc page khac; khong kiem tra duoc thi chay nhu cu.
        live_ids = upload_adapter.fetch_live_page_ids(
            self.app.config.tool_root, self.app.config.get("user_token", ""))
        if live_ids is not None:
            opts = dict(opts)
            opts["live_page_ids"] = live_ids
            ctx.log(f"Đã kiểm tra page còn sống: {len(live_ids)} page — "
                    f"page chết sẽ bị bỏ qua, đợt chạy tiếp tục.")
        else:
            ctx.log("Không kiểm tra được page còn sống (không có User Token "
                    "hoặc mất mạng) — chạy như cũ.")
        summary = upload_adapter.run_upload_pages(
            self.app.config.tool_root, pages, opts, self.app.runlog,
            ctx.run_id, ctx,
            resolve_captions_for_page(self.app.config.tool_root,
                                      self.app.config.get("per_page_captions_enabled", False)),
            overrides=overrides or {})
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
