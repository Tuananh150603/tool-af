"""Du lieu cu (legacy): Non_edit/ + pool_done.txt con sot — chuyen vao pool
hoac xoa, LUON co xac nhan, ghi su kien vao run-log. KHONG tu xoa."""
import shutil
from pathlib import Path

import customtkinter as ctk

from gui.core import store
from gui.theme import COLORS, PAD
from gui.views.common import (BaseView, clear_frame, data_table, danger_button,
                              ghost_button, heading, muted, primary_button,
                              title)


def build_model(tool_root):
    return {"legacy": store.scan_legacy(tool_root)}


def move_legacy_videos_to_pool(tool_root, pool_root, page_folder):
    """Copy video tho trong Non_edit/ vao thu muc pool cua kenh dang gan.
    Tra (so_file_da_copy, thong_bao). Chi chay khi page da co kenh."""
    page_dir = Path(tool_root) / "pages" / page_folder
    channel = store.read_source_channel(page_dir)
    if not channel:
        return 0, "Page chưa gắn kênh — không biết copy vào kênh nào."
    dest = Path(pool_root) / channel / store.VIDEO_SUB
    dest.mkdir(parents=True, exist_ok=True)
    n = 0
    for src in store.collect_legacy_videos(page_dir):
        target = dest / src.name
        if target.exists():
            continue  # trung ten -> bo qua, khong ghi de
        shutil.copy2(src, target)
        n += 1
    return n, f"Đã copy {n} video vào pool kênh {channel}."


class LegacyView(BaseView):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        title(self, "Dữ liệu cũ (legacy)").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        muted(self, "2 page HANZ và TND còn thư mục Non_edit/ (video thô) + file "
                     "pool_done.txt từ workflow cũ (trước 07/10/2026, code hiện tại "
                     "không đọc nữa). Chọn từng mục để xử lý — không tự xóa.").pack(
            anchor="w", padx=PAD, pady=(0, PAD))
        self.table_wrap = ctk.CTkFrame(self, fg_color="transparent")
        self.table_wrap.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

    def refresh(self):
        model = build_model(self.app.config.tool_root)
        clear_frame(self.table_wrap)
        legacy = model["legacy"]
        heading(self.table_wrap, f"Còn sót ở {len(legacy)} page").pack(anchor="w", pady=(0, 8))
        cols = [("Page", 300), ("Non_edit/", 200), ("pool_done.txt", 140)]
        rows = []
        for row in legacy:
            ne = row["non_edit"]
            ne_text = (f"{ne['video_count']} video "
                       f"({ne['total_bytes'] / 1024 / 1024:.1f} MB)"
                       + (" + bản xuất Douyin" if ne["has_data_export"] else "")
                       ) if ne["exists"] else "—"
            pd_text = f"{row['pool_done']['lines']} dòng" if row["pool_done"]["exists"] else "—"
            rows.append([row["folder"], ne_text, pd_text])
        if rows:
            data_table(self.table_wrap, cols, rows).pack(fill="x")
        else:
            muted(self.table_wrap, "Sạch — không còn dữ liệu cũ nào.").pack(anchor="w")
        # Hanh dong theo page
        for row in legacy:
            card = ctk.CTkFrame(self.table_wrap, fg_color=COLORS["bg_card"], corner_radius=10)
            card.pack(fill="x", pady=(8, 0))
            heading(card, row["folder"]).pack(anchor="w", padx=PAD, pady=(PAD, 2))
            bar = ctk.CTkFrame(card, fg_color="transparent")
            bar.pack(fill="x", padx=PAD, pady=(0, PAD))
            if row["non_edit"]["exists"]:
                primary_button(bar, "Chuyển video thô vào pool",
                               lambda f=row["folder"]: self.on_move(f)).pack(side="left")
                danger_button(bar, "Xóa thư mục Non_edit/",
                              lambda f=row["folder"]: self.on_delete_nonedit(f)).pack(
                                  side="left", padx=(10, 0))
            if row["pool_done"]["exists"]:
                danger_button(bar, "Xóa pool_done.txt",
                              lambda f=row["folder"]: self.on_delete_pooldone(f)).pack(
                                  side="left", padx=(10, 0))

    def on_move(self, folder):
        n, msg = move_legacy_videos_to_pool(self.app.config.tool_root,
                                            self.app.config.pool_root, folder)
        self.app.log(msg)
        self.app.runlog.record_event("legacy_move", msg, {"page": folder, "copied": n})
        self.refresh()

    def on_delete_nonedit(self, folder):
        from tkinter import messagebox
        if not messagebox.askyesno(
                "Xóa thư mục Non_edit/",
                f"Xóa toàn bộ thư mục Non_edit/ của {folder}?\n"
                f"Hành động này KHÔNG khôi phục được. Nên chuyển video vào pool trước."):
            return
        shutil.rmtree(Path(self.app.config.tool_root) / "pages" / folder / "Non_edit",
                      ignore_errors=True)
        self.app.log(f"Đã xóa Non_edit/ của {folder}.")
        self.app.runlog.record_event("legacy_delete", f"Đã xóa Non_edit/ của {folder}",
                                     {"page": folder})
        self.refresh()

    def on_delete_pooldone(self, folder):
        from tkinter import messagebox
        if not messagebox.askyesno(
                "Xóa pool_done.txt",
                f"Xóa file pool_done.txt của {folder}?\n"
                f"File này code hiện tại không đọc nữa (chỉ còn giá trị tham khảo)."):
            return
        (Path(self.app.config.tool_root) / "pages" / folder / "pool_done.txt").unlink(missing_ok=True)
        self.app.log(f"Đã xóa pool_done.txt của {folder}.")
        self.app.runlog.record_event("legacy_delete", f"Đã xóa pool_done.txt của {folder}",
                                     {"page": folder})
        self.refresh()
