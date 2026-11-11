"""Test gui/workers.py — thread rieng, dung khan cap, sleep ngat duoc."""
import time

from gui.workers import TaskRunner


def _wait_done(runner, timeout=5.0):
    end = time.monotonic() + timeout
    events = []
    while time.monotonic() < end:
        events += runner.poll()
        if any(e[0] in ("done", "error") for e in events):
            return events
        time.sleep(0.05)
    return events


def test_chay_xong_tra_summary():
    r = TaskRunner()
    assert r.start("demo", lambda ctx: {"ok": 2}) is True
    events = _wait_done(r)
    done = [e for e in events if e[0] == "done"]
    assert len(done) == 1
    assert done[0][3] == {"ok": 2}
    assert r.running is False


def test_log_va_progress_ve_queue():
    r = TaskRunner()

    def job(ctx):
        ctx.log("hello")
        ctx.progress(1, 2, "dang lam")
        return {}

    r.start("demo", job)
    events = _wait_done(r)
    kinds = [e[0] for e in events]
    assert "log" in kinds and "progress" in kinds
    assert [e for e in events if e[0] == "log"][0][1] == "hello"


def test_khong_chay_2_tac_vu_cung_luc():
    r = TaskRunner()
    r.start("a", lambda ctx: (ctx.sleep(2), {"x": 1})[1])
    assert r.start("b", lambda ctx: {}) is False
    _wait_done(r, timeout=6.0)


def test_dung_khan_cap():
    r = TaskRunner()

    def job(ctx):
        for _ in range(100):
            if ctx.is_stopped():
                return {"stopped": True}
            time.sleep(0.05)
        return {"stopped": False}

    r.start("demo", job)
    time.sleep(0.2)
    r.stop()
    events = _wait_done(r)
    done = [e for e in events if e[0] == "done"]
    assert done and done[0][3] == {"stopped": True}


def test_sleep_ngat_duoc():
    r = TaskRunner()
    seen = {}

    def job(ctx):
        t0 = time.monotonic()
        ok = ctx.sleep(30)
        seen["elapsed"] = time.monotonic() - t0
        seen["ok"] = ok
        return {}

    r.start("demo", job)
    time.sleep(0.3)
    r.stop()
    _wait_done(r)
    assert seen["ok"] is False
    assert seen["elapsed"] < 5  # khong doi het 30s


def test_loi_khong_lam_chet_runner():
    r = TaskRunner()
    r.start("demo", lambda ctx: 1 / 0)
    events = _wait_done(r)
    assert any(e[0] == "error" for e in events)
    assert r.running is False
    assert r.start("demo2", lambda ctx: {"ok": True}) is True
    _wait_done(r)
