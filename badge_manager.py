import yaml

from db import query_db
from datetime import datetime


class BadgeManager:
    def __init__(self):
        with open("assets/badges/badges.yml", "r", encoding="utf-8") as f:
            self.badges = yaml.safe_load(f)

    def update_badge(self, mitglied_id, badge_key, progress_value=None):
        """Überprüft und aktualisiert das Badge-Level"""

        badge_info = self.badges.get(badge_key)
        if not badge_info:
            return

        # Lade aktuellen Fortschritt
        row = query_db(
            "SELECT current_level, progress FROM badges_progress WHERE mitglied_id=? AND badge_key=?",
            (mitglied_id, badge_key),
            single=True
        )

        current_level = row["current_level"] if row else 0
        old_progress = row["progress"] if row else 0

        # Fortschritt bestimmen
        progress = progress_value if progress_value is not None else old_progress

        # Nächstes Level prüfen
        next_level = current_level + 1
        levels = badge_info["levels"]

        if next_level in levels and progress >= levels[next_level]["threshold"]:
            # Neues Level erreicht
            current_level = next_level
            achieved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"🎖️ Mitglied {mitglied_id} hat {badge_key} Level {next_level} erreicht!")

            query_db(
                """
                INSERT INTO badges_progress (mitglied_id, badge_key, current_level, progress, achieved_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(mitglied_id, badge_key)
                DO UPDATE SET current_level=excluded.current_level,
                              progress=excluded.progress,
                              achieved_at=excluded.achieved_at
                """,
                (mitglied_id, badge_key, current_level, progress, achieved_at)
            )
        else:
            # Nur Fortschritt aktualisieren
            query_db(
                """
                INSERT INTO badges_progress (mitglied_id, badge_key, current_level, progress)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(mitglied_id, badge_key)
                DO UPDATE SET progress=excluded.progress
                """,
                (mitglied_id, badge_key, current_level, progress)
            )

    def get_badges(self, mitglied_id):
        """Alle Badges und Level eines Mitglieds laden"""
        rows = query_db(
            "SELECT badge_key, current_level, progress, achieved_at FROM badges_progress WHERE mitglied_id=? AND current_level > 0",
            (mitglied_id,)
        )
        return rows
    
    def update_all_badges(self, mitglied_id):
        """Aktualisiert alle Badge-Typen eines Mitglieds"""

        # === 1. Normaler Trainings-Progress ===
        total_trainings = query_db("""
            SELECT COUNT(DISTINCT training_id) AS total
            FROM ergebnisse
            WHERE mitglied_id=?
        """, (mitglied_id,), single=True)["total"]
        self.update_badge(mitglied_id, "Trainingsorden", total_trainings)

        # === 2. Trainings in Folge berechnen ===
        consecutive = self.get_consecutive_trainings(mitglied_id)
        self.update_badge(mitglied_id, "Trainingsserie", consecutive)
     
        # === 3. Anzahl der Schuss ===
        amount_shots = self.get_amount_shots(mitglied_id)
        self.update_badge(mitglied_id, "Schussanzahl", amount_shots)

    def get_consecutive_trainings(self, mid):
        
        """
        Zählt, wie viele Trainings ein Mitglied in Folge besucht hat,
        basierend auf der Reihenfolge der von dir angelegten Trainings.
        """
        # Alle Trainings absteigend nach startzeit
        trainings = query_db("""
            SELECT t.training_id
            FROM training t
            ORDER BY t.startzeit DESC
        """)

        if not trainings:
            return 0

        # Trainings, die das Mitglied besucht hat
        attended = set(r['training_id'] for r in query_db("""
            SELECT training_id
            FROM ergebnisse
            WHERE mitglied_id = ?
        """, (mid,)))

        consecutive = 0
        for t in trainings:
            if t['training_id'] in attended:
                consecutive += 1
            else:
                break  # Kette unterbrochen

        return consecutive

    def get_amount_shots(self, mid):
        result = query_db("""
            SELECT SUM(schussanzahl) AS total_shots
            FROM ergebnisse
            WHERE mitglied_id=?
        """, (mid,), single=True)

        if result and result['total_shots'] is not None:
            return result['total_shots']
        return 0