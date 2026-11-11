"""Quan ly Page: quet page, kiem tra token, sua tag ngach."""
import customtkinter as ctk

from gui.adapters import upload_adapter
from gui.core import store
from gui.theme import COLORS, PAD
from gui.views.common import (BaseView, clear_frame, data_table, ghost_button,
                              heading, labeled_entry, muted, primary_button,
                              title)


def build_model(tool_root, pool_root, token_status=None):
    pages = store.all_page_status(tool_root, pool_root)
    for p in pages:
        p["status"] = "linked" if not p["waiting"] else "waiting"
        p["token_status"] = (token_status or {}).get(p["id"], "unknown")
    return {"pages": pages}


class PagesView(BaseView):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        title(self, "Quản lý Page").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        muted(self, "Quét Page từ User Token, kiểm tra token từng page, gán tag ngách.").pack(
            anchor="w", padx=PAD, pady=(0, PAD))
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=PAD, pady=(0, PAD))
        primary_button(bar, "Quét Page từ token", self.on_scan).pack(side="left")
        ghost_button(bar, "Kiểm tra token tất cả", self.on_check_all).pack(side="left", padx=(10, 0))
        ghost_button(bar, "Làm mới token", self.on_refresh_tokens).pack(side="left", padx=(10, 0))
        # Tim kiem + loc
        bar2 = ctk.CTkFrame(self, fg_color="transparent")
        bar2.pack(fill="x", padx=PAD, pady=(0, PAD))
        self.search = ctk.CTkEntry(bar2, placeholder_text="Tìm page theo tên / ID...",
                                   fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                                   text_color=COLORS["text"], width=320, height=36)
        self.search.pack(side="left")
        self.search.bind("<KeyRelease>", lambda e: self.refresh())
        self.filter_var = ctk.StringVar(value="all")
        ctk.CTkOptionMenu(bar2, values=["all", "linked", "waiting", "token_dead"],
                          variable=self.filter_var, command=lambda v: self.refresh(),
                          fg_color=COLORS["bg_input"], button_color=COLORS["border"],
                          text_color=COLORS["text"], width=170, height=36).pack(side="left", padx=(10, 0))
        # Sua tag ngach
        niche_card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        niche_card.pack(fill="x", padx=PAD, pady=(0, PAD))
        heading(niche_card, "Tag ngách của page (dùng cho caption riêng)").pack(
            anchor="w", padx=PAD, pady=(PAD, 4))
        row = ctk.CTkFrame(niche_card, fg_color="transparent")
        row.pack(fill="x", padx=PAD, pady=(0, PAD))
        self.page_menu_var = ctk.StringVar(value="")
        self.page_menu = ctk.CTkOptionMenu(row, values=["(chưa có page)"],
                                           variable=self.page_menu_var,
                                           fg_color=COLORS["bg_input"],
                                           button_color=COLORS["border"],
                                           text_color=COLORS["text"], width=320, height=36)
        self.page_menu.pack(side="left")
        niche_frame, self.niche_entry = labeled_entry(row, "", "vd: mua sắm, phong cảnh...")
        self.niche_entry.configure(width=220)
        niche_frame.pack(side="left")
        ghost_button(row, "Lưu tag", self.on_save_niche).pack(side="left", padx=(10, 0))
        self.table_wrap = ctk.CTkFrame(self, fg_color="transparent")
        self.table_wrap.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

    def refresh(self):
        model = build_model(self.app.config.tool_root, self.app.config.pool_root,
                            self.app.token_status)
        pages = store.filter_pages(model["pages"], self.search.get(),
                                   self.filter_var.get(), self.app.token_status)
        folders = [p["folder"] for p in model["pages"]]
        self.page_menu.configure(values=folders or ["(chưa có page)"])
        if folders and not self.page_menu_var.get():
            self.page_menu_var.set(folders[0])
        clear_frame(self.table_wrap)
        heading(self.table_wrap, f"Pages ({len(pages)})").pack(anchor="w", pady=(0, 8))
        cols = [("Page", 240), ("ID", 160), ("Kênh", 150), ("Ngách", 120),
                ("Token file", 90), ("Token", 150), ("Trạng thái", 130)]
        rows = []
        for p in pages:
            rows.append([
                p["name"], p["id"], p["channel"] or "—", p["niche"] or "—",
                "Có" if p["has_token"] else "Không",
                ("pill", "token_" + p["token_status"]),
                ("pill", p["status"]),
            ])
        if rows:
            data_table(self.table_wrap, cols, rows).pack(fill="both", expand=True)
        else:
            muted(self.table_wrap, "Không có page nào khớp bộ lọc.").pack(anchor="w")

    # ---- actions (chay tren thread rieng qua app.run_task) ----
    def on_scan(self):
        token = self.app.config.get("user_token", "")
        if not token:
            self.app.log("Chưa có User Token — nhập token trong Cài đặt trước.")
            self.app.show_view("settings")
            return
        self.app.run_task("scan-pages", self._do_scan, token)

    def _do_scan(self, ctx, token):
        pages, err = upload_adapter.setup_pages(self.app.config.tool_root, token)
        ctx.log(f"Quét xong: {len(pages)} page.")
        if err:
            ctx.log(f"Lỗi API: {err}")
        return {"pages": len(pages)}

    def on_check_all(self):
        self.app.run_task("check-tokens", self._do_check_all)

    def _do_check_all(self, ctx):
        pages = upload_adapter.refresh_page_tokens(self.app.config.tool_root)
        for pg in pages:
            ok, name, err = upload_adapter.check_token(pg.get("token", ""))
            self.app.token_status[pg["id"]] = "alive" if ok else "dead"
            ctx.log(f"{pg['name']}: {'còn sống' if ok else 'CHẾT — ' + str((err or {}).get('message', ''))[:100]}")
        return {"checked": len(pages)}

    def on_refresh_tokens(self):
        self.app.run_task("refresh-tokens", self._do_refresh)

    def _do_refresh(self, ctx):
        pages = upload_adapter.refresh_page_tokens(self.app.config.tool_root)
        ctx.log(f"Đã làm mới token cho {len(pages)} page (fetch từ User Token).")
        return {"pages": len(pages)}

    def on_save_niche(self):
        folder = self.page_menu_var.get()
        tag = self.niche_entry.get().strip()
        if not folder or folder.startswith("("):
            return
        page_dir = store.Path(self.app.config.tool_root) / "pages" / folder
        store.write_niche(page_dir, tag)
        self.app.log(f"Đã lưu tag '{tag}' cho {folder}.")
        self.refresh()
