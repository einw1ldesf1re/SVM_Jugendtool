import sqlite3
from pathlib import Path
from datetime import datetime

from utils.logger import Logger
from utils.updater import get_current_version

# Pfad zur Datenbank im schreibbaren AppData-Verzeichnis
APP_DATA = Path.home() / "AppData" / "Local" / "SVM-Jugend"
APP_DATA.mkdir(parents=True, exist_ok=True)

DB_FILE = APP_DATA / "training_manager.db"

NEWEST_DATABESE_VERSION = 2

logger = Logger()

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
                geschlecht TEXT,
                rolle TEXT,
                eintrittsdatum DATE
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

        c.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('db_version', ?)", (NEWEST_DATABESE_VERSION,))
        logger.info("[DATABASE] Standard Datenbank wurde erstellt (v2)")
    elif (db_version == 1):
        # 1. Alte Tabelle umbenennen
        c.execute("ALTER TABLE mitglieder RENAME TO mitglieder_alt")

        # 2. Neue Tabelle mit gewünschter Reihenfolge anlegen
        c.execute("""
            CREATE TABLE mitglieder (
                mitglieder_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vorname TEXT,
                nachname TEXT,
                geburtsdatum DATE,
                geschlecht TEXT,
                rolle TEXT,
                eintrittsdatum DATE
            )
        """)

        # 3. Daten aus alter Tabelle übernehmen
        c.execute("""
            INSERT INTO mitglieder (mitglieder_id, vorname, nachname, geburtsdatum, rolle)
            SELECT mitglieder_id, vorname, nachname, geburtsdatum, rolle
            FROM mitglieder_alt
        """)

        # 4. Alte Tabelle löschen
        c.execute("DROP TABLE mitglieder_alt")
        c.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('db_version', ?)", (NEWEST_DATABESE_VERSION,))
        logger.info(f"[DATABASE] Datenbank wurde geupdatet (v1 -> v{NEWEST_DATABESE_VERSION})")
    else:
        logger.info(f"[DATABASE] '{DB_FILE}' initialisiert, Version: {NEWEST_DATABESE_VERSION}")
    conn.commit()
    conn.close()
    return DB_FILE
