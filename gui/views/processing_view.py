"""Xu ly video: pipeline FFmpeg (chinh thong so + jitter) + xem truoc."""
import os
import platform
import subprocess
from pathlib import Path

import customtkinter as ctk

from gui.adapters import processing_adapter
from gui.core import store
from gui.core.pipeline import validate_jitter_cfg
from gui.theme import COLORS, PAD
from gui.views.common import (BaseView, clear_frame, data_table, ghost_button,
                              heading, labeled_entry, muted, primary_button,
                              title)


def build_model(tool_root, pool_root):
    """Trang thai tung page: pool / edited (khong fetch token)."""
    pages = []
    for d in store.list_page_dirs(tool_root):
        info = store.parse_info(d)
        sdir = store.read_source_path(d)
        pool_count = 0
        if sdir:
            pool_count = (1 if Path(sdir).is_file() and Path(sdir).suffix.lower() in store.VIDEO_EXTS
                          else store.count_videos(sdir))
        pages.append({"folder": d.name, "dir": str(d), "id": info["id"],
                      "name": info["name"], "pool_count": pool_count,
                      "edited_count": store.count_videos(d / "edited"),
                      "waiting": sdir is None})
    return {"pages": pages,
            "total_pool": sum(p["pool_count"] for p in pages),
            "total_edited": sum(p["edited_count"] for p in pages)}


def open_file(path):
    """Mo video bang trinh xem mac dinh cua he dieu hanh (xem truoc)."""
    if platform.system() == "Windows":
        os.startfile(str(path))  # noqa: S606
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


PARAM_FIELDS = [
    ("speed", "Tốc độ (1.045 = nhanh hơn 4,5%)", "1.045"),
    ("zoom", "Zoom trước khi crop", "1.06"),
    ("crop_w", "Crop rộng (0.94)", "0.94"),
    ("crop_h", "Crop cao (0.93)", "0.93"),
    ("contrast", "Contrast", "1.04"),
    ("saturation", "Saturation", "1.03"),
    ("noise", "Nhiễu hạt (alls)", "6"),
    ("trim_head", "Cắt đầu (giây)", "1"),
    ("trim_tail", "Cắt cuối (giây)", "2.5"),
    ("bgm_vol", "Âm lượng nhạc nền (0.18)", "0.18"),
]


class ProcessingView(BaseView):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        title(self, "Xử lý video — Pipeline FFmpeg").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        muted(self, "Mỗi lượt edit 1 video/page (xoay vòng). Mặc định KHÔNG xóa video gốc — "
                     "chống trùng bằng run-log.").pack(anchor="w", padx=PAD, pady=(0, PAD))
        # Form thong so
        form = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        form.pack(fill="x", padx=PAD, pady=(0, PAD))
        heading(form, "Thông số pipeline (mặc định = đúng hằng số gốc)").pack(
            anchor="w", padx=PAD, pady=(PAD, 4))
        self.entries = {}
        grid = ctk.CTkFrame(form, fg_color="transparent")
        grid.pack(fill="x", padx=PAD, pady=(0, PAD))
        for i, (key, label, ph) in enumerate(PARAM_FIELDS):
            frame, e = labeled_entry(grid, label, ph)
            frame.grid(row=i // 5, column=i % 5, padx=(0, 10), pady=4, sticky="ew")
            self.entries[key] = e
        for c in range(5):
            grid.grid_columnconfigure(c, weight=1)
        toggles = ctk.CTkFrame(form, fg_color="transparent")
        toggles.pack(fill="x", padx=PAD, pady=(0, PAD))
        self.hflip_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(toggles, text="Lật ngang (hflip)", variable=self.hflip_var,
                        fg_color=COLORS["accent"], text_color=COLORS["text"]).pack(side="left")
        self.bgm_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(toggles, text="Trộn nhạc nền (nếu có file trong bgm/)",
                        variable=self.bgm_var, fg_color=COLORS["accent"],
                        text_color=COLORS["text"]).pack(side="left", padx=(20, 0))
        self.del_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(toggles, text="XÓA video gốc sau khi edit (mặc định TẮT)",
                        variable=self.del_var, fg_color=COLORS["danger"],
                        text_color=COLORS["danger"]).pack(side="left", padx=(20, 0))
        # Jitter
        jit = ctk.CTkFrame(form, fg_color="transparent")
        jit.pack(fill="x", padx=PAD, pady=(0, PAD))
        self.jitter_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(jit, text="Dao động nhẹ thông số mỗi video (tránh 1 công thức cố định)",
                        variable=self.jitter_var, fg_color=COLORS["accent"],
                        text_color=COLORS["text"]).pack(side="left")
        muted(jit, "Khoảng dao động chỉnh trong Cài đặt (vd tốc độ 1.03–1.06).").pack(
            side="left", padx=(10, 0))
        # Chay
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=PAD, pady=(0, PAD))
        self.target_var = ctk.StringVar(value="all")
        self.target_menu = ctk.CTkOptionMenu(bar, values=["all"], variable=self.target_var,
                                             fg_color=COLORS["bg_input"],
                                             button_color=COLORS["border"],
                                             text_color=COLORS["text"], width=320, height=36)
        self.target_menu.pack(side="left")
        primary_button(bar, "Edit xoay vòng", self.on_edit).pack(side="left", padx=(10, 0))
        ghost_button(bar, "Xem trước video đã edit", self.on_preview).pack(side="left", padx=(10, 0))
        self.table_wrap = ctk.CTkFrame(self, fg_color="transparent")
        self.table_wrap.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))
        self._fill_form_from_config()

    def _fill_form_from_config(self):
        p = self.app.config.pipeline_params
        for key, e in self.entries.items():
            e.delete(0, "end")
            e.insert(0, str(p.get(key, "")))
        self.hflip_var.set(bool(p.get("hflip", True)))
        self.bgm_var.set(bool(p.get("use_bgm", True)))
        self.jitter_var.set(bool(self.app.config.get("jitter_enabled", False)))
        self.del_var.set(bool(self.app.config.get("delete_source_after_edit", False)))

    def _read_params(self):
        p = {}
        for key, e in self.entries.items():
            raw = e.get().strip()
            try:
                p[key] = float(raw) if "." in raw else int(raw)
            except Exception:
                p[key] = self.app.config.pipeline_params.get(key)
        p["hflip"] = self.hflip_var.get()
        p["use_bgm"] = self.bgm_var.get()
        p["noise"] = int(p.get("noise", 6))
        return p

    def refresh(self):
        model = build_model(self.app.config.tool_root, self.app.config.pool_root)
        folders = ["all"] + [p["folder"] for p in model["pages"]]
        self.target_menu.configure(values=folders)
        clear_frame(self.table_wrap)
        heading(self.table_wrap,
                f"Trạng thái: {model['total_pool']} video chưa edit, "
                f"{model['total_edited']} video đã edit").pack(anchor="w", pady=(0, 8))
        cols = [("Page", 300), ("Pool chưa edit", 120), ("Đã edit", 100), ("Trạng thái", 140)]
        rows = [[p["name"], str(p["pool_count"]), str(p["edited_count"]),
                 ("pill", "waiting" if p["waiting"] else "linked")] for p in model["pages"]]
        if rows:
            data_table(self.table_wrap, cols, rows).pack(fill="both", expand=True)
        else:
            muted(self.table_wrap, "Chưa có page nào.").pack(anchor="w")

    def on_edit(self):
        params = self._read_params()
        target = None if self.target_var.get() == "all" else [self.target_var.get()]
        jitter = self.app.config.jitter_cfg
        if self.jitter_var.get():
            errs = validate_jitter_cfg(jitter)
            if errs:
                self.app.log("Khoảng dao động sai: " + "; ".join(errs))
                return
        self.app.config.data["pipeline"] = params
        self.app.config.set("jitter_enabled", self.jitter_var.get())
        self.app.config.set("delete_source_after_edit", self.del_var.get())
        self.app.config.save()
        self.app.run_task("edit", self._do_edit, target, params)

    def _do_edit(self, ctx, target, params):
        summary = processing_adapter.run_edit_round(
            self.app.config.tool_root, target, 1, params,
            self.app.config.get("jitter_enabled", False),
            self.app.config.jitter_cfg,
            self.app.config.get("delete_source_after_edit", False),
            self.app.runlog, ctx.run_id, ctx)
        ctx.log(f"XONG edit: {summary['ok']}/{summary['total']} OK, "
                f"{summary['failed']} lỗi, {summary['skipped']} bỏ qua (đã edit).")
        return summary

    def on_preview(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Chọn video đã edit để xem trước",
            initialdir=str(Path(self.app.config.tool_root) / "pages"),
            filetypes=[("Video", "*.mp4 *.mov *.mkv *.avi")])
        if path:
            open_file(path)
