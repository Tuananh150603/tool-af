"""Cau hinh local cua GUI Tool AF.

File luu: <tool_root>/gui_config.json  (KHONG commit len git — xem .gitignore).
Token user luu o day + dong bo sang page_tok.txt de CLI goc van dung duoc.
"""
import copy
import json
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


def default_tool_root():
    """Thu muc goc cua tool = thu muc cha cua gui/."""
    return str(Path(__file__).resolve().parents[2])


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

    def _deep_merge(self, src):
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(self.data.get(k), dict):
                self.data[k].update(copy.deepcopy(v))
            else:
                self.data[k] = copy.deepcopy(v)

    @classmethod
    def load(cls, tool_root=None):
        root = Path(tool_root) if tool_root else Path(default_tool_root())
        path = root / CONFIG_FILENAME
        data = None
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                data = None
        cfg = cls(data, path=path)
        cfg.data["tool_root"] = str(root)
        return cfg

    def save(self):
        if self.path is None:
            self.path = Path(self.data["tool_root"]) / CONFIG_FILENAME
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
