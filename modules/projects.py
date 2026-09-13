from pathlib import Path
from datetime import datetime
import json
import os
import re
import threading
from uuid import uuid4

def safe_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", str(name).strip())
    return cleaned.strip("_")[:80] or "untitled"

class ProjectManager:
    def __init__(self, root="projects"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.current = None
        self.lock = threading.RLock()

    def start(self, name: str):
        with self.lock:
            if self.current is not None:
                self.end()
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            folder = self.root / f"{stamp}_{safe_name(name)}_{uuid4().hex[:6]}"
            folder.mkdir(exist_ok=False)
            for sub in ["photos", "videos", "notes", "reports"]:
                (folder / sub).mkdir()
            self.current = folder
            self._save_metadata({"name": name, "started": datetime.now().isoformat(),
                                 "ended": None, "events": []})
            self.log("Project started")
            return folder

    def ensure(self):
        with self.lock:
            if self.current is None:
                return self.start("Quick_Session")
            return self.current

    def metadata(self):
        with self.lock:
            return json.loads((self.ensure() / "project.json").read_text())

    def _save_metadata(self, data):
        with self.lock:
            folder = self.ensure()
            temporary = folder / (".project_" + uuid4().hex + ".tmp")
            try:
                with temporary.open("w", encoding="utf-8") as stream:
                    json.dump(data, stream, indent=2, ensure_ascii=False)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, folder / "project.json")
            finally:
                temporary.unlink(missing_ok=True)

    def log(self, message: str, kind="note"):
        with self.lock:
            data = self.metadata()
            data["events"].append({"time": datetime.now().isoformat(),
                                   "kind": kind, "message": str(message)})
            self._save_metadata(data)

    def end(self):
        with self.lock:
            if not self.current:
                return None
            data = self.metadata()
            data["ended"] = datetime.now().isoformat()
            self._save_metadata(data)
            ended = self.current
            self.current = None
            return ended

    def latest_project(self):
        with self.lock:
            candidates = sorted([p for p in self.root.iterdir()
                                 if p.is_dir() and (p / "project.json").is_file()], reverse=True)
            return candidates[0] if candidates else None
