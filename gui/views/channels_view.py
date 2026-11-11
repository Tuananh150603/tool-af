"""Kenh nguon Douyin: them/xoa kenh, xem kenh nao chua gan page."""
import shutil
from pathlib import Path

import customtkinter as ctk

from gui.core import store
from gui.theme import COLORS, PAD
from gui.views.common import (BaseView, clear_frame, data_table, danger_button,
                              ghost_button, heading, labeled_entry, muted,
                              primary_button, title)


def build_model(tool_root, pool_root):
    channels = store.list_pool_channels(pool_root)
    assign = store.channel_assignment(tool_root, pool_root)
    for c in channels:
        c["assigned_to"] = assign.get(c["id"])
        c["status"] = "linked" if c["assigned_to"] else "waiting"
    return {"channels": channels,
            "unassigned": [c for c in channels if not c["assigned_to"]]}


class ChannelsView(BaseView):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        title(self, "Kênh nguồn Douyin").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        muted(self, "Mỗi kênh là 1 thư mục ID trong pool, video nằm trong thư mục con 视频.").pack(
            anchor="w", padx=PAD, pady=(0, PAD))
        add = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        add.pack(fill="x", padx=PAD, pady=(0, PAD))
        heading(add, "Thêm kênh mới vào pool").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        row = ctk.CTkFrame(add, fg_color="transparent")
        row.pack(fill="x", padx=PAD, pady=(0, PAD))
        channel_frame, self.channel_entry = labeled_entry(row, "", "ID kênh Douyin, vd: 1083489147427179")
        self.channel_entry.configure(width=300)
        channel_frame.pack(side="left")
        primary_button(row, "Thêm kênh", self.on_add).pack(side="left", padx=(10, 0))
        muted(add, "Thêm xong, chạy Link Pool lần nữa để tự gán kênh cho page đang đợi (FIFO).").pack(
            anchor="w", padx=PAD, pady=(0, PAD))
        self.table_wrap = ctk.CTkFrame(self, fg_color="transparent")
        self.table_wrap.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

    def refresh(self):
        model = build_model(self.app.config.tool_root, self.app.config.pool_root)
        clear_frame(self.table_wrap)
        heading(self.table_wrap,
                f"Kênh trong pool ({len(model['channels'])}), "
                f"{len(model['unassigned'])} kênh chưa gán").pack(anchor="w", pady=(0, 8))
        cols = [("ID kênh", 260), ("Video", 90), ("Đang gán cho page", 320),
                ("Trạng thái", 140), ("", 120)]
        rows = []
        for c in model["channels"]:
            rows.append([c["id"], str(c["video_count"]),
                         c["assigned_to"] or "—", ("pill", c["status"]),
                         ("muted", "")])
        if rows:
            data_table(self.table_wrap, cols, rows).pack(fill="both", expand=True)
        else:
            muted(self.table_wrap, "Pool trống hoặc chưa cấu hình pool root trong Cài đặt.").pack(anchor="w")
        # Nut xoa kenh chua gan
        del_row = ctk.CTkFrame(self.table_wrap, fg_color="transparent")
        del_row.pack(fill="x", pady=(10, 0))
        self.del_var = ctk.StringVar(value="")
        unassigned = [c["id"] for c in model["unassigned"]]
        ctk.CTkOptionMenu(del_row, values=unassigned or ["(không có kênh trống)"],
                          variable=self.del_var,
                          fg_color=COLORS["bg_input"], button_color=COLORS["border"],
                          text_color=COLORS["text"], width=260, height=36).pack(side="left")
        danger_button(del_row, "Xóa kênh đã chọn", self.on_delete).pack(side="left", padx=(10, 0))
        muted(del_row, "Chỉ xóa được kênh chưa gán cho page nào. Luôn hỏi xác nhận trước khi xóa.").pack(
            side="left", padx=(10, 0))

    def on_add(self):
        cid = self.channel_entry.get().strip()
        if not cid or not cid.isdigit():
            self.app.log("ID kênh phải là dãy số (ID Douyin).")
            return
        vdir = Path(self.app.config.pool_root) / cid / "视频"
        vdir.mkdir(parents=True, exist_ok=True)
        self.app.log(f"Đã tạo kênh {cid} trong pool (chưa có video — copy video vào {vdir}).")
        self.refresh()

    def on_delete(self):
        cid = self.del_var.get()
        if not cid or cid.startswith("("):
            return
        from tkinter import messagebox
        if not messagebox.askyesno("Xóa kênh",
                                   f"Xóa kênh {cid} khỏi pool?\nChỉ xóa thư mục kênh, không chạm tới page."):
            return
        shutil.rmtree(Path(self.app.config.pool_root) / cid, ignore_errors=True)
        self.app.log(f"Đã xóa kênh {cid} khỏi pool.")
        self.refresh()
