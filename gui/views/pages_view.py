"""Quan ly Page: quet page, kiem tra token, sua tag ngach, xoa page chet."""
from pathlib import Path

import customtkinter as ctk

from gui.adapters import upload_adapter
from gui.core import store
from gui.theme import COLORS, FONTS, PAD, PAD_SMALL
from gui.views.common import (BaseView, clear_frame, danger_button,
                              ghost_button, heading, labeled_entry, muted,
                              pill, primary_button, title)


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
        muted(self, "Quét Page từ User Token, kiểm tra token từng page, gán tag ngách. "
                     "Page chết thì bấm Xóa page ở từng dòng — thư mục được chuyển "
                     "vào pages_deleted/ để khôi phục được, không xóa hẳn.").pack(
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
        # Moi dong bang: {folder, name, delete_button}
        self._rows = []

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
        self._rows = []
        heading(self.table_wrap, f"Pages ({len(pages)})").pack(anchor="w", pady=(0, 8))
        if not pages:
            muted(self.table_wrap, "Không có page nào khớp bộ lọc.").pack(anchor="w")
            return
        cols = [("Page", 240), ("ID", 160), ("Kênh", 150), ("Ngách", 120),
                ("Token file", 90), ("Token", 150), ("Trạng thái", 130), ("", 90)]
        header = ctk.CTkFrame(self.table_wrap, fg_color=COLORS["bg_hover"], corner_radius=6)
        header.pack(fill="x", pady=2)
        for ci, (text, w) in enumerate(cols):
            ctk.CTkLabel(header, text=text, font=ctk.CTkFont(*FONTS["small_bold"]),
                         text_color=COLORS["text"], width=w, anchor="w").grid(
                             row=0, column=ci, padx=PAD_SMALL, pady=6, sticky="w")
        for ri, p in enumerate(pages):
            bg = COLORS["bg_row_alt"] if ri % 2 else COLORS["bg_card"]
            fr = ctk.CTkFrame(self.table_wrap, fg_color=bg, corner_radius=6)
            fr.pack(fill="x", pady=2)
            cells = [
                (p["name"], 240), (p["id"], 160), (p["channel"] or "—", 150),
                (p["niche"] or "—", 120),
                ("Có" if p["has_token"] else "Không", 90),
            ]
            for ci, (text, w) in enumerate(cells):
                ctk.CTkLabel(fr, text=text, font=ctk.CTkFont(*FONTS["body"]),
                             text_color=COLORS["text"], width=w, anchor="w").grid(
                                 row=0, column=ci, padx=PAD_SMALL, pady=6, sticky="w")
            pill(fr, "token_" + p["token_status"]).grid(
                row=0, column=5, padx=PAD_SMALL, pady=6, sticky="w")
            pill(fr, p["status"]).grid(
                row=0, column=6, padx=PAD_SMALL, pady=6, sticky="w")
            row = {"folder": p["folder"], "name": p["name"]}
            btn = danger_button(fr, "Xóa page",
                                lambda f=p["folder"], n=p["name"]: self.on_delete_page(f, n))
            btn.grid(row=0, column=7, padx=PAD_SMALL, pady=6)
            row["delete_button"] = btn
            self._rows.append(row)

    def on_delete_page(self, folder, name):
        """Xoa page chet khoi tool: hoi xac nhan, chuyen thu muc page sang
        pages_deleted/ (khong xoa han), ghi su kien vao run-log, lam moi."""
        from tkinter import messagebox
        page_dir = Path(self.app.config.tool_root) / "pages" / folder
        n_edited = store.count_videos(page_dir / "edited")
        if not messagebox.askyesno(
                "Xóa page khỏi tool",
                f"Xóa page '{name}' ({folder}) khỏi tool?\n\n"
                f"Thư mục page sẽ được CHUYỂN sang pages_deleted/ (không xóa hẳn — "
                f"muốn khôi phục thì chuyển thư mục đó về lại pages/). "
                f"Page sẽ biến khỏi Dashboard, Upload, Link Pool.\n"
                f"Video đã edit trong page: {n_edited}."):
            return
        try:
            dest = store.delete_page(self.app.config.tool_root, folder)
        except ValueError as e:
            self.app.log(f"Không xóa được page {folder}: {e}")
            return
        self.app.log(f"Đã xóa page {name} ({folder}) — đã chuyển vào {dest.name}.")
        self.app.runlog.record_event(
            "page_delete", f"Đã xóa page {name} ({folder})",
            {"page": folder, "dest": dest.name})
        self.refresh()

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
