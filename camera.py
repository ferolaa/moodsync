"""
camera.py — one shared camera reader for the whole app.
A background thread grabs frames continuously; everyone reads the latest one.
This avoids multiple components fighting over the same webcam (a macOS issue).
"""
import threading
import cv2

CAMERA_INDEX = 1


class Camera:
    def __init__(self, index=CAMERA_INDEX):
        self.index = index
        self._cap = None
        self._frame = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        self._cap = cv2.VideoCapture(self.index)
        if not self._cap.isOpened():
            raise RuntimeError("Could not open camera index %d" % self.index)
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def _loop(self):
        while not self._stop.is_set():
            ok, frame = self._cap.read()
            if ok:
                with self._lock:
                    self._frame = frame

    def read(self):
        """Return the latest frame (BGR numpy array) or None."""
        with self._lock:
            return None if self._frame is None else self._frame.copy()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        if self._cap:
            self._cap.release()
