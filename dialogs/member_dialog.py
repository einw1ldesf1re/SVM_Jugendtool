from PyQt6.QtWidgets import QDialog, QFormLayout, QHBoxLayout, QLineEdit, QDateEdit, QPushButton
from PyQt6.QtCore import QDate

class MemberDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle('Mitglied hinzufügen' if data is None else 'Mitglied bearbeiten')
        self.data = data
        self.setup_ui()
        if data:
            self.load_data(data)

    def setup_ui(self):
        layout = QFormLayout(self)
        self.first_edit = QLineEdit()
        self.last_edit = QLineEdit()
        self.birth_edit = QDateEdit(calendarPopup=True)
        self.birth_edit.setDate(QDate.currentDate())
        layout.addRow('Vorname:', self.first_edit)
        layout.addRow('Nachname:', self.last_edit)
        layout.addRow('Geburtsdatum:', self.birth_edit)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton('Speichern')
        self.cancel_btn = QPushButton('Abbrechen')
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addRow(btn_layout)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def load_data(self, data):
        self.first_edit.setText(data['vorname'])
        self.last_edit.setText(data['nachname'])
        self.birth_edit.setDate(QDate.fromString(data['geburtsdatum'], 'yyyy-MM-dd'))

    def get_data(self):
        return {
            'vorname': self.first_edit.text().strip(),
            'nachname': self.last_edit.text().strip(),
            'geburtsdatum': self.birth_edit.date().toString('yyyy-MM-dd')
        }
