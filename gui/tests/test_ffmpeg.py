"""Test core/ffmpeg.py — tim FFmpeg + phien ban."""
import os
import shutil

from gui.core.ffmpeg import ffmpeg_version, resolve_ffmpeg


def test_resolve_config_bin_uu_tien_nhat(tmp_path):
    fake = tmp_path / "ffmpeg"
    fake.write_bytes(b"#!/bin/sh\necho hi\n")
    path, src = resolve_ffmpeg(str(fake))
    assert path == str(fake) and src == "config"


def test_resolve_config_bin_khong_ton_tai_bo_qua(tmp_path):
    path, src = resolve_ffmpeg(str(tmp_path / "khong-co"))
    assert src in ("FFMPEG_BIN", "imageio-ffmpeg", "PATH", "not-found")
    assert path != str(tmp_path / "khong-co")


def test_resolve_path_he_thong():
    if not shutil.which("ffmpeg"):
        return
    path, src = resolve_ffmpeg("")
    assert src == "PATH"
    assert path == shutil.which("ffmpeg")


def test_ffmpeg_version_that():
    ff = shutil.which("ffmpeg")
    if not ff:
        return
    v = ffmpeg_version(ff)
    assert v.startswith("ffmpeg version")


def test_ffmpeg_version_rong():
    assert ffmpeg_version("") == ""
    assert ffmpeg_version("/khong/tontai/ffmpeg") == ""


def test_env_ffmpeg_bin(monkeypatch, tmp_path):
    fake = tmp_path / "ffmpeg-env"
    fake.write_bytes(b"x")
    monkeypatch.setenv("FFMPEG_BIN", str(fake))
    path, src = resolve_ffmpeg("")
    assert (path, src) == (str(fake), "FFMPEG_BIN")
