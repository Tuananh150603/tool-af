"""Dashboard: the so lieu + bang page (tim kiem / loc trang thai)."""
import customtkinter as ctk

from gui.core import store
from gui.theme import COLORS, PAD
from gui.views.common import (BaseView, clear_frame, data_table, heading,
                              muted, stat_card, title)


def build_model(tool_root, pool_root, runlog, token_status=None):
    """Du lieu thuan cho Dashboard (test duoc headless)."""
    pages = store.all_page_status(tool_root, pool_root)
    rows = store.read_pool_map(tool_root)
    total_pool = sum(r["count"] for r in rows if not r["waiting"])
    for p in pages:
        p["today"] = runlog.uploads_today(p["id"])
        p["status"] = "linked" if not p["waiting"] else "waiting"
        p["token_status"] = (token_status or {}).get(p["id"], "unknown")
    return {
        "pages": pages,
        "total_pages": len(pages),
        "linked": sum(1 for p in pages if not p["waiting"]),
        "waiting": sum(1 for p in pages if p["waiting"]),
        "total_pool": total_pool,
        "total_edited": sum(p["edited_count"] for p in pages),
        "today_uploads": sum(p["today"] for p in pages),
        "backoff_until": runlog.get_backoff(),
    }


class DashboardView(BaseView):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.query_var = ctk.StringVar(value="")
        self.filter_var = ctk.StringVar(value="all")
        title(self, "Dashboard").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        muted(self, "Tổng quan hệ thống — 16 page, pool Douyin, tiến độ hôm nay").pack(
            anchor="w", padx=PAD, pady=(0, PAD))
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=PAD, pady=(0, PAD))
        self.backoff_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                          text_color=COLORS["warning"])
        self.backoff_label.pack(anchor="w", padx=PAD, pady=(0, PAD))
        # Tim kiem + loc
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=PAD, pady=(0, PAD))
        self.search = ctk.CTkEntry(bar, placeholder_text="Tìm page theo tên / ID...",
                                   fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                                   text_color=COLORS["text"], width=320, height=36)
        self.search.pack(side="left")
        self.search.bind("<KeyRelease>", lambda e: self.refresh())
        self.filter_menu = ctk.CTkOptionMenu(
            bar, values=["all", "linked", "waiting", "token_dead"],
            variable=self.filter_var, command=lambda v: self.refresh(),
            fg_color=COLORS["bg_input"], button_color=COLORS["border"],
            text_color=COLORS["text"], width=170, height=36)
        self.filter_menu.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(bar, text="all: tất cả • linked: đã gắn • waiting: đang đợi • token_dead: lỗi token",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=COLORS["text_muted"]).pack(side="left", padx=(10, 0))
        self.table_wrap = ctk.CTkFrame(self, fg_color="transparent")
        self.table_wrap.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

    def refresh(self):
        model = build_model(self.app.config.tool_root, self.app.config.pool_root,
                            self.app.runlog, self.app.token_status)
        clear_frame(self.cards_frame)
        for i, (num, label) in enumerate([
                (model["total_pages"], "Page"),
                (model["linked"], "Đã gắn kênh"),
                (model["waiting"], "Đang đợi kênh"),
                (model["total_pool"], "Video trong pool"),
                (model["total_edited"], "Video đã edit"),
                (model["today_uploads"], "Đã đăng hôm nay")]):
            c = stat_card(self.cards_frame, num, label)
            c.grid(row=0, column=i, padx=(0, 10), sticky="nsew")
            self.cards_frame.grid_columnconfigure(i, weight=1)
        if model["backoff_until"]:
            self.backoff_label.configure(
                text=f"⚠ Đang backoff sau rate-limit đến {model['backoff_until']} — không tự chạy lại.")
        else:
            self.backoff_label.configure(text="")
        pages = store.filter_pages(model["pages"], self.search.get(),
                                   self.filter_var.get(), self.app.token_status)
        clear_frame(self.table_wrap)
        heading(self.table_wrap, f"Pages ({len(pages)})").pack(anchor="w", pady=(0, 8))
        cols = [("Page", 260), ("Kênh Douyin", 170), ("Pool", 70),
                ("Đã edit", 70), ("Hôm nay", 70), ("Trạng thái", 150)]
        rows = []
        for p in pages:
            rows.append([
                p["name"],
                p["channel"] or "—",
                str(p["pool_count"]),
                str(p["edited_count"]),
                f"{p['today']}/{self.app.config.get('daily_cap_per_page', 1)}",
                ("pill", p["status"]),
            ])
        if rows:
            data_table(self.table_wrap, cols, rows).pack(fill="both", expand=True)
        else:
            muted(self.table_wrap, "Không có page nào khớp bộ lọc.").pack(anchor="w")
