"""Thong so pipeline + dao dong nhe (jitter) moi video.

Mac dinh (tat jitter): dung dung hang so goc trong Processing.DEFAULT_PARAMS.
Khi bat jitter: moi video lay 1 bo thong so lay mau ngau nhien trong khoang
Han chinh duoc (Cai dat), de khong phai video nao cung qua dung 1 cong thuc.
"""
import random

# Khoa nao duoc jitter + kieu gia tri (float lam tron 3 chu so, noise la int).
JITTER_KEYS = ("speed", "contrast", "saturation", "zoom", "crop_w", "crop_h", "noise")


def sample_jitter(jitter_cfg, rng=None):
    """Tra ve dict cac thong so da lay mau trong khoang jitter_cfg.
    jitter_cfg: {"speed": [min, max], ...} (noise: [min, max] int)."""
    rng = rng or random
    out = {}
    for key in JITTER_KEYS:
        lo, hi = jitter_cfg.get(key, [None, None])
        if lo is None or hi is None:
            continue
        if key == "noise":
            out[key] = rng.randint(int(lo), int(hi))
        else:
            out[key] = round(rng.uniform(float(lo), float(hi)), 3)
    return out


def effective_params(base_params, jitter_enabled, jitter_cfg, rng=None):
    """Thong so thuc dung cho 1 video: base + jitter (neu bat)."""
    params = dict(base_params)
    if jitter_enabled:
        params.update(sample_jitter(jitter_cfg, rng=rng))
    return params


def validate_jitter_cfg(jitter_cfg):
    """Kiem tra khoang jitter hop le: tra ve list loi (rong = OK)."""
    errors = []
    for key in JITTER_KEYS:
        rng = jitter_cfg.get(key)
        if rng is None:
            continue
        if not isinstance(rng, (list, tuple)) or len(rng) != 2:
            errors.append(f"{key}: cần khoảng [min, max]")
            continue
        lo, hi = rng
        try:
            lo, hi = float(lo), float(hi)
        except Exception:
            errors.append(f"{key}: min/max phải là số")
            continue
        if lo > hi:
            errors.append(f"{key}: min ({lo}) lớn hơn max ({hi})")
        if key == "speed" and (lo <= 0 or hi <= 0):
            errors.append("speed: phải > 0")
        if key in ("crop_w", "crop_h") and not (0 < lo <= hi <= 1):
            errors.append(f"{key}: phải trong khoảng (0, 1]")
        if key == "noise" and (lo < 0 or hi < 0):
            errors.append("noise: không được âm")
    return errors
