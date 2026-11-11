"""Test gui/theme.py — bang mau nhat quan, khong mau lung tung."""
from gui.theme import COLORS, FONTS, STATUS_PILLS, pill_for, validate_palette


def test_palette_hop_le():
    assert validate_palette() == []


def test_chi_1_mau_nhan():
    assert COLORS["accent"] == "#2E86FF"
    assert COLORS["accent"] != COLORS["success"]
    assert COLORS["accent"] != COLORS["danger"]


def test_mau_ngu_nghia_co_dinh():
    assert COLORS["success"] == "#2ECC71"   # xanh la = ok/da gan
    assert COLORS["warning"] == "#F5B301"   # vang = dang doi
    assert COLORS["danger"] == "#E5484D"    # do = loi/het han


def test_nen_toi_nhat_quan():
    # nen chinh toi nhat, the sang hon chut, sidebar dam nhat
    def lum(hexcolor):
        r, g, b = (int(hexcolor[i:i + 2], 16) for i in (1, 3, 5))
        return 0.299 * r + 0.587 * g + 0.114 * b
    assert lum(COLORS["sidebar"]) < lum(COLORS["bg"]) < lum(COLORS["bg_card"])


def test_font_segoe_ui():
    assert FONTS["title"][0] == "Segoe UI"
    assert FONTS["title"][1] == 18
    assert FONTS["body"][1] == 12
    assert FONTS["mono"][0] == "Consolas"


def test_pill_for():
    label, fg, bg = pill_for("linked")
    assert "gắn" in label and fg == COLORS["success"]
    label, fg, bg = pill_for("waiting")
    assert "đợi" in label and fg == COLORS["warning"]
    label, fg, bg = pill_for("token_dead")
    assert fg == COLORS["danger"]
    label, fg, bg = pill_for("khong-ton-tai")
    assert fg == COLORS["text_muted"]


def test_status_pills_du_trang_thai():
    for key in ("linked", "waiting", "token_alive", "token_dead",
                "token_unknown", "ok", "failed", "pending", "skipped"):
        assert key in STATUS_PILLS
