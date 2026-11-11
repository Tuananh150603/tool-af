"""Widget dung chung theo theme (dark, 1 accent, pill trang thai).

Moi man hinh dung cac helper nay de can le / co chu / mau sac nhat quan.
"""
import customtkinter as ctk

from gui.theme import COLORS, FONTS, PAD, PAD_SMALL, pill_for


class BaseView(ctk.CTkScrollableFrame):
    """Khung cuon chung cho moi man hinh. Ghi de refresh() o view con."""

    def __init__(self, parent, app, **kw):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0,
                         scrollbar_button_color=COLORS["border"], **kw)
        self.app = app

    def refresh(self):
        pass


def card(parent):
    return ctk.CTkFrame(parent, fg_color=COLORS["bg_card"],
                        corner_radius=10, border_width=1,
                        border_color=COLORS["border"])


def title(parent, text):
    return ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(*FONTS["title"]),
                        text_color=COLORS["text"])


def heading(parent, text):
    return ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(*FONTS["heading"]),
                        text_color=COLORS["text"])


def muted(parent, text):
    return ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(*FONTS["small"]),
                        text_color=COLORS["text_muted"])


def body_label(parent, text):
    return ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(*FONTS["body"]),
                        text_color=COLORS["text"])


def primary_button(parent, text, command):
    return ctk.CTkButton(parent, text=text, command=command,
                         fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                         text_color=COLORS["accent_text"], height=40,
                         font=ctk.CTkFont(*FONTS["body_bold"]), corner_radius=8)


def danger_button(parent, text, command):
    return ctk.CTkButton(parent, text=text, command=command,
                         fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                         text_color="#FFFFFF", height=36,
                         font=ctk.CTkFont(*FONTS["body_bold"]), corner_radius=8)


def ghost_button(parent, text, command):
    return ctk.CTkButton(parent, text=text, command=command,
                         fg_color="transparent", hover_color=COLORS["bg_hover"],
                         text_color=COLORS["text"], border_width=1,
                         border_color=COLORS["border"], height=36,
                         font=ctk.CTkFont(*FONTS["body"]), corner_radius=8)


def labeled_entry(parent, label, placeholder=""):
    """(frame, entry): o nhap co nhan ro + placeholder vi du."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    lbl = ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(*FONTS["small_bold"]),
                       text_color=COLORS["text"])
    lbl.pack(anchor="w")
    entry = ctk.CTkEntry(frame, placeholder_text=placeholder,
                         fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                         text_color=COLORS["text"],
                         placeholder_text_color=COLORS["text_muted"],
                         font=ctk.CTkFont(*FONTS["body"]), height=36, corner_radius=8)
    entry.pack(fill="x", pady=(4, 0))
    return frame, entry


def pill(parent, status):
    """Nhan trang thai bo tron co mau (xanh la/vang/do theo theme)."""
    label, fg, bg = pill_for(status)
    return ctk.CTkLabel(parent, text=f" {label} ", font=ctk.CTkFont(*FONTS["small_bold"]),
                        text_color=fg, fg_color=bg, corner_radius=10)


def stat_card(parent, number, label):
    """The so lieu lon + nhan nho (Dashboard)."""
    frame = card(parent)
    num = ctk.CTkLabel(frame, text=str(number),
                       font=ctk.CTkFont(*FONTS["big_number"]),
                       text_color=COLORS["text"])
    num.pack(padx=PAD, pady=(PAD, 0), anchor="w")
    lbl = ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(*FONTS["small"]),
                       text_color=COLORS["text_muted"])
    lbl.pack(padx=PAD, pady=(0, PAD), anchor="w")
    return frame


def data_table(parent, columns, rows):
    """Bang du lieu: header dam + hang xen ke 2 tong nen.
    columns: [(tieu_de, rong_px)].
    rows: list[list[cell]]; cell = str | ("pill", status) | ("muted", str)."""
    wrap = ctk.CTkFrame(parent, fg_color="transparent")
    table_header(wrap, columns).pack(fill="x")
    for ri, row in enumerate(rows):
        bg = COLORS["bg_row_alt"] if ri % 2 else COLORS["bg_card"]
        fr = ctk.CTkFrame(wrap, fg_color=bg, corner_radius=6)
        fr.pack(fill="x", pady=2)
        for ci, cell in enumerate(row):
            w = columns[ci][1]
            if isinstance(cell, tuple) and cell[0] == "pill":
                pill(fr, cell[1]).grid(row=0, column=ci, padx=PAD_SMALL, pady=6, sticky="w")
            elif isinstance(cell, tuple) and cell[0] == "muted":
                ctk.CTkLabel(fr, text=cell[1], font=ctk.CTkFont(*FONTS["body"]),
                             text_color=COLORS["text_muted"], width=w, anchor="w").grid(
                                 row=0, column=ci, padx=PAD_SMALL, pady=6, sticky="w")
            else:
                ctk.CTkLabel(fr, text=str(cell), font=ctk.CTkFont(*FONTS["body"]),
                             text_color=COLORS["text"], width=w, anchor="w").grid(
                                 row=0, column=ci, padx=PAD_SMALL, pady=6, sticky="w")
    return wrap


def clear_frame(frame):
    for w in frame.winfo_children():
        w.destroy()


def table_header(parent, columns):
    """Hang tieu de bang: chu dam, nen hoi dam. columns: [(text, width)]."""
    frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_hover"], corner_radius=6)
    for i, (text, width) in enumerate(columns):
        lbl = ctk.CTkLabel(frame, text=text, font=ctk.CTkFont(*FONTS["small_bold"]),
                           text_color=COLORS["text"], width=width, anchor="w")
        lbl.grid(row=0, column=i, padx=PAD_SMALL, pady=6, sticky="w")
    return frame
