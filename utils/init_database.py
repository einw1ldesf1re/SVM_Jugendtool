import sqlite3
from pathlib import Path
from datetime import datetime

# Pfad zur Datenbank im schreibbaren AppData-Verzeichnis
APP_DATA = Path.home() / "AppData" / "Local" / "SVM-Jugend"
APP_DATA.mkdir(parents=True, exist_ok=True)

DB_FILE = APP_DATA / "training_manager.db"

def init_database():
    """Initialisiert die SQLite-Datenbank, legt Tabellen an, füllt Standardwerte und verwaltet DB-Version."""

    # Verbindung zur SQLite-Datenbank herstellen (erstellt Datei automatisch)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # --- Meta-Tabelle für DB-Version ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()

    # aktuelle DB-Version ermitteln
    c.execute("SELECT value FROM meta WHERE key='db_version'")
    row = c.fetchone()
    db_version = int(row['value']) if row else 0

    # --- Migrationen / Tabellen anlegen ---
    if db_version < 1:
        # Tabelle: anschlaege
        c.execute("""
            CREATE TABLE IF NOT EXISTS anschlaege (
                anschlag_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        """)
        # Standardwerte
        c.execute("INSERT OR IGNORE INTO anschlaege (anschlag_id, name) VALUES (1, 'frei')")
        c.execute("INSERT OR IGNORE INTO anschlaege (anschlag_id, name) VALUES (2, 'aufgelegt')")

        # Tabelle: kategorien
        c.execute("""
            CREATE TABLE IF NOT EXISTS kategorien (
                kategorie_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        """)
        kategorien = ["Bogen", "Lichtgewehr", "Luftgewehr", "Luftpistole", "Blasrohr"]
        for idx, name in enumerate(kategorien, start=1):
            c.execute("INSERT OR IGNORE INTO kategorien (kategorie_id, name) VALUES (?, ?)", (idx, name))

        # Tabelle: mitglieder
        c.execute("""
            CREATE TABLE IF NOT EXISTS mitglieder (
                mitglieder_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vorname TEXT,
                nachname TEXT,
                geburtsdatum DATE,
                rolle TEXT
            )
        """)

        # Tabelle: training
        c.execute("""
            CREATE TABLE IF NOT EXISTS training (
                training_id INTEGER PRIMARY KEY AUTOINCREMENT,
                startzeit TIMESTAMP,
                endzeit TIMESTAMP
            )
        """)

        # Tabelle: training_kategorien
        c.execute("""
            CREATE TABLE IF NOT EXISTS training_kategorien (
                training_id INTEGER,
                kategorie_id INTEGER,
                PRIMARY KEY (training_id, kategorie_id)
            )
        """)

        # Tabelle: badges_progress
        c.execute("""
            CREATE TABLE IF NOT EXISTS badges_progress (
                mitglied_id INTEGER,
                badge_key TEXT,
                current_level INTEGER DEFAULT 0,
                progress INTEGER DEFAULT 0,
                achieved_at TEXT,
                PRIMARY KEY (mitglied_id, badge_key)
            )
        """)

        # Tabelle: ergebnisse
        c.execute("""
            CREATE TABLE IF NOT EXISTS ergebnisse (
                ergebnis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                training_id INTEGER,
                mitglied_id INTEGER,
                kategorie_id INTEGER,
                anschlag_id INTEGER,
                schussanzahl INTEGER,
                gesamtpunktzahl REAL,
                details_json TEXT
            )
        """)

        # DB-Version auf 1 setzen
        db_version = 1
        c.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('db_version', ?)", (db_version,))

    conn.commit()
    conn.close()
    print(f"[DB] '{DB_FILE}' initialisiert, Version: {db_version}")
    return DB_FILE
