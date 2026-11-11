"""Test core/pipeline.py — jitter + thong so hieu luc."""
import random

from gui.core.config import DEFAULTS
from gui.core.pipeline import effective_params, sample_jitter, validate_jitter_cfg


def test_jitter_nam_trong_khoang():
    rng = random.Random(42)
    out = sample_jitter(DEFAULTS["jitter"], rng=rng)
    assert 1.03 <= out["speed"] <= 1.06
    assert 1.02 <= out["contrast"] <= 1.06
    assert 1.01 <= out["saturation"] <= 1.05
    assert 1.04 <= out["zoom"] <= 1.08
    assert 0.92 <= out["crop_w"] <= 0.96
    assert 0.91 <= out["crop_h"] <= 0.95
    assert isinstance(out["noise"], int) and 4 <= out["noise"] <= 8


def test_jitter_khac_nhau_moi_video():
    rng = random.Random(1)
    a = sample_jitter(DEFAULTS["jitter"], rng=rng)
    b = sample_jitter(DEFAULTS["jitter"], rng=rng)
    assert a != b  # lay mau lien tiep phai khac nhau (gan nhu chac chan)


def test_effective_params_tat_jitter_giu_hang_so_goc():
    base = dict(DEFAULTS["pipeline"])
    out = effective_params(base, False, DEFAULTS["jitter"], rng=random.Random(0))
    assert out == base


def test_effective_params_bat_jitter_chi_doi_khoa_jitter():
    base = dict(DEFAULTS["pipeline"])
    out = effective_params(base, True, DEFAULTS["jitter"], rng=random.Random(7))
    assert out["hflip"] is True and out["bgm_vol"] == 0.18 and out["trim_head"] == 1
    assert 1.03 <= out["speed"] <= 1.06


def test_validate_jitter_ok():
    assert validate_jitter_cfg(DEFAULTS["jitter"]) == []


def test_validate_jitter_loi():
    bad = {"speed": [1.06, 1.03], "contrast": [1.02, 1.06], "crop_w": [0.5, 1.2],
           "noise": [-1, 8]}
    errs = validate_jitter_cfg(bad)
    assert any("speed" in e for e in errs)
    assert any("crop_w" in e for e in errs)
    assert any("noise" in e for e in errs)
