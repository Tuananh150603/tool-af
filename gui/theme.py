"""Bang mau + chuan tham my dung XUYEN SUOT app (ghi lai trong README_GUI.md).

- Dark theme nhat quan, 1 mau nhan (accent) duy nhat cho nut chinh/link.
- Mau ngu nghia co dinh: xanh la = ok/da gan, vang = dang doi,
  do = loi/het han/nut nguy hiem.
- Font: Segoe UI (Windows), tieu de 16-18 bold, noi dung 12-13,
  log console monospace.
- Padding chuan 12-16px, card bo goc 10px.
"""
import re

COLORS = {
    "bg": "#121417",          # nen chinh toi
    "bg_card": "#1B1E23",     # nen the (card) hoi sang hon nen chinh
    "bg_input": "#23272E",    # nen o nhap
    "bg_hover": "#262A31",    # hover
    "bg_row_alt": "#17191D",  # hang xen ke trong bang
    "border": "#2E333B",      # vien
    "text": "#F2F3F5",        # chu trang
    "text_muted": "#9AA3AF",  # chu xam nhat
    "accent": "#2E86FF",      # MAU NHAN DUY NHAT (nut chinh / link)
    "accent_hover": "#1F6FEB",
    "accent_text": "#FFFFFF",
    "success": "#2ECC71",     # xanh la = ok / da gan
    "warning": "#F5B301",     # vang = dang doi
    "danger": "#E5484D",      # do = loi / het han / nut nguy hiem
    "danger_hover": "#C93A3F",
    "sidebar": "#0E1013",     # sidebar trai dam hon nen chinh
}

FONTS = {
    "title": ("Segoe UI", 18, "bold"),
    "heading": ("Segoe UI", 14, "bold"),
    "body": ("Segoe UI", 12),
    "body_bold": ("Segoe UI", 12, "bold"),
    "small": ("Segoe UI", 11),
    "small_bold": ("Segoe UI", 11, "bold"),
    "mono": ("Consolas", 11),
    "big_number": ("Segoe UI", 26, "bold"),
    "logo": ("Segoe UI", 20, "bold"),
}

PAD = 14            # padding chuan (12-16px)
PAD_SMALL = 8
CARD_RADIUS = 10
BUTTON_HEIGHT = 36
BUTTON_PRIMARY_HEIGHT = 40

# Trang thai page -> (nhan pill, mau chu tren pill, mau nen pill)
STATUS_PILLS = {
    "linked": ("Đã gắn kênh", COLORS["success"], "#123524"),
    "waiting": ("Đang đợi kênh", COLORS["warning"], "#3A2E00"),
    "token_alive": ("Token còn sống", COLORS["success"], "#123524"),
    "token_dead": ("Token chết/hết hạn", COLORS["danger"], "#3D1416"),
    "token_unknown": ("Chưa kiểm tra", COLORS["text_muted"], "#23272E"),
    "ok": ("OK", COLORS["success"], "#123524"),
    "failed": ("Lỗi", COLORS["danger"], "#3D1416"),
    "pending": ("Đang chờ", COLORS["warning"], "#3A2E00"),
    "skipped": ("Bỏ qua", COLORS["text_muted"], "#23272E"),
}

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def pill_for(status):
    """(nhan, mau_chu, mau_nen) cho 1 trang thai. Khong biet -> xam."""
    return STATUS_PILLS.get(
        status, ("Không rõ", COLORS["text_muted"], "#23272E"))


def validate_palette():
    """Kiem tra bang mau hop le: tat ca la hex 6 ky tu, accent chi co 1 mau,
    3 mau ngu nghia phan biet nhau."""
    errors = []
    for k, v in COLORS.items():
        if not HEX_RE.match(v):
            errors.append(f"{k}: '{v}' khong phai hex #RRGGBB")
    if len({COLORS["success"], COLORS["warning"], COLORS["danger"]}) != 3:
        errors.append("3 mau ngu nghia (success/warning/danger) phai khac nhau")
    if COLORS["accent"] in (COLORS["success"], COLORS["warning"], COLORS["danger"]):
        errors.append("accent khong duoc trung mau ngu nghia")
    return errors
