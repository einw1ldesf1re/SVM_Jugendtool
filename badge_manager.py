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

        if str(next_level) in levels and progress >= levels[str(next_level)]["threshold"]:
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
            "SELECT badge_key, current_level, progress, achieved_at FROM badges_progress WHERE mitglied_id=?",
            (mitglied_id,)
        )
        return rows