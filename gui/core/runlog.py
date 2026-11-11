"""Nhat ky chay (run log) — file JSON local, KHONG commit len git.

Dung de:
- Chong dang trung: luu hash video goc da edit + hash file da dang + ID Facebook.
- Tiep tuc dot chay do: video nao dang pending/failed thi chay lai, khong chay lai tu dau.
- Gioi han video/ngay: dem so video da dang cua tung page trong ngay.
- Ghi su kien an toan: checkpoint / rate-limit / backoff / don du lieu cu.
File luu: <tool_root>/gui_runlog.json
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

RUNLOG_FILENAME = "gui_runlog.json"


def file_hash(path, chunk=1024 * 1024):
    """MD5 noi dung file (doc theo chunk, khong doi het file vao RAM)."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def today_str(now=None):
    return (now or datetime.now()).date().isoformat()


def _now_iso(now=None):
    return (now or datetime.now()).isoformat(timespec="seconds")


class RunLog:
    def __init__(self, path):
        self.path = Path(path)
        self.data = {"version": 1, "edits": [], "uploads": [], "events": [],
                     "state": {"backoff_until": None, "last_schedule_date": None}}
        self.load()

    def load(self):
        if self.path.is_file():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    for k in ("edits", "uploads", "events"):
                        if isinstance(raw.get(k), list):
                            self.data[k] = raw[k]
                    if isinstance(raw.get("state"), dict):
                        self.data["state"].update(raw["state"])
            except Exception:
                pass
        return self.data

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    # ---- edits ----
    def record_edit(self, run_id, page_id, page_folder, source_path, source_hash,
                    output_path, params, status, error="", now=None):
        entry = {"ts": _now_iso(now), "run_id": run_id, "page_id": page_id,
                 "page_folder": page_folder, "source_path": str(source_path),
                 "source_hash": source_hash, "output_path": str(output_path),
                 "output_name": Path(output_path).name if output_path else "",
                 "params": params, "status": status, "error": error}
        self.data["edits"].append(entry)
        self.save()
        return entry

    def is_source_edited(self, source_hash):
        return any(e.get("source_hash") == source_hash and e.get("status") == "ok"
                   for e in self.data["edits"])

    # ---- uploads ----
    def record_upload(self, run_id, page_id, page_folder, file_path, file_hash_value,
                      caption, comment, fb_video_id, status, error="", kind="",
                      now=None):
        entry = {"ts": _now_iso(now), "run_id": run_id, "page_id": page_id,
                 "page_folder": page_folder, "file_path": str(file_path),
                 "file_hash": file_hash_value, "caption": caption or "",
                 "comment": comment or "", "fb_video_id": fb_video_id or "",
                 "status": status, "error": error, "kind": kind}
        self.data["uploads"].append(entry)
        self.save()
        return entry

    def is_file_uploaded(self, file_hash_value):
        return any(u.get("file_hash") == file_hash_value and u.get("status") == "ok"
                   for u in self.data["uploads"])

    def mark_upload(self, run_id, file_hash_value, status, fb_video_id="",
                    error="", kind=""):
        """Cap nhat entry upload moi nhat (cung run_id + file_hash)."""
        for u in reversed(self.data["uploads"]):
            if u.get("run_id") == run_id and u.get("file_hash") == file_hash_value:
                u["status"] = status
                if fb_video_id:
                    u["fb_video_id"] = fb_video_id
                if error:
                    u["error"] = error
                if kind:
                    u["kind"] = kind
                self.save()
                return u
        return None

    def uploads_today(self, page_id, date=None):
        """So video page nay da dang thanh cong trong ngay (cho gioi han/ngay)."""
        d = date or today_str()
        return sum(1 for u in self.data["uploads"]
                   if u.get("page_id") == str(page_id)
                   and u.get("status") == "ok"
                   and str(u.get("ts", ""))[:10] == d)

    def pending_uploads(self, run_id):
        """Video dang do (pending/failed) cua 1 dot chay — de bam Tiep tuc."""
        return [u for u in self.data["uploads"]
                if u.get("run_id") == run_id and u.get("status") in ("pending", "failed")]

    def run_summary(self, run_id):
        ups = [u for u in self.data["uploads"] if u.get("run_id") == run_id]
        eds = [e for e in self.data["edits"] if e.get("run_id") == run_id]
        return {
            "uploads_ok": sum(1 for u in ups if u.get("status") == "ok"),
            "uploads_failed": sum(1 for u in ups if u.get("status") == "failed"),
            "uploads_skipped": sum(1 for u in ups if u.get("status", "").startswith("skipped")),
            "uploads_total": len(ups),
            "edits_ok": sum(1 for e in eds if e.get("status") == "ok"),
            "edits_failed": sum(1 for e in eds if e.get("status") == "failed"),
            "edits_total": len(eds),
        }

    def recent(self, n=100):
        """Lich su gan nhat (upload + edit + event) sap theo thoi gian giam dan."""
        items = []
        for u in self.data["uploads"]:
            items.append({"ts": u.get("ts", ""), "type": "upload", "data": u})
        for e in self.data["edits"]:
            items.append({"ts": e.get("ts", ""), "type": "edit", "data": e})
        for ev in self.data["events"]:
            items.append({"ts": ev.get("ts", ""), "type": "event", "data": ev})
        items.sort(key=lambda x: x["ts"], reverse=True)
        return items[:n]

    # ---- events (checkpoint / backoff / don dep / ...) ----
    def record_event(self, type_, message, data=None, now=None):
        entry = {"ts": _now_iso(now), "type": type_, "message": message,
                 "data": data or {}}
        self.data["events"].append(entry)
        self.save()
        return entry

    # ---- state ----
    def set_backoff(self, until_iso):
        self.data["state"]["backoff_until"] = until_iso
        self.save()

    def get_backoff(self):
        return self.data["state"].get("backoff_until")

    def clear_backoff(self):
        self.data["state"]["backoff_until"] = None
        self.save()

    def set_last_schedule_date(self, date_str):
        self.data["state"]["last_schedule_date"] = date_str
        self.save()

    def get_last_schedule_date(self):
        return self.data["state"].get("last_schedule_date")
