"""Nhac nen (BGM): them/xoa file nhac, bat/tat tron nhac, muc am luong."""
import shutil
from pathlib import Path

import customtkinter as ctk

from gui.core import store
from gui.theme import COLORS, PAD
from gui.views.common import (BaseView, clear_frame, data_table, danger_button,
                              ghost_button, heading, muted, primary_button,
                              title)


def build_model(tool_root, config):
    files = store.list_bgm(tool_root)
    return {"files": [{"name": f.name, "size_mb": round(f.stat().st_size / 1024 / 1024, 1)}
                      for f in files],
            "use_bgm": config.pipeline_params.get("use_bgm", True),
            "bgm_vol": config.pipeline_params.get("bgm_vol", 0.18)}


class BgmView(BaseView):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        title(self, "Nhạc nền (BGM)").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        muted(self, "File nhạc trong video_processing/bgm/ được trộn ngẫu nhiên vào "
                     "video lúc edit. Thư mục đang trống thì video chỉ có audio gốc.").pack(
            anchor="w", padx=PAD, pady=(0, PAD))
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=PAD, pady=(0, PAD))
        primary_button(bar, "Thêm file nhạc...", self.on_add).pack(side="left")
        self.bgm_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(bar, text="Bật trộn nhạc nền",
                        variable=self.bgm_var, fg_color=COLORS["accent"],
                        text_color=COLORS["text"]).pack(side="left", padx=(20, 0))
        ghost_button(bar, "Lưu cài đặt nhạc", self.on_save).pack(side="left", padx=(10, 0))
        self.vol_label = muted(bar, "")
        self.vol_label.pack(side="left", padx=(10, 0))
        self.table_wrap = ctk.CTkFrame(self, fg_color="transparent")
        self.table_wrap.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

    def refresh(self):
        model = build_model(self.app.config.tool_root, self.app.config)
        self.bgm_var.set(bool(model["use_bgm"]))
        self.vol_label.configure(text=f"Mức trộn: {model['bgm_vol']} (18% mặc định)")
        clear_frame(self.table_wrap)
        heading(self.table_wrap, f"File nhạc ({len(model['files'])})").pack(
            anchor="w", pady=(0, 8))
        cols = [("Tên file", 420), ("Dung lượng (MB)", 140)]
        rows = [[f["name"], str(f["size_mb"])] for f in model["files"]]
        if rows:
            data_table(self.table_wrap, cols, rows).pack(fill="x")
        else:
            muted(self.table_wrap, "Chưa có file nhạc nào — bấm 'Thêm file nhạc...' để thêm.").pack(anchor="w")
        del_row = ctk.CTkFrame(self.table_wrap, fg_color="transparent")
        del_row.pack(fill="x", pady=(10, 0))
        self.del_var = ctk.StringVar(value="")
        names = [f["name"] for f in model["files"]]
        ctk.CTkOptionMenu(del_row, values=names or ["(chưa có file)"],
                          variable=self.del_var,
                          fg_color=COLORS["bg_input"], button_color=COLORS["border"],
                          text_color=COLORS["text"], width=320, height=36).pack(side="left")
        danger_button(del_row, "Xóa file đã chọn", self.on_delete).pack(side="left", padx=(10, 0))

    def on_add(self):
        from tkinter import filedialog
        paths = filedialog.askopenfilenames(
            title="Chọn file nhạc",
            filetypes=[("Nhạc", "*.mp3 *.wav *.m4a")])
        bgm_dir = Path(self.app.config.tool_root) / "video_processing" / "bgm"
        bgm_dir.mkdir(parents=True, exist_ok=True)
        n = 0
        for p in paths:
            shutil.copy(p, bgm_dir / Path(p).name)
            n += 1
        if n:
            self.app.log(f"Đã thêm {n} file nhạc vào bgm/.")
        self.refresh()

    def on_save(self):
        self.app.config.data["pipeline"]["use_bgm"] = self.bgm_var.get()
        self.app.config.save()
        self.app.log(f"Đã lưu: trộn nhạc nền = {'BẬT' if self.bgm_var.get() else 'TẮT'}.")

    def on_delete(self):
        name = self.del_var.get()
        if not name or name.startswith("("):
            return
        from tkinter import messagebox
        if not messagebox.askyesno("Xóa file nhạc", f"Xóa {name} khỏi bgm/?"):
            return
        (Path(self.app.config.tool_root) / "video_processing" / "bgm" / name).unlink(missing_ok=True)
        self.app.log(f"Đã xóa {name}.")
        self.refresh()
