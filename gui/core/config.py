"""Cau hinh local cua GUI Tool AF.

File luu: <tool_root>/gui_config.json  (KHONG commit len git — xem .gitignore).
Token user luu o day + dong bo sang page_tok.txt de CLI goc van dung duoc.
"""
import copy
import json
import sys
from pathlib import Path

CONFIG_FILENAME = "gui_config.json"

# Mac dinh = dung hanh vi tool goc. Cac muc an toan mac dinh BAT,
# cac muc doi hanh vi mac dinh TAT (chi bat khi Han chinh tay).
DEFAULTS = {
    "tool_root": "",
    "pool_root": r"D:\Video Douyin Pool\data\关注",
    "user_token": "",
    "ffmpeg_bin": "",
    "delete_source_after_edit": False,   # mac dinh KHONG xoa video goc sau edit
    # --- An toan (mac dinh BAT) ---
    "stop_on_checkpoint": True,          # dung dot chay khi gap checkpoint/429/khoa
    "daily_cap_enabled": True,           # gioi han video/ngay
    "daily_cap_per_page": 1,             # nhip van hanh cua Han: 1 video/page/ngay
    "rate_limit_backoff_minutes": 15,    # 429 -> nghi toi thieu truoc khi chay tay lai
    # --- Doi hanh vi (mac dinh TAT = giu dung tool goc) ---
    "per_page_captions_enabled": False,  # caption rieng theo page/ngach
    "jitter_enabled": False,             # dao dong nhe thong so xu ly moi video
    "jitter": {
        "speed": [1.03, 1.06],
        "contrast": [1.02, 1.06],
        "saturation": [1.01, 1.05],
        "zoom": [1.04, 1.08],
        "crop_w": [0.92, 0.96],
        "crop_h": [0.91, 0.95],
        "noise": [4, 8],
    },
    # --- Thong so pipeline mac dinh (dung hang so goc) ---
    "pipeline": {
        "speed": 1.045, "zoom": 1.06, "crop_w": 0.94, "crop_h": 0.93,
        "hflip": True, "contrast": 1.04, "saturation": 1.03, "noise": 6,
        "trim_head": 1, "trim_tail": 2.5, "bgm_vol": 0.18, "use_bgm": True,
    },
    "upload": {
        "gap_seconds": 10, "comment_delay": 15,
        "big_first": False, "shuffle": True,
    },
    "schedule": {
        "enabled": False, "time": "08:00",
        "run_edit": True, "run_upload": True,
    },
}


def _looks_like_tool_root(path):
    """Thu muc goc cua tool: chua Uploadvideo_multipage.py hoac thu muc pages/."""
    p = Path(path)
    return (p / "Uploadvideo_multipage.py").is_file() or (p / "pages").is_dir()


def default_tool_root():
    """Thu muc goc cua tool.

    - Chay bang Python: thu muc cha cua gui/ (gui/core/config.py -> parents[2]).
    - Chay bang .exe dong goi (PyInstaller onefile): __file__ nam trong thu muc
      tam _MEI (bi xoa khi thoat) nen KHONG dung duoc — lay thu muc chua file
      .exe (sys.executable) roi di nguoc len toi da 3 cap de tim thu muc chua
      Uploadvideo_multipage.py / pages/.
    """
    if getattr(sys, "frozen", False):
        start = Path(sys.executable).resolve().parent
    else:
        start = Path(__file__).resolve().parents[2]
    cur = start
    for _ in range(4):
        if _looks_like_tool_root(cur):
            return str(cur)
        if cur.parent == cur:
            break
        cur = cur.parent
    return str(start)


class Config:
    def __init__(self, data=None, path=None):
        self.path = Path(path) if path else None
        # Deepcopy: moi Config co dict rieng, khong dung chung DEFAULTS
        # (truoc day sua cfg.data["schedule"] lam nhiem sang moi instance).
        self.data = copy.deepcopy(DEFAULTS)
        if data:
            self._deep_merge(data)
        if not self.data.get("tool_root"):
            self.data["tool_root"] = default_tool_root()
        # Nho tool_root luc khoi tao: save() chi doi file khi tool_root
        # bi doi sau do (vd Han doi trong Cai dat); neu khong doi thi ghi
        # dung vao self.path (ke ca khi path duoc truyen tuong minh).
        self._constructed_tool_root = self.data.get("tool_root")

    def _deep_merge(self, src):
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(self.data.get(k), dict):
                self.data[k].update(copy.deepcopy(v))
            else:
                self.data[k] = copy.deepcopy(v)

    @staticmethod
    def _read_file(path):
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    @classmethod
    def load(cls, tool_root=None):
        root = Path(tool_root) if tool_root else Path(default_tool_root())
        data = cls._read_file(root / CONFIG_FILENAME)
        # Ton trong tool_root da luu (Han doi trong Cai dat): neu thu muc do
        # ton tai thi dung no, ke ca khi file config dang nam o cho khac.
        saved_root = (data or {}).get("tool_root")
        if saved_root and Path(saved_root).is_dir() and Path(saved_root) != root:
            root = Path(saved_root)
            data2 = cls._read_file(root / CONFIG_FILENAME)
            if data2 is not None:
                data = data2
        cfg = cls(data, path=root / CONFIG_FILENAME)
        cfg.data["tool_root"] = str(root)
        return cfg

    def save(self):
        # Chi doi file khi tool_root bi doi sau luc khoi tao (Han doi trong
        # Cai dat thi file config phai di theo sang thu muc moi). Neu khong
        # doi thi ghi dung vao self.path (ke ca path truyen tuong minh).
        if self.path is None or self.data.get("tool_root") != self._constructed_tool_root:
            self.path = Path(self.data["tool_root"]) / CONFIG_FILENAME
            self._constructed_tool_root = self.data.get("tool_root")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)
        return self.path

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value

    @property
    def tool_root(self):
        return self.data["tool_root"]

    @property
    def pool_root(self):
        return self.data["pool_root"]

    @property
    def pipeline_params(self):
        p = dict(DEFAULTS["pipeline"])
        p.update(self.data.get("pipeline") or {})
        return p

    @property
    def jitter_cfg(self):
        j = {k: list(v) for k, v in DEFAULTS["jitter"].items()}
        j.update(self.data.get("jitter") or {})
        return j
