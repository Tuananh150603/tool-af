"""Hen gio chay tu dong moi ngay (khi app dang mo). Ham thuan, test duoc."""
from datetime import datetime, time as dtime


def parse_hhmm(hhmm):
    """'08:00' -> time(8, 0). Tra None neu sai dinh dang."""
    try:
        h, m = hhmm.strip().split(":")
        h, m = int(h), int(m)
        if 0 <= h <= 23 and 0 <= m <= 59:
            return dtime(h, m)
    except Exception:
        return None
    return None


def next_run_datetime(now, hhmm):
    """Thoi diem chay ke tiep (datetime). Neu gio hen hom nay da qua -> ngay mai."""
    t = parse_hhmm(hhmm)
    if t is None or now is None:
        return None
    cand = datetime.combine(now.date(), t)
    if cand <= now:
        cand = datetime.combine(now.date().fromordinal(now.date().toordinal() + 1), t)
    return cand


def is_due(now, hhmm, last_run_date):
    """Den gio chay chua, va hom nay chua chay roi?
    last_run_date: 'YYYY-MM-DD' hoac None."""
    t = parse_hhmm(hhmm)
    if t is None or now is None:
        return False
    if now.time() < t:
        return False
    if last_run_date == now.date().isoformat():
        return False
    return True
