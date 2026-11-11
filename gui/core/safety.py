"""Phan loai loi Facebook API -> quyet dinh co dung dot chay khong.

Tool goc chi in loi ra man hinh roi chay tiep. GUI phai dung ngay khi gap:
checkpoint / khoa tai khoan / rate-limit (429) / token het han — de Han xu ly
tay truoc khi tai khoan bi danh dau them.
"""
from datetime import datetime, timedelta

CHECKPOINT_SUBCODES = {459, 460, 463, 464, 467, 469, 470}
RATE_LIMIT_CODES = {4, 17, 32, 341, 613, 80004}

# Cac loai loi phai DUNG dot chay (khi stop_on_checkpoint bat).
STOP_KINDS = {"checkpoint", "blocked", "rate_limit", "token"}

KIND_LABELS = {
    "checkpoint": "Facebook yêu cầu xác minh (checkpoint)",
    "blocked": "Tài khoản/Page bị chặn tạm thời",
    "rate_limit": "Bị giới hạn tốc độ (rate-limit / 429)",
    "token": "Token hết hạn hoặc không hợp lệ",
    "other": "Lỗi API khác",
}


def classify_fb_error(err):
    """err: dict {"status","code","subcode","message"} (nhu LAST_API_ERROR).
    Tra ve loai loi hoac None neu khong co loi."""
    if not err:
        return None
    status = err.get("status")
    code = err.get("code")
    sub = err.get("subcode")
    msg = str(err.get("message") or "").lower()
    if status == 429 or code in RATE_LIMIT_CODES:
        return "rate_limit"
    if "checkpoint" in msg or "verify your identity" in msg or "verify your account" in msg:
        return "checkpoint"
    if code == 190 and sub in CHECKPOINT_SUBCODES:
        return "checkpoint"
    if code == 368:
        return "blocked"
    if code in (190, 102):
        return "token"
    if code is not None:
        return "other"
    return None


def should_stop(kind, stop_on_checkpoint=True):
    """Co dung dot chay khi gap loai loi nay khong."""
    if kind is None:
        return False
    if not stop_on_checkpoint:
        return False
    return kind in STOP_KINDS


def backoff_until(now, minutes):
    """Thoi diem het backoff (datetime) sau khi gap 429."""
    if now is None:
        now = datetime.now()
    return now + timedelta(minutes=max(1, int(minutes)))


def backoff_remaining_seconds(now, until_iso):
    """So giay con lai cua backoff; <=0 nghia la het backoff."""
    if not until_iso:
        return 0
    try:
        until = datetime.fromisoformat(until_iso)
    except Exception:
        return 0
    return (until - (now or datetime.now())).total_seconds()
