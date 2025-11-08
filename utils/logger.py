# utils/logger.py
import pathlib
import datetime
import os

class Logger:
    def __init__(self, log_dir=None, log_file_name="default.log"):
        """
        log_dir: Pfad zum Ordner, in dem die Log-Datei liegen soll.
                 Wenn None, dann im gleichen Ordner wie die exe.
        """
        if log_dir is None:
            self.log_dir = pathlib.Path(__file__).parent.parent  # Root-Ordner des Projekts
        else:
            self.log_dir = pathlib.Path(log_dir)

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
