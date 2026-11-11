"""Caption & Comment: kho chung, kho rieng theo page/ngach, link Shopee."""
from pathlib import Path

import customtkinter as ctk

from gui.core import store
from gui.theme import COLORS, PAD
from gui.views.common import (BaseView, clear_frame, data_table, ghost_button,
                              heading, labeled_entry, muted, primary_button,
                              title)


def build_model(tool_root):
    captions = store.load_text_lines(Path(tool_root) / "captions.txt")
    comments = store.load_text_lines(Path(tool_root) / "comments.txt")
    links = store.extract_shopee_links(comments)
    pools = store.list_caption_pools(tool_root)
    per_page = []
    for d in store.list_page_dirs(tool_root):
        info = store.parse_info(d)
        own = store.load_text_lines(d / store.GUI_CAPTIONS_FILENAME)
        per_page.append({"folder": d.name, "name": info["name"],
                         "niche": store.read_niche(d), "own_count": len(own)})
    return {"captions": captions, "comments": comments, "links": links,
            "pools": pools, "per_page": per_page}


class CaptionsView(BaseView):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        title(self, "Caption & Comment").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        muted(self, "Kho chung dùng cho mọi page. Bật 'caption riêng theo page' trong "
                     "Cài đặt để page có kho riêng thì dùng kho đó, chưa có thì về kho chung.").pack(
            anchor="w", padx=PAD, pady=(0, PAD))
        # 2 kho chung canh nhau (khong dung tab)
        mid = ctk.CTkFrame(self, fg_color="transparent")
        mid.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))
        left = ctk.CTkFrame(mid, fg_color=COLORS["bg_card"], corner_radius=10)
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))
        heading(left, "Caption chung").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        self.cap_box = ctk.CTkTextbox(left, fg_color=COLORS["bg_input"],
                                      text_color=COLORS["text"],
                                      font=ctk.CTkFont("Segoe UI", 12), height=220)
        self.cap_box.pack(fill="both", expand=True, padx=PAD, pady=(0, 8))
        primary_button(left, "Lưu caption chung", self.on_save_caps).pack(
            anchor="w", padx=PAD, pady=(0, PAD))
        right = ctk.CTkFrame(mid, fg_color=COLORS["bg_card"], corner_radius=10)
        right.pack(side="left", fill="both", expand=True, padx=(5, 0))
        heading(right, "Comment chung (gắn link Shopee)").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        self.cmt_box = ctk.CTkTextbox(right, fg_color=COLORS["bg_input"],
                                      text_color=COLORS["text"],
                                      font=ctk.CTkFont("Segoe UI", 12), height=220)
        self.cmt_box.pack(fill="both", expand=True, padx=PAD, pady=(0, 8))
        primary_button(right, "Lưu comment chung", self.on_save_cmts).pack(
            anchor="w", padx=PAD, pady=(0, PAD))
        # Link Shopee
        link_card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        link_card.pack(fill="x", padx=PAD, pady=(0, PAD))
        heading(link_card, "Link Shopee Affiliate đang xoay vòng").pack(
            anchor="w", padx=PAD, pady=(PAD, 4))
        row = ctk.CTkFrame(link_card, fg_color="transparent")
        row.pack(fill="x", padx=PAD, pady=(0, 4))
        link_frame, self.link_entry = labeled_entry(row, "", "Link mới, vd: https://s.shopee.vn/xxxxxx")
        self.link_entry.configure(width=320)
        link_frame.pack(side="left")
        ghost_button(row, "Thêm link (tạo comment mới chứa link)",
                     self.on_add_link).pack(side="left", padx=(10, 0))
        self.links_wrap = ctk.CTkFrame(link_card, fg_color="transparent")
        self.links_wrap.pack(fill="x", padx=PAD, pady=(0, PAD))
        # Caption rieng theo page
        own_card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        own_card.pack(fill="x", padx=PAD, pady=(0, PAD))
        heading(own_card, "Caption riêng của từng page").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        row2 = ctk.CTkFrame(own_card, fg_color="transparent")
        row2.pack(fill="x", padx=PAD, pady=(0, 4))
        self.page_var = ctk.StringVar(value="")
        self.page_menu = ctk.CTkOptionMenu(row2, values=["(chưa có page)"],
                                           variable=self.page_var,
                                           fg_color=COLORS["bg_input"],
                                           button_color=COLORS["border"],
                                           text_color=COLORS["text"], width=320, height=36)
        self.page_menu.pack(side="left")
        ghost_button(row2, "Mở kho riêng để sửa", self.on_edit_own).pack(side="left", padx=(10, 0))
        self.own_box = ctk.CTkTextbox(own_card, fg_color=COLORS["bg_input"],
                                      text_color=COLORS["text"],
                                      font=ctk.CTkFont("Segoe UI", 12), height=120)
        self.own_box.pack(fill="x", padx=PAD, pady=(0, 8))
        primary_button(own_card, "Lưu caption riêng của page", self.on_save_own).pack(
            anchor="w", padx=PAD, pady=(0, PAD))
        self.per_page_wrap = ctk.CTkFrame(self, fg_color="transparent")
        self.per_page_wrap.pack(fill="x", padx=PAD, pady=(0, PAD))

    def refresh(self):
        model = build_model(self.app.config.tool_root)
        self.cap_box.delete("1.0", "end")
        self.cap_box.insert("1.0", "\n".join(model["captions"]))
        self.cmt_box.delete("1.0", "end")
        self.cmt_box.insert("1.0", "\n".join(model["comments"]))
        clear_frame(self.links_wrap)
        cols = [("Link Shopee", 320), ("Số comment dùng link này", 200)]
        rows = [[link, str(n)] for link, n in sorted(
            model["links"].items(), key=lambda kv: -kv[1])]
        if rows:
            data_table(self.links_wrap, cols, rows).pack(fill="x")
        else:
            muted(self.links_wrap, "Chưa có link Shopee nào trong kho comment.").pack(anchor="w")
        folders = [p["folder"] for p in model["per_page"]]
        self.page_menu.configure(values=folders or ["(chưa có page)"])
        if folders and not self.page_var.get():
            self.page_var.set(folders[0])
        clear_frame(self.per_page_wrap)
        cols2 = [("Page", 300), ("Ngách", 140), ("Caption riêng", 120)]
        rows2 = [[p["name"], p["niche"] or "—",
                  f"{p['own_count']} dòng" if p["own_count"] else "—"]
                 for p in model["per_page"]]
        if rows2:
            data_table(self.per_page_wrap, cols2, rows2).pack(fill="x")

    def _lines(self, box):
        return [l.strip() for l in box.get("1.0", "end").splitlines() if l.strip()]

    def on_save_caps(self):
        store.save_text_lines(Path(self.app.config.tool_root) / "captions.txt",
                              self._lines(self.cap_box))
        self.app.log("Đã lưu kho caption chung.")

    def on_save_cmts(self):
        store.save_text_lines(Path(self.app.config.tool_root) / "comments.txt",
                              self._lines(self.cmt_box))
        self.app.log("Đã lưu kho comment chung.")
        self.refresh()

    def on_add_link(self):
        link = self.link_entry.get().strip()
        if not link.startswith("http"):
            self.app.log("Link phải bắt đầu bằng http(s)://")
            return
        comments = store.load_text_lines(Path(self.app.config.tool_root) / "comments.txt")
        comments.append(f"Săn deal ngon ở đây {link} #sale")
        store.save_text_lines(Path(self.app.config.tool_root) / "comments.txt", comments)
        self.app.log(f"Đã thêm link {link} vào kho comment (1 comment mới).")
        self.refresh()

    def on_edit_own(self):
        folder = self.page_var.get()
        if not folder or folder.startswith("("):
            return
        page_dir = Path(self.app.config.tool_root) / "pages" / folder
        lines = store.load_text_lines(page_dir / store.GUI_CAPTIONS_FILENAME)
        self.own_box.delete("1.0", "end")
        self.own_box.insert("1.0", "\n".join(lines))

    def on_save_own(self):
        folder = self.page_var.get()
        if not folder or folder.startswith("("):
            return
        page_dir = Path(self.app.config.tool_root) / "pages" / folder
        store.save_text_lines(page_dir / store.GUI_CAPTIONS_FILENAME, self._lines(self.own_box))
        self.app.log(f"Đã lưu caption riêng cho {folder}.")
        self.refresh()
