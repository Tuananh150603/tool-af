"""Link Pool: xem truoc (dry-run) / ap dung gan 1-1 / gan tay / go gan."""
import customtkinter as ctk

from gui.adapters import pool_adapter
from gui.core import store
from gui.theme import COLORS, PAD
from gui.views.common import (BaseView, clear_frame, data_table, danger_button,
                              ghost_button, heading, muted, primary_button,
                              title)


def build_model(tool_root, pool_root):
    """(kept, waiting, free_left, counts) tu dry-run + bang pool_map hien tai."""
    kept, waiting, free_left, counts = pool_adapter.preview(tool_root, pool_root)
    rows = store.read_pool_map(tool_root)
    return {"kept": kept, "waiting": waiting, "free_left": free_left,
            "counts": counts, "pool_map": rows}


class PoolView(BaseView):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        title(self, "Link Pool — Gán kênh Douyin cho Page").pack(
            anchor="w", padx=PAD, pady=(PAD, 4))
        muted(self, "STRICT 1-1: 1 page = 1 kênh duy nhất, không share kênh. "
                     "Xem trước (dry-run) không ghi file nào.").pack(
            anchor="w", padx=PAD, pady=(0, PAD))
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=PAD, pady=(0, PAD))
        primary_button(bar, "Xem trước gán (dry-run)", self.on_preview).pack(side="left")
        ghost_button(bar, "Áp dụng gán (ghi file)", self.on_apply).pack(side="left", padx=(10, 0))
        # Gan tay
        manual = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        manual.pack(fill="x", padx=PAD, pady=(0, PAD))
        heading(manual, "Gán tay 1 kênh cho 1 page").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        row = ctk.CTkFrame(manual, fg_color="transparent")
        row.pack(fill="x", padx=PAD, pady=(0, PAD))
        self.page_var = ctk.StringVar(value="")
        self.page_menu = ctk.CTkOptionMenu(row, values=["(chưa có page)"],
                                           variable=self.page_var,
                                           fg_color=COLORS["bg_input"],
                                           button_color=COLORS["border"],
                                           text_color=COLORS["text"], width=320, height=36)
        self.page_menu.pack(side="left")
        self.channel_var = ctk.StringVar(value="")
        self.channel_menu = ctk.CTkOptionMenu(row, values=["(chưa có kênh)"],
                                              variable=self.channel_var,
                                              fg_color=COLORS["bg_input"],
                                              button_color=COLORS["border"],
                                              text_color=COLORS["text"], width=220, height=36)
        self.channel_menu.pack(side="left", padx=(10, 0))
        ghost_button(row, "Gán", self.on_assign).pack(side="left", padx=(10, 0))
        danger_button(row, "Gỡ gán page đã chọn", self.on_unassign).pack(side="left", padx=(10, 0))
        self.table_wrap = ctk.CTkFrame(self, fg_color="transparent")
        self.table_wrap.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

    def refresh(self):
        model = build_model(self.app.config.tool_root, self.app.config.pool_root)
        pages = store.list_page_dirs(self.app.config.tool_root)
        folders = [p.name for p in pages]
        self.page_menu.configure(values=folders or ["(chưa có page)"])
        if folders and not self.page_var.get():
            self.page_var.set(folders[0])
        channels = [c["id"] for c in store.list_pool_channels(self.app.config.pool_root)]
        self.channel_menu.configure(values=channels or ["(chưa có kênh)"])
        if channels and not self.channel_var.get():
            self.channel_var.set(channels[0])
        clear_frame(self.table_wrap)
        heading(self.table_wrap,
                f"Kết quả gán (dry-run): {len(model['kept'])} page có kênh, "
                f"{len(model['waiting'])} page đang đợi, "
                f"{len(model['free_left'])} kênh trống").pack(anchor="w", pady=(0, 8))
        cols = [("Page", 320), ("Kênh Douyin", 180), ("Video", 80), ("Trạng thái", 150)]
        rows = []
        for pg in sorted(model["kept"]):
            cid = model["kept"][pg]
            rows.append([pg, cid, str(model["counts"].get(cid, 0)), ("pill", "linked")])
        for pg in sorted(model["waiting"]):
            rows.append([pg, "—", "0", ("pill", "waiting")])
        if rows:
            data_table(self.table_wrap, cols, rows).pack(fill="both", expand=True)
        else:
            muted(self.table_wrap, "Chưa có page nào.").pack(anchor="w")

    def on_preview(self):
        self.refresh()
        self.app.log("Xem trước (dry-run) — chưa ghi file nào.")

    def on_apply(self):
        self.app.run_task("pool-apply", self._do_apply)

    def _do_apply(self, ctx):
        kept, waiting, free_left, counts = pool_adapter.apply(
            self.app.config.tool_root, self.app.config.pool_root)
        ctx.log(f"Đã gán: {len(kept)} page có kênh, {len(waiting)} page vẫn đợi.")
        return {"kept": len(kept), "waiting": len(waiting)}

    def on_assign(self):
        page = self.page_var.get()
        channel = self.channel_var.get()
        if not page or page.startswith("(") or not channel or channel.startswith("("):
            return
        ok, msg = pool_adapter.assign(self.app.config.tool_root,
                                      self.app.config.pool_root, page, channel)
        self.app.log(msg)
        self.refresh()

    def on_unassign(self):
        page = self.page_var.get()
        if not page or page.startswith("("):
            return
        if pool_adapter.unassign(self.app.config.tool_root, page):
            self.app.log(f"Đã gỡ gán kênh của {page}.")
        else:
            self.app.log(f"{page} không có source.txt để gỡ.")
        self.refresh()
