"""Lich su chay: nhat ky edit/upload/event + tom tat dot chay + tiep tuc."""
import customtkinter as ctk

from gui.theme import COLORS, PAD
from gui.views.common import (BaseView, clear_frame, data_table, heading,
                              muted, title)


def build_model(runlog, n=100):
    items = runlog.recent(n)
    runs = {}
    for u in runlog.data["uploads"]:
        runs.setdefault(u.get("run_id"), runlog.run_summary(u.get("run_id")))
    return {"items": items, "runs": runs}


class HistoryView(BaseView):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        title(self, "Lịch sử chạy").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        muted(self, "Mọi lần edit/upload/sự kiện an toàn đều ghi ở đây. "
                     "Đợt chạy dở thì bấm 'Tiếp tục' ở màn Upload.").pack(
            anchor="w", padx=PAD, pady=(0, PAD))
        self.table_wrap = ctk.CTkFrame(self, fg_color="transparent")
        self.table_wrap.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

    def refresh(self):
        model = build_model(self.app.runlog)
        clear_frame(self.table_wrap)
        heading(self.table_wrap, f"Hoạt động gần nhất ({len(model['items'])})").pack(
            anchor="w", pady=(0, 8))
        cols = [("Thời gian", 150), ("Loại", 80), ("Nội dung", 420), ("Trạng thái", 120)]
        rows = []
        for it in model["items"][:60]:
            d = it["data"]
            if it["type"] == "upload":
                text = f"{d.get('page_folder', '')}: {d.get('file_path', '').split('/')[-1].split(chr(92))[-1]}"
                if d.get("fb_video_id"):
                    text += f" → FB {d['fb_video_id']}"
                status = d.get("status", "")
                pill = {"ok": "ok", "failed": "failed", "pending": "pending"}.get(status, "skipped")
                rows.append([d.get("ts", "")[:19], "Upload", text, ("pill", pill)])
            elif it["type"] == "edit":
                text = f"{d.get('page_folder', '')}: {d.get('source_path', '').split('/')[-1].split(chr(92))[-1]} → {d.get('output_name', '')}"
                pill = "ok" if d.get("status") == "ok" else "failed"
                rows.append([d.get("ts", "")[:19], "Edit", text, ("pill", pill)])
            else:
                rows.append([d.get("ts", "")[:19], "Sự kiện", d.get("message", ""),
                             ("pill", "pending")])
        if rows:
            data_table(self.table_wrap, cols, rows).pack(fill="both", expand=True)
        else:
            muted(self.table_wrap, "Chưa có hoạt động nào.").pack(anchor="w")
