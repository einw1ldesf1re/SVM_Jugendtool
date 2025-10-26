from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QHBoxLayout, QLineEdit, QDateEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import QDate, Qt
from db import query_db


class InlineSuggestLineEdit(QLineEdit):
    """QLineEdit mit Inline-Autocomplete nach dem Cursor."""
    def __init__(self, items=None, parent=None):
        super().__init__(parent)
        self.items = sorted(items) if items else []
        self.suggestion = ""

        # Bei jedem Tippen oder Löschen den Vorschlag updaten
        self.textEdited.connect(self.update_suggestion)

    def keyPressEvent(self, event):
        key = event.key()
        cursor_pos = self.cursorPosition()

        # Vorschlag übernehmen mit Tab oder Pfeil rechts
        if key in (Qt.Key.Key_Tab, Qt.Key.Key_Right) and self.suggestion:
            self.accept_suggestion()
            return

        super().keyPressEvent(event)
        self.update_suggestion()

    def update_suggestion(self):
        cursor_pos = self.cursorPosition()
        text = self.text()
        text_left = text[:cursor_pos]

        # Suche passenden Vorschlag
        suggestion = ""
        for item in self.items:
            if item.lower().startswith(text_left.lower()):
                suggestion = item[len(text_left):]
                break

        # Text nach dem Cursor ersetzen / löschen
        new_text = text_left + suggestion
        self.blockSignals(True)
        self.setText(new_text)
        # Cursor bleibt dort, wo der Benutzer zuletzt getippt hat
        self.setCursorPosition(cursor_pos)
        self.blockSignals(False)

        self.suggestion = suggestion

    def accept_suggestion(self):
        if self.suggestion:
            cursor_pos = self.cursorPosition()
            text_left = self.text()[:cursor_pos]
            new_text = text_left + self.suggestion
            self.setText(new_text)
            self.setCursorPosition(cursor_pos + len(self.suggestion))
            self.suggestion = ""


class MemberDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle('Mitglied hinzufügen' if data is None else 'Mitglied bearbeiten')
        self.data = data
        self.setup_ui()
        self.load_member_names()
        if data:
            self.load_data(data)

    def setup_ui(self):
        layout = QFormLayout(self)

        # === Vorname ===
        self.first_edit = InlineSuggestLineEdit([], self)
        layout.addRow('Vorname:', self.first_edit)

        # === Nachname ===
        self.last_edit = InlineSuggestLineEdit([], self)
        layout.addRow('Nachname:', self.last_edit)

        # === Geburtsdatum ===
        self.birth_edit = QDateEdit(calendarPopup=True)
        self.birth_edit.setDate(QDate.currentDate())
        layout.addRow('Geburtsdatum:', self.birth_edit)

        # === Buttons ===
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton('Speichern')
        self.cancel_btn = QPushButton('Abbrechen')
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addRow(btn_layout)

        self.save_btn.clicked.connect(self.validate_and_accept)
        self.cancel_btn.clicked.connect(self.reject)

    def load_member_names(self):
        """Lädt vorhandene Vornamen und Nachnamen für Vorschläge."""
        members = query_db("SELECT vorname, nachname FROM mitglieder")
        self.first_names = sorted(set(m['vorname'] for m in members))
        self.last_names = sorted(set(m['nachname'] for m in members))

        self.first_edit.items = self.first_names
        self.last_edit.items = self.last_names

    def load_data(self, data):
        self.first_edit.setText(data['vorname'])
        self.last_edit.setText(data['nachname'])
        self.birth_edit.setDate(QDate.fromString(data['geburtsdatum'], 'yyyy-MM-dd'))

    def validate_and_accept(self):
        vorname = self.first_edit.text().strip()
        nachname = self.last_edit.text().strip()

        if not vorname or not nachname:
            QMessageBox.warning(self, "Fehler", "Vorname und Nachname müssen ausgefüllt sein!")
            return

        # Prüfen, ob die Kombination schon existiert
        exists = query_db(
            "SELECT 1 FROM mitglieder WHERE vorname=? AND nachname=?",
            (vorname, nachname),
            single=True
        )
        if exists and not (self.data and self.data['vorname'] == vorname and self.data['nachname'] == nachname):
            QMessageBox.warning(self, "Fehler", "Dieses Mitglied existiert bereits!")
            return

        self.accept()

    def get_data(self):
        return {
            'vorname': self.first_edit.text().strip(),
            'nachname': self.last_edit.text().strip(),
            'geburtsdatum': self.birth_edit.date().toString('yyyy-MM-dd')
        }
