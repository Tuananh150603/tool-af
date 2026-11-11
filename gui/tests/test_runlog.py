"""Test core/runlog.py — ghi/doc nhat ky, chong trung, gioi han/ngay, tiep tuc."""
from gui.core.runlog import RunLog, file_hash, today_str


def test_mark_upload_cap_nhat_pending(tmp_path):
    log = RunLog(tmp_path / "gui_runlog.json")
    log.record_upload("r1", "111", "p1", "/e/a.mp4", "h1", "", "", "", "pending")
    updated = log.mark_upload("r1", "h1", "ok", fb_video_id="123")
    assert updated["status"] == "ok" and updated["fb_video_id"] == "123"
    assert log.is_file_uploaded("h1") is True
    assert log.mark_upload("r1", "khong-co", "ok") is None


def test_file_hash(tmp_path):
    f = tmp_path / "v.mp4"
    f.write_bytes(b"abc123")
    import hashlib
    assert file_hash(f) == hashlib.md5(b"abc123").hexdigest()


def test_edit_dedup(tmp_path):
    log = RunLog(tmp_path / "gui_runlog.json")
    assert log.is_source_edited("hash1") is False
    log.record_edit("run1", "111", "p1", "/pool/a.mp4", "hash1", "/edited/a_edit.mp4",
                    {"speed": 1.045}, "ok")
    assert log.is_source_edited("hash1") is True
    assert log.is_source_edited("hash2") is False


def test_upload_dedup_va_ngay(tmp_path):
    log = RunLog(tmp_path / "gui_runlog.json")
    log.record_upload("run1", "111", "p1", "/edited/a.mp4", "fh1",
                      "cap", "cmt", "999", "ok")
    assert log.is_file_uploaded("fh1") is True
    assert log.uploads_today("111") == 1
    assert log.uploads_today("222") == 0
    log.record_upload("run1", "111", "p1", "/edited/b.mp4", "fh2",
                      "cap", "cmt", "1000", "failed", error="timeout")
    assert log.uploads_today("111") == 1  # chi dem thanh cong


def test_pending_va_summary(tmp_path):
    log = RunLog(tmp_path / "gui_runlog.json")
    log.record_upload("run9", "111", "p1", "/e/a.mp4", "h1", "", "", "", "pending")
    log.record_upload("run9", "111", "p1", "/e/b.mp4", "h2", "", "", "", "failed")
    log.record_upload("run9", "111", "p1", "/e/c.mp4", "h3", "", "", "5", "ok")
    log.record_upload("run8", "111", "p1", "/e/d.mp4", "h4", "", "", "", "pending")
    assert len(log.pending_uploads("run9")) == 2
    s = log.run_summary("run9")
    assert s["uploads_ok"] == 1 and s["uploads_failed"] == 1 and s["uploads_total"] == 3


def test_event_va_recent(tmp_path):
    log = RunLog(tmp_path / "gui_runlog.json")
    log.record_event("checkpoint", "Dung dot chay do checkpoint", {"page_id": "111"})
    log.record_upload("r1", "111", "p1", "/e/a.mp4", "h1", "", "", "5", "ok")
    recent = log.recent(10)
    assert len(recent) == 2
    assert recent[0]["ts"] >= recent[1]["ts"]
    assert any(i["type"] == "event" for i in recent)


def test_backoff_state(tmp_path):
    log = RunLog(tmp_path / "gui_runlog.json")
    assert log.get_backoff() is None
    log.set_backoff("2026-11-12T08:15:00")
    assert log.get_backoff() == "2026-11-12T08:15:00"
    log.clear_backoff()
    assert log.get_backoff() is None


def test_persistence_qua_2_instance(tmp_path):
    p = tmp_path / "gui_runlog.json"
    log1 = RunLog(p)
    log1.record_edit("r1", "111", "p1", "/s.mp4", "hh", "/o.mp4", {}, "ok")
    log1.record_event("cap", "Dat tran ngay")
    log2 = RunLog(p)
    assert log2.is_source_edited("hh") is True
    assert len(log2.data["events"]) == 1


def test_today_str():
    assert len(today_str()) == 10  # YYYY-MM-DD
