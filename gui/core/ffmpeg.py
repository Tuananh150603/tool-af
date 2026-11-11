"""Tim FFmpeg dang dung + phien ban (hien thi trong Cai dat).

Thu tu uu tien (giong Processing.py goc):
1. Duong dan Han chi tay trong Cài đặt (config ffmpeg_bin)
2. Bien moi truong FFMPEG_BIN
3. FFmpeg dong goi san cua imageio-ffmpeg
4. Lenh ffmpeg trong PATH he thong
"""
import os
import shutil
import subprocess


def resolve_ffmpeg(config_bin=""):
    """Tra ve (duong_dan, nguon) — nguon: config | FFMPEG_BIN |
    imageio-ffmpeg | PATH | not-found."""
    if config_bin and os.path.exists(config_bin):
        return config_bin, "config"
    env = os.environ.get("FFMPEG_BIN", "")
    if env and os.path.exists(env):
        return env, "FFMPEG_BIN"
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe, "imageio-ffmpeg"
    except Exception:
        pass
    which = shutil.which("ffmpeg")
    if which:
        return which, "PATH"
    return "", "not-found"


def ffmpeg_version(path):
    """Dong dau tien cua `ffmpeg -version`, vd 'ffmpeg version 7.1 ...'."""
    if not path or not os.path.exists(path):
        return ""
    try:
        r = subprocess.run([path, "-version"], capture_output=True, text=True, timeout=10)
        out = (r.stdout or "") + (r.stderr or "")
        for line in out.splitlines():
            if line.strip():
                return line.strip()[:120]
    except Exception:
        return ""
    return ""
