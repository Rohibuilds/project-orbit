import threading
import cv2
from datetime import datetime
from pathlib import Path
from .resistor import analyze_resistor

class VisionSystem:
    def __init__(self, camera_index=0, width=1280, height=720, fps=20, disabled=False):
        self.lock = threading.RLock()
        self.cap = None if disabled else cv2.VideoCapture(camera_index)
        if self.cap is not None:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.fps = max(1, min(60, int(fps)))
        self.writer = None
        self.recording_path = None

    def ok(self):
        with self.lock:
            return self.cap is not None and self.cap.isOpened()

    def read(self):
        with self.lock:
            if not self.ok():
                return False, None
            ok, frame = self.cap.read()
            if ok and self.writer is not None:
                self.writer.write(frame)
            return ok, frame

    def snapshot(self, folder: Path, frame=None):
        if frame is None:
            return None
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
        return path if cv2.imwrite(str(path), frame) else None

    def start_recording(self, folder: Path, frame_size):
        with self.lock:
            if self.writer is not None:
                return self.recording_path
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / f"video_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.mp4"
            writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), self.fps, frame_size)
            if not writer.isOpened():
                writer.release()
                return None
            self.writer = writer
            self.recording_path = path
            return path

    def stop_recording(self):
        with self.lock:
            path = self.recording_path
            if self.writer is not None:
                self.writer.release()
            self.writer = None
            self.recording_path = None
            return path

    def resistor(self, frame):
        return analyze_resistor(frame)

    def close(self):
        with self.lock:
            self.stop_recording()
            if self.cap is not None:
                self.cap.release()
                self.cap = None
