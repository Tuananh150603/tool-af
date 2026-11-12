"""Load script goc tu tool root bang duong dan TUONG MINH.

Ly do can loader rieng (thay cho `import` + sys.path):
- Trong .exe dong goi (PyInstaller onefile), FrozenImporter co the tra ve
  ban copy dong goi san thay vi file that trong tool root.
- Neu 3 script trong tool root la ban cu (thang 10/2026, truoc khi refactor
  cho GUI), adapter se vo phai AttributeError/TypeError kho hieu GIUA CHUNG
  dot chay (vd: Uploadvideo_multipage khong co clear_api_error).
Loader nay luon doc file that tren dia, va kiem tra cac ham can thiet co
ton tai khong — thieu thi bao loi RO RANG ngay tu dau, huong dan copy 3
file script moi tu repo vao tool root, thay vi vo loi giua dot chay.

Cache: moi file chi exec 1 lan cho den khi file thay doi tren dia (theo
mtime). Nhu vay module tra ve la CUNG 1 object trong suot phien chay —
giong `import` thuong — de trang thai module (LAST_API_ERROR) va cac
monkeypatch trong test duoc giu nguyen.
"""
import importlib.util
from pathlib import Path

UPDATE_HINT = (
    "Script goc trong tool root la ban cu — copy 3 file moi tu repo "
    "(Uploadvideo_multipage.py, link_pool.py, "
    "video_processing/Processing.py) vao thu muc tool root roi chay lai."
)

_CACHE = {}  # str(path) -> (mtime_ns, module)


def load_script(tool_root, rel_path, required=()):
    """Load file script tai tool_root/rel_path, kiem tra required attrs.

    Tra ve module (cache theo duong dan + mtime). Thieu file hoac thieu
    ham -> RuntimeError noi ro.
    """
    path = Path(tool_root) / rel_path
    if not path.is_file():
        raise RuntimeError(
            f"Khong thay file {rel_path} trong tool root {tool_root}. {UPDATE_HINT}")
    key = str(path.resolve())
    mtime = path.stat().st_mtime_ns
    cached = _CACHE.get(key)
    if cached is not None and cached[0] == mtime:
        m = cached[1]
    else:
        name = "_toolaf_" + Path(rel_path).stem
        spec = importlib.util.spec_from_file_location(name, str(path))
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Khong load duoc {rel_path}. {UPDATE_HINT}")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _CACHE[key] = (mtime, m)
    missing = [a for a in required if not hasattr(m, a)]
    if missing:
        raise RuntimeError(
            f"{rel_path} thieu: {', '.join(missing)}. {UPDATE_HINT}")
    return m
