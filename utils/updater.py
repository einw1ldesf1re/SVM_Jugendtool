# utils/updater.py
import json
import pathlib
import requests
import subprocess
import tempfile
import os
import sys

# URL zur Versionsinfo (raw auf main)
UPDATE_INFO_URL = "https://raw.githubusercontent.com/einw1ldesf1re/SVM_Jugendtool/refs/heads/main/docs/svm_version.json"
CURRENT_VERSION_FILE = pathlib.Path(__file__).parent.parent / "version.json"

# Basis-URL für die Installer-Datei
INSTALLER_BASE_URL = "https://github.com/einw1ldesf1re/SVM_Jugendtool/releases/download"

def get_current_version():
    with open(CURRENT_VERSION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["version"]

def build_installer_url(version):
    """
    Baut die Download-URL automatisch aus der Version:
    z.B.: v1.0.1 -> .../v1.0.1/SVM-Jugend-Setup.exe
    """
    return f"{INSTALLER_BASE_URL}/v{version}/SVM-Jugend-Setup.exe"

def check_for_update():
    try:
        r = requests.get(UPDATE_INFO_URL, timeout=6)
        r.raise_for_status()
        data = r.json()
        latest_version = data["version"]

        # URL automatisch erstellen
        installer_url = build_installer_url(latest_version)

        current = get_current_version()
        print(f"[UPDATE] Aktuell: {current}, Online: {latest_version}")

        if latest_version != current:
            print("[UPDATE] Neue Version gefunden! Installer wird geladen...")
            download_and_run_installer(installer_url)
        else:
            print("[UPDATE] Keine neue Version verfügbar.")
    except Exception as e:
        print(f"[UPDATE] Update-Check fehlgeschlagen: {e}")

def download_and_run_installer(url):
    temp_dir = tempfile.gettempdir()
    installer_path = pathlib.Path(temp_dir) / "SVM-Jugend-Setup.exe"

    try:
        # Installer herunterladen
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(installer_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(f"[UPDATE] Installer gespeichert unter {installer_path}")

        # Installer starten (non-blocking)
        subprocess.Popen([str(installer_path)], shell=True)

        # Sofort die aktuelle App beenden, damit Installer überschreiben kann
        sys.exit(0)

    except Exception as e:
        print(f"[UPDATE] Fehler beim Herunterladen oder Starten des Installers: {e}")
