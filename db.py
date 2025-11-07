import sqlite3
from pathlib import Path
from utils import init_database  # falls init_database.py in utils liegt

# Pfad zur beschreibbaren Datenbank im AppData-Verzeichnis
APP_DATA = Path.home() / "AppData" / "Local" / "SVM-Jugend"
APP_DATA.mkdir(parents=True, exist_ok=True)

DB_FILE = APP_DATA / "training_manager.db"

def init_db():
    """
    Initialisiert die Datenbank, falls sie noch nicht existiert,
    inklusive Tabellen, Standardwerte und Versionierung.
    """
    # Wenn DB-Datei noch nicht existiert, init_database aufrufen
    if not DB_FILE.exists():
        init_database()

def query_db(sql, params=(), single=False, commit=True, return_id=False):
    """
    Führt eine SQL-Abfrage aus.
    
    Args:
        sql (str): SQL-Abfrage
        params (tuple): Parameter für SQL-Abfrage
        single (bool): Wenn True, gibt nur ein dict zurück
        commit (bool): Ob Änderungen committet werden
        return_id (bool): Wenn True, gibt lastrowid zurück

    Returns:
        Liste von dicts, ein dict oder lastrowid
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(sql, params)
    rv = c.fetchall()
    if commit:
        conn.commit()
    if return_id:
        last_id = c.lastrowid
        c.close()
        conn.close()
        return last_id
    c.close()
    conn.close()
    if single:
        return dict(rv[0]) if rv else None
    return [dict(r) for r in rv]
