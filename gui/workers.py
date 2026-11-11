"""Chay tac vu dai tren thread rieng: tien do + log ve UI qua queue,
nut Dung khan cap, sleep ngat duoc (khong doi het delay moi dung)."""
import queue
import random
import threading
import time
import traceback
import uuid


class TaskContext:
    """Doi tuong truyen vao ham tac vu: log / progress / is_stopped / sleep."""

    def __init__(self, runner, run_id):
        self._runner = runner
        self.run_id = run_id
        self.rng = random.Random()

    def log(self, msg):
        self._runner._put(("log", str(msg)))

    def progress(self, done, total, msg=""):
        self._runner._put(("progress", done, total, str(msg)))

    def is_stopped(self):
        return self._runner.stop_event.is_set()

    def sleep(self, seconds):
        """Nghi seconds giay, kiem tra stop moi 0.2s. Tra False neu bi dung."""
        end = time.monotonic() + max(0, float(seconds))
        while time.monotonic() < end:
            if self.is_stopped():
                return False
            time.sleep(min(0.2, max(0, end - time.monotonic())))
        return not self.is_stopped()


class TaskRunner:
    """Chay 1 tac vu tai 1 thoi diem. UI poll queue bang poll() trong after()."""

    def __init__(self):
        self.queue = queue.Queue()
        self.stop_event = threading.Event()
        self.thread = None
        self.current_name = None
        self.running = False

    def _put(self, item):
        self.queue.put(item)

    def start(self, name, fn, *args, **kwargs):
        """fn(ctx, *args, **kwargs) -> summary dict. Tra False neu dang chay."""
        if self.running:
            return False
        self.stop_event.clear()
        self.current_name = name
        self.running = True
        run_id = f"{name}-{uuid.uuid4().hex[:8]}"

        def _wrap():
            ctx = TaskContext(self, run_id)
            try:
                summary = fn(ctx, *args, **kwargs) or {}
                self._put(("done", name, run_id, summary))
            except Exception:
                self._put(("error", name, run_id, traceback.format_exc()))
            finally:
                self.running = False

        self.thread = threading.Thread(target=_wrap, daemon=True, name=f"ToolAF-{name}")
        self.thread.start()
        return True

    def stop(self):
        """Dung khan cap: dat co, tac vu tu thoat o diem kiem tra ke tiep."""
        self.stop_event.set()

    def poll(self):
        """Lay het event trong queue (goi tu main thread)."""
        items = []
        try:
            while True:
                items.append(self.queue.get_nowait())
        except queue.Empty:
            pass
        return items
