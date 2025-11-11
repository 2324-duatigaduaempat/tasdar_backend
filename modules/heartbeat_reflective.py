import time, threading, queue, os
from datetime import datetime, timezone

class Heartbeat:
    def __init__(self, bpm:int=12):
        self.interval = 60.0 / max(1, bpm)  # denyut/minit
        self.q = queue.Queue(maxsize=1000)
        self._running = False
        self.thread = None

    def start(self):
        if self._running: return
        self._running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            beat = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "source": "tasdar_core/heartbeat.py",
                "bpm": round(60.0 / self.interval),
                "status": "alive"
            }
            try:
                self.q.put_nowait(beat)
            except queue.Full:
                pass
            time.sleep(self.interval)

    def get(self, timeout=2.0):
        try:
            return self.q.get(timeout=timeout)
        except queue.Empty:
            return None
