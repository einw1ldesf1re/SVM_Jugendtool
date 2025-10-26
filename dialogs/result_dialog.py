from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QListWidget, QListWidgetItem,
    QComboBox, QSpinBox, QDoubleSpinBox, QHBoxLayout, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, QPoint, QDateTime
from db import query_db

class ResultDialog(QDialog):
    def __init__(self, parent=None, tid=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Ergebnis hinzufügen" if data is None else "Ergebnis bearbeiten")
        self.data = data
        self.tid = tid
        self.selected_member_id = None
        self.setup_ui()
        if self.tid:
            self.update_categories_for_training()
        if data:
            self.load_data(data)
        elif self.tid:
            self.update_categories_for_training()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # === Mitglied-Auswahl mit flüssiger Suche ===
        self.member_edit = QLineEdit()
        form_layout.addRow("Mitglied:", self.member_edit)

        # Vorschlagsliste
        self.popup = QListWidget(self)
        self.popup.hide()
        self.popup.setWindowFlags(Qt.WindowType.ToolTip)
        self.popup.itemClicked.connect(self.on_member_selected)

        # Namen vorbereiten
        members = query_db("SELECT mitglieder_id, vorname || ' ' || nachname AS name FROM mitglieder ORDER BY nachname")
        self.members_map = {m['name']: m['mitglieder_id'] for m in members}
        self.member_names = list(self.members_map.keys())
        self.member_names_lower = [n.lower() for n in self.member_names]

        self.member_edit.textEdited.connect(self.update_member_popup)

        # === Kategorie-Auswahl ===
        self.category_cb = QComboBox()
        self.cats_map = {}
        form_layout.addRow("Kategorie:", self.category_cb)

        # === Anschlag ===
        self.anschlag_cb = QComboBox()
        anschlaege = query_db("SELECT anschlag_id, name FROM anschlaege ORDER BY name")
        self.anschlaege_map = {a['name']: a['anschlag_id'] for a in anschlaege}
        self.anschlag_cb.addItem("")  # optional
        for a in anschlaege:
            self.anschlag_cb.addItem(a['name'])
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

        self.save_btn.clicked.connect(self.validate_and_accept)
        self.cancel_btn.clicked.connect(self.reject)

    # === Mitgliedsauswahl Methoden ===
    def update_member_popup(self, text):
        text = text.strip().lower()
        if not text:
            self.popup.hide()
            return

        tokens = text.split()
        matches = [name for name, name_lower in zip(self.member_names, self.member_names_lower)
                   if all(tok in name_lower for tok in tokens)]
        matches = matches[:20]  # max 20 Vorschläge

        if not matches:
            self.popup.hide()
            return

        self.popup.clear()
        for name in matches:
            QListWidgetItem(name, self.popup)

        pos = self.member_edit.mapToGlobal(QPoint(0, self.member_edit.height()))
        self.popup.move(pos)
        self.popup.resize(self.member_edit.width(), min(200, len(matches) * 24))
        self.popup.show()

    def on_member_selected(self, item):
        self.member_edit.setText(item.text())
        self.selected_member_id = self.members_map[item.text()]
        self.popup.hide()

    # === Kategorien laden ===
    def update_categories_for_training(self):
        self.category_cb.clear()
        self.cats_map.clear()
        if not self.tid:
            return
        sql = """
            SELECT DISTINCT k.kategorie_id, k.name
            FROM training_kategorien tk
            JOIN kategorien k ON k.kategorie_id = tk.kategorie_id
            WHERE tk.training_id = ?
            ORDER BY k.name
        """
        cats = query_db(sql, (self.tid,))
        for c in cats:
            self.category_cb.addItem(c['name'])
            self.cats_map[c['name']] = c['kategorie_id']

    # === Daten laden ===
    def load_data(self, data):
        # Mitglied
        m_display = query_db("SELECT vorname || ' ' || nachname AS name FROM mitglieder WHERE mitglieder_id=?", 
                             (data['mitglied_id'],), single=True)['name']
        self.member_edit.setText(m_display)
        self.selected_member_id = data['mitglied_id']

        # Kategorie
        cat_name = query_db("SELECT name FROM kategorien WHERE kategorie_id=?", 
                            (data['kategorie_id'],), single=True)['name']
        idx = self.category_cb.findText(cat_name)
        if idx >= 0:
            self.category_cb.setCurrentIndex(idx)

        # Anschlag
        if data['anschlag_id']:
            ans_name = query_db("SELECT name FROM anschlaege WHERE anschlag_id=?", 
                                (data['anschlag_id'],), single=True)['name']
            idx = self.anschlag_cb.findText(ans_name)
            if idx >= 0:
                self.anschlag_cb.setCurrentIndex(idx)

        self.shots_spin.setValue(data['schussanzahl'] or 0)
        self.update_points_max()
        self.points_spin.setValue(data['gesamtpunktzahl'] or 0)

    # === Punkte berechnen ===
    def update_points_max(self):
        self.points_spin.setMaximum(self.shots_spin.value() * 10)

    # === Validierung & Daten holen ===
    def validate_and_accept(self):
        text = self.member_edit.text().strip()
        member_id = self.members_map.get(text)
        if not member_id:
            QMessageBox.warning(self, "Fehler", "Bitte ein gültiges Mitglied auswählen!")
            return
        self.selected_member_id = member_id
        if not self.category_cb.currentText():
            QMessageBox.warning(self, "Fehler", "Bitte eine Kategorie auswählen!")
            return
        self.accept()

    def get_data(self):
        return {
            'training_id': self.tid,
            'mitglied_id': self.selected_member_id,
            'kategorie_id': self.cats_map[self.category_cb.currentText()],
            'anschlag_id': self.anschlaege_map.get(self.anschlag_cb.currentText()),
            'schussanzahl': self.shots_spin.value(),
            'gesamtpunktzahl': self.points_spin.value()
        }
