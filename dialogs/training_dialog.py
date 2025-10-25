from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel, QCheckBox, QScrollArea, QWidget, QPushButton, QDateTimeEdit
from PyQt6.QtCore import QDate, QDateTime
from db import query_db

class TrainingDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle('Training hinzufügen' if data is None else 'Training bearbeiten')
        self.data = data
        self.categories = query_db('SELECT * FROM kategorien')
        self.setup_ui()
        if data:
            self.load_data(data)

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.start_edit = QDateTimeEdit(calendarPopup=True)
        self.start_edit.setDateTime(QDateTime.currentDateTime())
        self.end_edit = QDateTimeEdit(calendarPopup=True)
        self.end_edit.setDateTime(QDateTime.currentDateTime())
        form_layout.addRow('Startzeit:', self.start_edit)
        form_layout.addRow('Endzeit:', self.end_edit)
        self.layout.addLayout(form_layout)

        self.category_checks = []
        cat_label = QLabel('Kategorien:')
        self.layout.addWidget(cat_label)
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        for cat in self.categories:
            cb = QCheckBox(cat['name'])
            scroll_layout.addWidget(cb)
            self.category_checks.append((cb, cat['kategorie_id']))
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidgetResizable(True)
        scroll.setWidget(scroll_widget)
        self.layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton('Speichern')
        self.cancel_btn = QPushButton('Abbrechen')
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        self.layout.addLayout(btn_layout)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def load_data(self, data):
        # startzeit
        start_dt = QDateTime.fromString(data['startzeit'], 'yyyy-MM-dd HH:mm:ss')
        if start_dt.isValid():
            self.start_edit.setDateTime(start_dt)
        else:
            self.start_edit.setDateTime(QDateTime.currentDateTime())

        # endzeit
        end_dt = QDateTime.fromString(data['endzeit'], 'yyyy-MM-dd HH:mm:ss')
        if end_dt.isValid():
            self.end_edit.setDateTime(end_dt)
        else:
            self.end_edit.setDateTime(QDateTime.currentDateTime())

        # Kategorien laden
        assigned = [tk['kategorie_id'] for tk in query_db(
            'SELECT * FROM training_kategorien WHERE training_id=?', 
            (data['training_id'],)
        )]
        for cb, cid in self.category_checks:
            cb.setChecked(cid in assigned)

    def get_data(self):
        categories_selected = [cid for cb, cid in self.category_checks if cb.isChecked()]
        return {
            'startzeit': self.start_edit.dateTime().toString('yyyy-MM-dd HH:mm:ss'),
            'endzeit': self.end_edit.dateTime().toString('yyyy-MM-dd HH:mm:ss'),
            'categories': categories_selected
        }
