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

    def set_badge_level(self, mitglied_id, badge_key, level):
        """Direkt ein bestimmtes Level für einen Badge setzen"""
        if level <= 0:
            return

        achieved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        query_db(
            """
            INSERT INTO badges_progress (mitglied_id, badge_key, current_level, progress, achieved_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(mitglied_id, badge_key)
            DO UPDATE SET current_level=excluded.current_level,
                        progress=excluded.progress,
                        achieved_at=excluded.achieved_at
            """,
            (mitglied_id, badge_key, level, level, achieved_at)
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

        # === 4. Leistungs-Badges pro Kategorie ===
        categories = query_db("SELECT kategorie_id, name FROM kategorien")
        cat_map = {c["name"].lower(): c["kategorie_id"] for c in categories}

        # Gruppierung definieren: nur Lichtgewehr + Luftgewehr zusammenfassen
        grouped = {
            "Gewehr": [cat_map.get("lichtgewehr"), cat_map.get("luftgewehr")]
        }

        processed_ids = set()

        # 🔧 Hilfsfunktion: Dynamisch aus YAML ermitteln, welches Level der Prozentsatz erreicht
        def get_dynamic_performance_level(badge_info, percent):
            levels = badge_info.get("levels", {})
            achieved_level = 0
            for lvl, info in sorted(levels.items(), key=lambda x: int(x[0])):
                threshold = info.get("threshold", 0)
                if percent >= threshold:
                    achieved_level = int(lvl)
                else:
                    break
            return achieved_level

        # 1️⃣ Gruppe "Gewehr" (Licht- & Luftgewehr zusammengefasst)
        gewehr_ids = [cid for cid in grouped["Gewehr"] if cid]
        if gewehr_ids:
            perf = self.get_group_performance(mitglied_id, gewehr_ids, last_n=5)
            badge_key = "Leistungsorden_Gewehr"
            badge_info = self.badges.get(badge_key, {})
            level = get_dynamic_performance_level(badge_info, perf)
            if level > 0:
                self.set_badge_level(mitglied_id, badge_key, level)
            processed_ids.update(gewehr_ids)

        # 2️⃣ Alle anderen Kategorien einzeln auswerten
        for name, cid in cat_map.items():
            if not cid or cid in processed_ids:
                continue  # Lichtgewehr + Luftgewehr wurden schon verarbeitet

            perf = self.get_group_performance(mitglied_id, [cid], last_n=5)
            badge_key = f"Leistungsorden_{name.capitalize()}"
            badge_info = self.badges.get(badge_key, {})
            level = get_dynamic_performance_level(badge_info, perf)

            if level > 0:
                self.set_badge_level(mitglied_id, badge_key, level)

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
    
    def get_group_performance(self, mid, categories, last_n=5):
        """Durchschnittliche Punkte (%) über mehrere Kategorien"""
        placeholders = ",".join("?" * len(categories))
        params = [mid] + categories + [last_n]

        results = query_db(f"""
            SELECT gesamtpunktzahl, schussanzahl
            FROM ergebnisse
            WHERE mitglied_id=? AND kategorie_id IN ({placeholders})
            ORDER BY ergebnis_id DESC
            LIMIT ?
        """, params)

        if not results:
            return 0

        total_points = sum(r["gesamtpunktzahl"] for r in results)
        max_points = sum(r["schussanzahl"] * 10 for r in results if r["schussanzahl"])

        return round((total_points / max_points) * 100, 1) if max_points else 0