"""Hen gio: chay tu dong moi ngay theo gio dat truoc (khi app dang mo)."""
from datetime import datetime

import customtkinter as ctk

from gui.core.scheduler import is_due, next_run_datetime, parse_hhmm
from gui.theme import COLORS, PAD
from gui.views.common import (BaseView, heading, labeled_entry, muted,
                              primary_button, title)


def build_model(config, runlog, now=None):
    sched = config.get("schedule", {})
    now = now or datetime.now()
    nxt = next_run_datetime(now, sched.get("time", "08:00")) if sched.get("enabled") else None
    return {"enabled": bool(sched.get("enabled", False)),
            "time": sched.get("time", "08:00"),
            "run_edit": bool(sched.get("run_edit", True)),
            "run_upload": bool(sched.get("run_upload", True)),
            "next_run": nxt,
            "last_date": runlog.get_last_schedule_date(),
            "due": is_due(now, sched.get("time", "08:00"),
                          runlog.get_last_schedule_date()) if sched.get("enabled") else False}


class SchedulerView(BaseView):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        title(self, "Hẹn giờ chạy tự động").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        muted(self, "App đang mở sẽ tự chạy edit + upload vào giờ hẹn mỗi ngày "
                     "(1 video/page/ngày theo trần đã đặt).").pack(
            anchor="w", padx=PAD, pady=(0, PAD))
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        card.pack(fill="x", padx=PAD, pady=(0, PAD))
        self.enabled_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(card, text="Bật hẹn giờ mỗi ngày",
                        variable=self.enabled_var, fg_color=COLORS["accent"],
                        text_color=COLORS["text"],
                        font=ctk.CTkFont("Segoe UI", 13, "bold")).pack(
                            anchor="w", padx=PAD, pady=(PAD, 8))
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=PAD, pady=(0, 8))
        time_frame, self.time_entry = labeled_entry(row, "Giờ chạy (24h)", "08:00")
        self.time_entry.configure(width=120)
        time_frame.pack(side="left")
        self.edit_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(row, text="Edit video (xoay vòng)",
                        variable=self.edit_var, fg_color=COLORS["accent"],
                        text_color=COLORS["text"]).pack(side="left", padx=(20, 0), pady=(18, 0))
        self.upload_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(row, text="Upload lên Facebook",
                        variable=self.upload_var, fg_color=COLORS["accent"],
                        text_color=COLORS["text"]).pack(side="left", padx=(20, 0), pady=(18, 0))
        primary_button(card, "Lưu lịch hẹn", self.on_save).pack(
            anchor="w", padx=PAD, pady=(0, PAD))
        self.info_label = muted(self, "")
        self.info_label.pack(anchor="w", padx=PAD, pady=(0, PAD))

    def refresh(self):
        model = build_model(self.app.config, self.app.runlog)
        self.enabled_var.set(model["enabled"])
        self.time_entry.delete(0, "end")
        self.time_entry.insert(0, model["time"])
        self.edit_var.set(model["run_edit"])
        self.upload_var.set(model["run_upload"])
        if model["enabled"] and model["next_run"]:
            self.info_label.configure(
                text=f"Lần chạy kế tiếp: {model['next_run'].strftime('%H:%M %d/%m/%Y')}"
                     + (f" — đã chạy ngày {model['last_date']}" if model["last_date"] else ""))
        else:
            self.info_label.configure(text="Hẹn giờ đang tắt.")

    def on_save(self):
        hhmm = self.time_entry.get().strip()
        if parse_hhmm(hhmm) is None:
            self.app.log("Giờ hẹn sai định dạng — dùng HH:MM, vd 08:00.")
            return
        self.app.config.data["schedule"] = {
            "enabled": self.enabled_var.get(), "time": hhmm,
            "run_edit": self.edit_var.get(), "run_upload": self.upload_var.get()}
        self.app.config.save()
        self.app.log(f"Đã lưu lịch hẹn: {'BẬT' if self.enabled_var.get() else 'TẮT'} lúc {hhmm} mỗi ngày.")
        self.refresh()
