# utils/logger.py
from pathlib import Path
import datetime
import os

class Logger:
    def __init__(self, log_dir=None, log_file_name="default.log"):
        if log_dir is None:
            # Standard: AppData\Local\SVM-Jugend\logs
            log_dir = Path(os.environ["LOCALAPPDATA"]) / "SVM-Jugend" / "logs"
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / log_file_name

    def _write(self, level, msg):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] [{level}] {msg}"
        # In Datei schreiben
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        # Optional auf Konsole ausgeben
        print(line)

    def info(self, msg):
        self._write("INFO", msg)

    def warn(self, msg):
        self._write("WARN", msg)

    def error(self, msg):
        self._write("ERROR", msg)
