"""Cua so chinh Tool AF GUI.

Bo cuc: sidebar trai co dinh (logo + menu 12 man hinh + trang thai token),
noi dung ben phai, console log + thanh tien do + nut Dung o duoi,
banner do hien khi dot chay bi dung do checkpoint/rate-limit.
"""
import sys
from datetime import datetime
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
if str(TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT))

import customtkinter as ctk

from gui.core.config import Config
from gui.core.runlog import RunLog
from gui.core.safety import KIND_LABELS
from gui.theme import COLORS, FONTS, PAD
from gui.views.bgm_view import BgmView
from gui.views.captions_view import CaptionsView
from gui.views.channels_view import ChannelsView
from gui.views.dashboard import DashboardView
from gui.views.history_view import HistoryView
from gui.views.legacy_view import LegacyView
from gui.views.pages_view import PagesView
from gui.views.pool_view import PoolView
from gui.views.processing_view import ProcessingView
from gui.views.scheduler_view import SchedulerView, build_model as scheduler_model
from gui.views.settings_view import SettingsView
from gui.views.upload_view import UploadView
from gui.workers import TaskRunner

VIEWS = [
    ("dashboard", "Dashboard", DashboardView),
    ("pages", "Page", PagesView),
    ("pool", "Link Pool", PoolView),
    ("channels", "Kênh nguồn", ChannelsView),
    ("processing", "Xử lý video", ProcessingView),
    ("upload", "Upload", UploadView),
    ("captions", "Caption & Comment", CaptionsView),
    ("bgm", "Nhạc nền", BgmView),
    ("history", "Lịch sử", HistoryView),
    ("legacy", "Dữ liệu cũ", LegacyView),
    ("scheduler", "Hẹn giờ", SchedulerView),
    ("settings", "Cài đặt", SettingsView),
]


class App(ctk.CTk):
    def __init__(self, config=None, runlog=None):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title("Tool AF — Quản lý đa Page Facebook")
        self.geometry("1280x800")
        self.minsize(1000, 650)
        self.config = config or Config.load()
        self.runlog = runlog or RunLog(Path(self.config.tool_root) / "gui_runlog.json")
        self.runner = TaskRunner()
        self.token_status = {}
        self.current_view = None
        self._build_layout()
        self.show_view("dashboard")
        self.after(100, self._poll_runner)
        self.after(30000, self._scheduler_tick)

    # ---- layout ----
    def _build_layout(self):
        sidebar = ctk.CTkFrame(self, fg_color=COLORS["sidebar"], width=210, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        ctk.CTkLabel(sidebar, text="Tool AF", font=ctk.CTkFont(*FONTS["logo"]),
                     text_color=COLORS["text"]).pack(anchor="w", padx=PAD, pady=(PAD, 0))
        ctk.CTkLabel(sidebar, text="Douyin → Facebook • Đa Page",
                     font=ctk.CTkFont(*FONTS["small"]),
                     text_color=COLORS["text_muted"]).pack(anchor="w", padx=PAD, pady=(0, PAD))
        self.nav_buttons = {}
        for key, label, _cls in VIEWS:
            b = ctk.CTkButton(sidebar, text=label,
                              command=lambda k=key: self.show_view(k),
                              fg_color="transparent", hover_color=COLORS["bg_hover"],
                              text_color=COLORS["text"], anchor="w", height=38,
                              corner_radius=8, font=ctk.CTkFont(*FONTS["body"]))
            b.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = b
        self.token_label = ctk.CTkLabel(sidebar, text="Token: chưa nhập",
                                        font=ctk.CTkFont(*FONTS["small"]),
                                        text_color=COLORS["text_muted"])
        self.token_label.pack(side="bottom", anchor="w", padx=PAD, pady=PAD)

        main = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        main.pack(side="left", fill="both", expand=True)
        # Banner do (an mac dinh) — hien khi dung dot chay do checkpoint/429
        self.banner = ctk.CTkFrame(main, fg_color=COLORS["danger"], corner_radius=8)
        self.banner_label = ctk.CTkLabel(self.banner, text="",
                                         font=ctk.CTkFont(*FONTS["body_bold"]),
                                         text_color="#FFFFFF", wraplength=900,
                                         justify="left")
        self.banner_label.pack(side="left", padx=PAD, pady=8, fill="x", expand=True)
        ctk.CTkButton(self.banner, text="Xem lịch sử",
                      command=lambda: self.show_view("history"),
                      fg_color="#FFFFFF", hover_color="#E8E8E8",
                      text_color=COLORS["danger"], height=30,
                      font=ctk.CTkFont(*FONTS["small_bold"])).pack(side="right", padx=PAD)
        ctk.CTkButton(self.banner, text="✕", command=self.hide_banner,
                      fg_color="transparent", hover_color="#C93A3F",
                      text_color="#FFFFFF", height=30, width=30,
                      font=ctk.CTkFont(*FONTS["body_bold"])).pack(side="right")
        # Noi dung
        self.content = ctk.CTkFrame(main, fg_color="transparent")
        self.content.pack(fill="both", expand=True)
        self.views = {}
        for key, _label, cls in VIEWS:
            self.views[key] = cls(self.content, self)
        # Console duoi: progress + nut Dung + log
        console = ctk.CTkFrame(main, fg_color=COLORS["bg_card"], corner_radius=0,
                               border_width=1, border_color=COLORS["border"])
        console.pack(fill="x", side="bottom")
        top = ctk.CTkFrame(console, fg_color="transparent")
        top.pack(fill="x", padx=PAD, pady=(8, 0))
        self.progress = ctk.CTkProgressBar(top, fg_color=COLORS["border"],
                                           progress_color=COLORS["accent"], height=10)
        self.progress.pack(side="left", fill="x", expand=True)
        self.progress.set(0)
        self.progress_label = ctk.CTkLabel(top, text="Sẵn sàng",
                                           font=ctk.CTkFont(*FONTS["small"]),
                                           text_color=COLORS["text_muted"], width=300,
                                           anchor="w")
        self.progress_label.pack(side="left", padx=(10, 0))
        self.stop_button = ctk.CTkButton(top, text="■ Dừng", command=self.on_stop,
                                         fg_color=COLORS["danger"],
                                         hover_color=COLORS["danger_hover"],
                                         text_color="#FFFFFF", height=30, width=80,
                                         state="disabled",
                                         font=ctk.CTkFont(*FONTS["body_bold"]))
        self.stop_button.pack(side="left", padx=(10, 0))
        self.log_box = ctk.CTkTextbox(console, fg_color="#0B0D0F",
                                      text_color="#D6DEE8",
                                      font=ctk.CTkFont("Consolas", 11), height=130)
        self.log_box.pack(fill="x", padx=PAD, pady=8)
        self.log_box.configure(state="disabled")

    # ---- dieu huong ----
    def show_view(self, key):
        for k, v in self.views.items():
            v.pack_forget()
        self.views[key].pack(fill="both", expand=True)
        self.current_view = key
        for k, b in self.nav_buttons.items():
            b.configure(fg_color=COLORS["bg_hover"] if k == key else "transparent")
        self._update_token_label()
        try:
            self.views[key].refresh()
        except Exception as e:
            self.log(f"Lỗi tải màn hình {key}: {e}")

    def _update_token_label(self):
        has = bool(self.config.get("user_token", ""))
        self.token_label.configure(
            text="Token: đã nhập ✓" if has else "Token: chưa nhập — vào Cài đặt",
            text_color=COLORS["success"] if has else COLORS["warning"])

    # ---- log / banner / tien do (chi goi tu main thread) ----
    def log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", str(msg) + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def show_safety_banner(self, summary):
        kind = summary.get("stop_kind", "other")
        label = KIND_LABELS.get(kind, kind)
        self.banner_label.configure(
            text=f"⛔ ĐÃ DỪNG ĐỢT CHẠY — {label}"
                 + (f" (page {summary.get('stop_page')}, video {summary.get('stop_video')})"
                    if summary.get("stop_page") else "")
                 + " — kiểm tra tài khoản rồi bấm chạy lại tay.")
        self.banner.pack(fill="x", padx=PAD, pady=(PAD, 0))

    def hide_banner(self):
        self.banner.pack_forget()

    def _set_progress(self, done, total, msg):
        if total:
            self.progress.set(max(0.0, min(1.0, done / total)))
            self.progress_label.configure(text=f"{msg} ({done}/{total})")
        else:
            self.progress_label.configure(text=f"{msg} ({done} xong)")

    # ---- tac vu nen ----
    def run_task(self, name, fn, *args, **kwargs):
        if not self.runner.start(name, fn, *args, **kwargs):
            self.log("Đang có tác vụ chạy — bấm ■ Dừng trước khi chạy tác vụ khác.")
            return False
        self.stop_button.configure(state="normal")
        self.progress.set(0)
        self.progress_label.configure(text=f"Đang chạy: {name}...")
        self.log(f"▶ Bắt đầu: {name}")
        return True

    def on_stop(self):
        self.runner.stop()
        self.log("■ Đã bấm Dừng — đang dừng tác vụ...")

    def _poll_runner(self):
        if not self.winfo_exists():
            return
        for event in self.runner.poll():
            kind = event[0]
            if kind == "log":
                self.log(event[1])
            elif kind == "progress":
                _, done, total, msg = event
                self._set_progress(done, total, msg)
            elif kind == "done":
                _, name, _run_id, summary = event
                self.stop_button.configure(state="disabled")
                self.progress.set(1.0 if not summary.get("stopped") else 0.0)
                self.progress_label.configure(text="Xong." if not summary.get("stopped")
                                              else "Đã dừng.")
                self.log(f"■ Xong: {name} — {summary}")
                if summary.get("stop_kind"):
                    self.show_safety_banner(summary)
                if self.current_view:
                    try:
                        self.views[self.current_view].refresh()
                    except Exception:
                        pass
            elif kind == "error":
                _, name, _run_id, tb = event
                self.stop_button.configure(state="disabled")
                self.log(f"✖ Lỗi trong tác vụ {name}:\n{tb[-1500:]}")
        self.after(100, self._poll_runner)

    # ---- hen gio ----
    def _scheduler_tick(self):
        if not self.winfo_exists():
            return
        try:
            model = scheduler_model(self.config, self.runlog, now=datetime.now())
            if model["due"] and not self.runner.running:
                self.log(f"⏰ Đến giờ hẹn {model['time']} — tự chạy edit + upload.")
                self.run_task("schedule", self._run_scheduled, model)
        except Exception as e:
            self.log(f"Lỗi kiểm tra lịch hẹn: {e}")
        self.after(30000, self._scheduler_tick)

    def _run_scheduled(self, ctx, model):
        from gui.adapters import processing_adapter, upload_adapter
        from gui.views.upload_view import resolve_captions_for_page
        self.runlog.set_last_schedule_date(datetime.now().date().isoformat())
        if model["run_edit"]:
            s = processing_adapter.run_edit_round(
                self.config.tool_root, None, 1, self.config.pipeline_params,
                self.config.get("jitter_enabled", False), self.config.jitter_cfg,
                self.config.get("delete_source_after_edit", False),
                self.runlog, ctx.run_id, ctx)
            ctx.log(f"[Hẹn giờ] Edit: {s['ok']}/{s['total']} OK.")
        if model["run_upload"] and not ctx.is_stopped():
            pages = upload_adapter.refresh_page_tokens(self.config.tool_root)
            opts = {"gap": self.config.get("upload", {}).get("gap_seconds", 10),
                    "comment_delay": self.config.get("upload", {}).get("comment_delay", 15),
                    "big_first": self.config.get("upload", {}).get("big_first", False),
                    "shuffle": True,
                    "cap_enabled": self.config.get("daily_cap_enabled", True),
                    "cap_per_page": self.config.get("daily_cap_per_page", 1),
                    "stop_on_checkpoint": self.config.get("stop_on_checkpoint", True),
                    "backoff_minutes": self.config.get("rate_limit_backoff_minutes", 15),
                    "manual_files": {}, "rng": ctx.rng}
            s = upload_adapter.run_upload_pages(
                self.config.tool_root, pages, opts, self.runlog, ctx.run_id, ctx,
                resolve_captions_for_page(
                    self.config.tool_root,
                    self.config.get("per_page_captions_enabled", False)))
            ctx.log(f"[Hẹn giờ] Upload: {s['ok']}/{s['total']} OK.")
            return s
        return {"scheduled": True}


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
