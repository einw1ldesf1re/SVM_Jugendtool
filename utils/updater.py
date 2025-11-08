import tempfile
import pathlib
import requests
import os
import sys
import json
import subprocess

from utils.logger import Logger

logger = Logger()

UPDATE_INFO_URL = "https://raw.githubusercontent.com/einw1ldesf1re/SVM_Jugendtool/refs/heads/main/docs/svm_version.json"
INSTALLER_BASE_URL = "https://github.com/einw1ldesf1re/SVM_Jugendtool/releases/download"

if getattr(sys, 'frozen', False):
    # Läuft als exe → Pfad zur EXE
    BASE_DIR = pathlib.Path(sys.executable).parent
else:
    # Läuft als Skript → Pfad zum Projektroot
    BASE_DIR = pathlib.Path(__file__).parent.parent

CURRENT_VERSION_FILE = BASE_DIR / "version.json"

def get_current_version():
    try:
        with open(CURRENT_VERSION_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)["version"]
    except FileNotFoundError:
        return "0.0.0"
    
def build_installer_url(version):
    return f"{INSTALLER_BASE_URL}/v{version}/SVM-Jugend-Setup.exe"

def check_for_update():
    try:
        r = requests.get(UPDATE_INFO_URL, timeout=6)
        r.raise_for_status()
        data = r.json()
        latest_version = data["version"]

        current = get_current_version()
        logger.info(f"[UPDATE] Aktuell: {current}, Online: {latest_version}")

        if latest_version != current:
            logger.info("[UPDATE] Neue Version gefunden! Installer wird geladen...")
            installer_url = build_installer_url(latest_version)
            download_and_run_installer(installer_url, auto_restart=True)
        else:
            logger.info("[UPDATE] Keine neue Version verfügbar.")

    except Exception as e:
        logger.error(f"[UPDATE] Update-Check fehlgeschlagen: {e}")

def download_and_run_installer(url, auto_restart=False):
    """
    Lädt den Installer herunter und startet ihn.
    
    auto_restart=True  -> Auto-Update-Modus: Alte Version wird beendet,
                          Installer bekommt Parameter, um neue Version automatisch zu starten.
    auto_restart=False -> Manueller Start: Installer wird normal gestartet, kein Auto-Start.
    """
    temp_dir = tempfile.gettempdir()
    installer_path = pathlib.Path(temp_dir) / "SVM-Jugend-Setup.exe"

    # 1️⃣ Installer herunterladen
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(installer_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logger.info(f"[UPDATE] Installer gespeichert: {installer_path}")
    except Exception as e:
        logger.error(f"[UPDATE] Fehler beim Herunterladen des Installers: {e}")
        return

    # 2️⃣ Installer starten
    try:
        if auto_restart:
            current_exe = sys.executable  # Pfad zur laufenden exe
            param = f'--run-after-install="{current_exe}"'
            logger.info(f"[UPDATE] Starte Installer mit Auto-Update Parameter...")

            # Subprocess mit neuem Fenster für Sichtbarkeit
            subprocess.Popen(
                f'"{installer_path}" {param}',
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )

            # Alte Version sofort beenden
            sys.exit(0)

        else:
            logger.info(f"[UPDATE] Starte Installer normal...")
            # Manueller Start ohne Parameter, sichtbar
            os.startfile(installer_path)

    except Exception as e:
        logger.error(f"[UPDATE] Fehler beim Starten des Installers: {e}")
