"""Cai dat: duong dan, token, FFmpeg, gioi han/ngay, jitter, an toan."""
from pathlib import Path

import customtkinter as ctk

from gui.core import ffmpeg as ffmpeg_core
from gui.core.pipeline import validate_jitter_cfg
from gui.theme import COLORS, PAD
from gui.views.common import (BaseView, ghost_button, heading, labeled_entry,
                              muted, primary_button, title)


def build_model(config):
    ff_path, ff_src = ffmpeg_core.resolve_ffmpeg(config.get("ffmpeg_bin", ""))
    return {"ffmpeg_path": ff_path, "ffmpeg_source": ff_src,
            "ffmpeg_version": ffmpeg_core.ffmpeg_version(ff_path)}


class SettingsView(BaseView):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        title(self, "Cài đặt").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        muted(self, "Cấu hình lưu trong gui_config.json ở thư mục tool (KHÔNG commit "
                     "lên git). Token cũng đồng bộ sang page_tok.txt để CLI gốc dùng được.").pack(
            anchor="w", padx=PAD, pady=(0, PAD))
        # Duong dan
        paths = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        paths.pack(fill="x", padx=PAD, pady=(0, PAD))
        heading(paths, "Đường dẫn").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        tool_frame, self.tool_entry = labeled_entry(paths, "Thư mục Tool AF (chứa Uploadvideo_multipage.py)",
                                           r"D:\Tool AF")
        tool_frame.pack(fill="x", padx=PAD, pady=(0, 4))
        ghost_button(paths, "Duyệt thư mục Tool AF...", self._browse_tool).pack(
            anchor="w", padx=PAD, pady=(0, 8))
        pool_frame, self.pool_entry = labeled_entry(paths, "Thư mục pool Douyin (chứa các ID kênh)",
                                           r"D:\Video Douyin Pool\data\关注")
        pool_frame.pack(fill="x", padx=PAD, pady=(0, 4))
        ghost_button(paths, "Duyệt thư mục pool...", self._browse_pool).pack(
            anchor="w", padx=PAD, pady=(0, PAD))
        # Token
        tok = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        tok.pack(fill="x", padx=PAD, pady=(0, PAD))
        heading(tok, "User Token Facebook").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        tok_frame, self.token_entry = labeled_entry(tok, "User Token (dùng để quét Page + làm mới token)",
                                            "EAA... (dán token vào đây)")
        self.token_entry.configure(show="•")
        tok_frame.pack(fill="x", padx=PAD, pady=(0, 4))
        muted(tok, "Token chỉ lưu local (gui_config.json + page_tok.txt, đều nằm trong "
                    ".gitignore) — không bao giờ đưa lên GitHub.").pack(
            anchor="w", padx=PAD, pady=(0, PAD))
        # FFmpeg
        ff = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        ff.pack(fill="x", padx=PAD, pady=(0, PAD))
        heading(ff, "FFmpeg đang dùng").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        self.ff_label = muted(ff, "")
        self.ff_label.pack(anchor="w", padx=PAD, pady=(0, 4))
        ff_frame, self.ff_entry = labeled_entry(ff, "Đường dẫn FFmpeg tay (để trống = tự tìm)",
                                         r"C:\ffmpeg\bin\ffmpeg.exe")
        ff_frame.pack(fill="x", padx=PAD, pady=(0, 4))
        ghost_button(ff, "Duyệt file ffmpeg...", self._browse_ffmpeg).pack(
            anchor="w", padx=PAD, pady=(0, PAD))
        # An toan
        safe = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        safe.pack(fill="x", padx=PAD, pady=(0, PAD))
        heading(safe, "An toàn & giới hạn (mặc định BẬT)").pack(anchor="w", padx=PAD, pady=(PAD, 4))
        self.stop_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(safe, text="Dừng đợt chạy khi gặp checkpoint / khóa / rate-limit (429)",
                        variable=self.stop_var, fg_color=COLORS["accent"],
                        text_color=COLORS["text"]).pack(anchor="w", padx=PAD, pady=2)
        self.cap_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(safe, text="Giới hạn số video đăng mỗi page mỗi ngày",
                        variable=self.cap_var, fg_color=COLORS["accent"],
                        text_color=COLORS["text"]).pack(anchor="w", padx=PAD, pady=2)
        row = ctk.CTkFrame(safe, fg_color="transparent")
        row.pack(fill="x", padx=PAD, pady=(0, 4))
        cap_frame, self.cap_entry = labeled_entry(row, "Trần video / page / ngày", "1")
        self.cap_entry.configure(width=100)
        cap_frame.pack(side="left", padx=(0, 10))
        backoff_frame, self.backoff_entry = labeled_entry(row, "Backoff sau 429 (phút)", "15")
        self.backoff_entry.configure(width=120)
        backoff_frame.pack(side="left")
        self.del_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(safe, text="XÓA video gốc sau khi edit (mặc định TẮT — nên để tắt)",
                        variable=self.del_var, fg_color=COLORS["danger"],
                        text_color=COLORS["danger"]).pack(anchor="w", padx=PAD, pady=(0, 4))
        # Caption rieng + jitter
        adv = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        adv.pack(fill="x", padx=PAD, pady=(0, PAD))
        heading(adv, "Nâng cao (mặc định TẮT = giữ đúng hành vi tool gốc)").pack(
            anchor="w", padx=PAD, pady=(PAD, 4))
        self.perpage_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(adv, text="Caption riêng theo page/ngách (page có kho riêng thì dùng kho đó)",
                        variable=self.perpage_var, fg_color=COLORS["accent"],
                        text_color=COLORS["text"]).pack(anchor="w", padx=PAD, pady=2)
        self.jitter_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(adv, text="Dao động nhẹ thông số xử lý mỗi video",
                        variable=self.jitter_var, fg_color=COLORS["accent"],
                        text_color=COLORS["text"]).pack(anchor="w", padx=PAD, pady=2)
        row2 = ctk.CTkFrame(adv, fg_color="transparent")
        row2.pack(fill="x", padx=PAD, pady=(0, PAD))
        jit_speed_frame, self.jit_speed = labeled_entry(row2, "Tốc độ min–max (vd 1.03-1.06)", "1.03-1.06")
        self.jit_speed.configure(width=160)
        jit_speed_frame.pack(side="left", padx=(0, 10))
        jit_contrast_frame, self.jit_contrast = labeled_entry(row2, "Contrast min–max", "1.02-1.06")
        self.jit_contrast.configure(width=160)
        jit_contrast_frame.pack(side="left")
        primary_button(self, "Lưu tất cả cài đặt", self.on_save).pack(
            anchor="w", padx=PAD, pady=(0, PAD))
        self._fill_from_config()

    def _fill_from_config(self):
        c = self.app.config
        self.tool_entry.delete(0, "end")
        self.tool_entry.insert(0, c.tool_root)
        self.pool_entry.delete(0, "end")
        self.pool_entry.insert(0, c.pool_root)
        self.token_entry.delete(0, "end")
        self.token_entry.insert(0, c.get("user_token", ""))
        self.ff_entry.delete(0, "end")
        self.ff_entry.insert(0, c.get("ffmpeg_bin", ""))
        self.stop_var.set(bool(c.get("stop_on_checkpoint", True)))
        self.cap_var.set(bool(c.get("daily_cap_enabled", True)))
        self.cap_entry.delete(0, "end")
        self.cap_entry.insert(0, str(c.get("daily_cap_per_page", 1)))
        self.backoff_entry.delete(0, "end")
        self.backoff_entry.insert(0, str(c.get("rate_limit_backoff_minutes", 15)))
        self.del_var.set(bool(c.get("delete_source_after_edit", False)))
        self.perpage_var.set(bool(c.get("per_page_captions_enabled", False)))
        self.jitter_var.set(bool(c.get("jitter_enabled", False)))
        j = c.jitter_cfg
        self.jit_speed.delete(0, "end")
        self.jit_speed.insert(0, f"{j['speed'][0]}-{j['speed'][1]}")
        self.jit_contrast.delete(0, "end")
        self.jit_contrast.insert(0, f"{j['contrast'][0]}-{j['contrast'][1]}")

    def refresh(self):
        model = build_model(self.app.config)
        src_label = {"config": "do Han chỉ tay", "FFMPEG_BIN": "biến môi trường FFMPEG_BIN",
                     "imageio-ffmpeg": "imageio-ffmpeg (đóng gói sẵn)",
                     "PATH": "lệnh ffmpeg trong PATH",
                     "not-found": "KHÔNG TÌM THẤY"}.get(model["ffmpeg_source"], model["ffmpeg_source"])
        self.ff_label.configure(
            text=f"FFmpeg: {model['ffmpeg_path'] or '(không có)'} — nguồn: {src_label}\n"
                 f"Phiên bản: {model['ffmpeg_version'] or '(không đọc được)'}")

    def _browse_tool(self):
        from tkinter import filedialog
        d = filedialog.askdirectory(title="Chọn thư mục Tool AF")
        if d:
            self.tool_entry.delete(0, "end")
            self.tool_entry.insert(0, d)

    def _browse_pool(self):
        from tkinter import filedialog
        d = filedialog.askdirectory(title="Chọn thư mục pool Douyin")
        if d:
            self.pool_entry.delete(0, "end")
            self.pool_entry.insert(0, d)

    def _browse_ffmpeg(self):
        from tkinter import filedialog
        p = filedialog.askopenfilename(title="Chọn file ffmpeg.exe",
                                       filetypes=[("ffmpeg", "ffmpeg.exe"), ("Tất cả", "*.*")])
        if p:
            self.ff_entry.delete(0, "end")
            self.ff_entry.insert(0, p)

    @staticmethod
    def _parse_range(text, default):
        try:
            lo, hi = text.replace(",", "-").split("-")
            return [float(lo), float(hi)]
        except Exception:
            return default

    def on_save(self):
        c = self.app.config
        c.data["tool_root"] = self.tool_entry.get().strip() or c.tool_root
        c.data["pool_root"] = self.pool_entry.get().strip() or c.pool_root
        token = self.token_entry.get().strip()
        c.set("user_token", token)
        c.set("ffmpeg_bin", self.ff_entry.get().strip())
        c.set("stop_on_checkpoint", self.stop_var.get())
        c.set("daily_cap_enabled", self.cap_var.get())
        try:
            c.set("daily_cap_per_page", max(1, int(self.cap_entry.get() or 1)))
        except Exception:
            c.set("daily_cap_per_page", 1)
        try:
            c.set("rate_limit_backoff_minutes", max(1, int(self.backoff_entry.get() or 15)))
        except Exception:
            c.set("rate_limit_backoff_minutes", 15)
        c.set("delete_source_after_edit", self.del_var.get())
        c.set("per_page_captions_enabled", self.perpage_var.get())
        c.set("jitter_enabled", self.jitter_var.get())
        j = c.jitter_cfg
        j["speed"] = self._parse_range(self.jit_speed.get(), j["speed"])
        j["contrast"] = self._parse_range(self.jit_contrast.get(), j["contrast"])
        errs = validate_jitter_cfg(j)
        if errs:
            self.app.log("Khoảng dao động sai: " + "; ".join(errs))
            return
        c.data["jitter"] = j
        c.save()
        # Dong bo token sang page_tok.txt de CLI goc dung duoc (file nay da gitignore)
        if token:
            try:
                (Path(c.tool_root) / "page_tok.txt").write_text(token, encoding="utf-8")
            except Exception as e:
                self.app.log(f"Không ghi được page_tok.txt: {e}")
        self.app.log("Đã lưu cài đặt.")
        self.refresh()
