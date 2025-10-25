from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QComboBox, QSpinBox, QDoubleSpinBox, QHBoxLayout, QPushButton
from PyQt6.QtCore import QDateTime
from db import query_db

class ResultDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Ergebnis hinzufügen" if data is None else "Ergebnis bearbeiten")
        self.data = data
        self.setup_ui()
        if data:
            self.load_data(data)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # === Training-Auswahl ===
        self.training_cb = QComboBox()
        trainings = query_db("SELECT training_id, startzeit, endzeit FROM training ORDER BY startzeit DESC")
        self.trainings_map = {}
        for t in trainings:
            start_dt = QDateTime.fromString(t['startzeit'], "yyyy-MM-dd HH:mm:ss")
            end_dt = QDateTime.fromString(t['endzeit'], "yyyy-MM-dd HH:mm:ss") if t['endzeit'] else None
            display = f"{start_dt.toString('dd.MM.yyyy / HH:mm')} – {end_dt.toString('HH:mm') if end_dt else '?'}"
            self.training_cb.addItem(display)
            self.trainings_map[display] = t['training_id']
        form_layout.addRow("Training:", self.training_cb)

        # === Mitglied-Auswahl ===
        self.member_cb = QComboBox()
        members = query_db("SELECT mitglieder_id, vorname || ' ' || nachname AS name FROM mitglieder ORDER BY nachname")
        self.members_map = {}
        for m in members:
            self.member_cb.addItem(m['name'])
            self.members_map[m['name']] = m['mitglieder_id']
        form_layout.addRow("Mitglied:", self.member_cb)

        # === Kategorie-Auswahl (abhängig vom Training) ===
        self.category_cb = QComboBox()
        self.cats_map = {}
        form_layout.addRow("Kategorie:", self.category_cb)

        # === Anschlag ===
        self.anschlag_cb = QComboBox()
        anschlaege = query_db("SELECT anschlag_id, name FROM anschlaege ORDER BY name")
        self.anschlaege_map = {}
        self.anschlag_cb.addItem("")  # optional
        for a in anschlaege:
            self.anschlag_cb.addItem(a['name'])
            self.anschlaege_map[a['name']] = a['anschlag_id']
        form_layout.addRow("Anschlag:", self.anschlag_cb)

        # === Schussanzahl & Punkte ===
        self.shots_spin = QSpinBox()
        self.shots_spin.setMinimum(0)
        form_layout.addRow("Schussanzahl:", self.shots_spin)

        self.points_spin = QDoubleSpinBox()
        self.points_spin.setMinimum(0)
        self.points_spin.setDecimals(1)
        self.points_spin.setSingleStep(0.1)
        form_layout.addRow("Gesamtpunkte:", self.points_spin)

        self.shots_spin.valueChanged.connect(self.update_points_max)
        self.update_points_max()

        layout.addLayout(form_layout)

        # === Buttons ===
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Speichern")
        self.cancel_btn = QPushButton("Abbrechen")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        # 🔁 Kategorie-Liste aktualisieren, wenn Training geändert wird
        self.training_cb.currentIndexChanged.connect(self.update_categories_for_training)

        # Beim Start gleich für erstes Training laden
        if self.training_cb.count() > 0:
            self.update_categories_for_training()

    def update_categories_for_training(self):
        """Lädt nur Kategorien, die beim gewählten Training angeboten wurden."""
        self.category_cb.clear()
        self.cats_map.clear()

        current_training_display = self.training_cb.currentText()
        if not current_training_display:
            return

        training_id = self.trainings_map[current_training_display]

        # 🔍 Nur Kategorien laden, die beim Training verwendet wurden
        sql = """
            SELECT DISTINCT k.kategorie_id, k.name
            FROM training_kategorien tk
            JOIN kategorien k ON k.kategorie_id = tk.kategorie_id
            WHERE tk.training_id = ?
            ORDER BY k.name
        """
        cats = query_db(sql, (training_id,))

        for c in cats:
            self.category_cb.addItem(c['name'])
            self.cats_map[c['name']] = c['kategorie_id']

    def load_data(self, data):
        # Trainingsauswahl setzen
        t_data = query_db("SELECT startzeit, endzeit FROM training WHERE training_id=?", (data['training_id'],), single=True)
        start_dt = QDateTime.fromString(t_data['startzeit'], "yyyy-MM-dd HH:mm:ss")
        end_dt = QDateTime.fromString(t_data['endzeit'], "yyyy-MM-dd HH:mm:ss") if t_data['endzeit'] else None
        t_display = f"{start_dt.toString('dd.MM.yyyy / HH:mm')} – {end_dt.toString('HH:mm') if end_dt else '?'}"
        idx = self.training_cb.findText(t_display)
        if idx >= 0:
            self.training_cb.setCurrentIndex(idx)

        # Mitglied
        m_display = query_db("SELECT vorname || ' ' || nachname AS name FROM mitglieder WHERE mitglieder_id=?", 
                            (data['mitglied_id'],), single=True)['name']
        idx = self.member_cb.findText(m_display)
        if idx >= 0:
            self.member_cb.setCurrentIndex(idx)

        # Kategorie
        cat_name = query_db("SELECT name FROM kategorien WHERE kategorie_id=?", (data['kategorie_id'],), single=True)['name']
        idx = self.category_cb.findText(cat_name)
        if idx >= 0:
            self.category_cb.setCurrentIndex(idx)

        # Anschlag
        if data['anschlag_id']:
            ans_name = query_db("SELECT name FROM anschlaege WHERE anschlag_id=?", (data['anschlag_id'],), single=True)['name']
            idx = self.anschlag_cb.findText(ans_name)
            if idx >= 0:
                self.anschlag_cb.setCurrentIndex(idx)

        self.shots_spin.setValue(data['schussanzahl'] or 0)
        self.update_points_max()
        self.points_spin.setValue(data['gesamtpunktzahl'] or 0)

    def get_data(self):
        training_id = self.trainings_map[self.training_cb.currentText()]
        member_id = self.members_map[self.member_cb.currentText()]
        category_id = self.cats_map[self.category_cb.currentText()]
        ans_text = self.anschlag_cb.currentText()
        anschlag_id = self.anschlaege_map.get(ans_text)
        return {
            'training_id': training_id,
            'mitglied_id': member_id,
            'kategorie_id': category_id,
            'anschlag_id': anschlag_id,
            'schussanzahl': self.shots_spin.value(),
            'gesamtpunktzahl': self.points_spin.value()
        }
    
    def update_points_max(self):
        max_points = self.shots_spin.value() * 10
        self.points_spin.setMaximum(max_points)
