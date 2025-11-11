# tasdar_core/heartbeat.py
import threading, time, queue

class Heartbeat:
    def __init__(self, bpm=12):
        self.bpm = bpm
        self._interval = 60.0 / self.bpm
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        while not self._stop_event.is_set():
            ts = time.time()
            beat = {"timestamp": ts, "status": "alive"}
            try:
                self._queue.put(beat, timeout=0.1)
            except queue.Full:
                pass
            time.sleep(self._interval)

    def start(self):
        if not self._thread.is_alive():
            self._thread.start()

    def stop(self):
        self._stop_event.set()

    def get(self, timeout=2.0):
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None
