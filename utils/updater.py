# utils/updater.py
import json
import pathlib
import requests
import subprocess
import tempfile
import os

# URL zur Versionsinfo (raw auf main)
UPDATE_INFO_URL = "https://einw1ldesf1re.github.io/SVM-Jugend/svm_version.json"
CURRENT_VERSION_FILE = pathlib.Path(__file__).parent.parent / "version.json"

def get_current_version():
    with open(CURRENT_VERSION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["version"]

def check_for_update():
    try:
        r = requests.get(UPDATE_INFO_URL, timeout=6)
        r.raise_for_status()
        data = r.json()
        latest_version = data["version"]
        installer_url = data["url"]
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

    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(installer_path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)

    print(f"[UPDATE] Installer gespeichert unter {installer_path}")
    # Starten des Installers (non-blocking)
    subprocess.Popen([str(installer_path)])
    # Sofort beenden, damit Installer überschreiben kann
    os._exit(0)
