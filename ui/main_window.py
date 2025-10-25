from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QTabWidget, QMessageBox, QDialog, QScrollArea, QLabel, QToolButton, QSizePolicy
from PyQt6.QtCore import QDateTime, QDate, Qt, QSize
from PyQt6.QtGui import QIcon, QColor, QBrush
from dialogs.training_dialog import TrainingDialog
from dialogs.member_dialog import MemberDialog
from db import query_db
from datetime import datetime
from functools import partial

from pdf_printer import print_training_results, print_member_list


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Training Manager')
        self.resize(1000, 600)
        self.training_tables = {}  # Für pro-Training Tabellen
        self.current_training_id = None
        self.current_result_row = None
        self.setup_ui()
        self.load_all()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Trainings Tab
        self.trainings_tab = QWidget()
        t_layout = QVBoxLayout(self.trainings_tab)
        btn_row = QHBoxLayout()
        self.add_training_btn = QPushButton('Neues Training')
        self.edit_training_btn = QPushButton('Bearbeiten')
        self.delete_training_btn = QPushButton('Löschen')
        btn_row.addWidget(self.add_training_btn)
        btn_row.addWidget(self.edit_training_btn)
        btn_row.addWidget(self.delete_training_btn)
        btn_row.addStretch()
        t_layout.addLayout(btn_row)
        self.trainings_table = QTableWidget(0, 3)
        self.trainings_table.setHorizontalHeaderLabels(['ID','Startzeit','Endzeit'])
        self.trainings_table.setColumnHidden(0, True)
        self.trainings_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.trainings_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t_layout.addWidget(self.trainings_table)
        self.add_training_btn.clicked.connect(self.add_training)
        self.edit_training_btn.clicked.connect(self.edit_training)
        self.delete_training_btn.clicked.connect(self.delete_training)
        self.tabs.addTab(self.trainings_tab, 'Trainings')

        # Mitglieder Tab
        self.members_tab = QWidget()
        m_layout = QVBoxLayout(self.members_tab)
        m_btn_row = QHBoxLayout()
        self.add_member_btn = QPushButton('Neues Mitglied')
        self.edit_member_btn = QPushButton('Bearbeiten')
        self.delete_member_btn = QPushButton('Löschen')
        self.export_youth_btn = QPushButton("Drucken")
        m_btn_row.addWidget(self.add_member_btn)
        m_btn_row.addWidget(self.edit_member_btn)
        m_btn_row.addWidget(self.delete_member_btn)
        m_btn_row.addWidget(self.export_youth_btn)
        self.export_youth_btn.clicked.connect(self.print_member_list)
        m_btn_row.addStretch()
        m_layout.addLayout(m_btn_row)
        self.member_table = QTableWidget(0, 4)
        self.member_table.setHorizontalHeaderLabels(['ID','Vorname','Nachname','Geburtsdatum'])
        self.member_table.setColumnHidden(0, True)
        self.member_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.member_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        m_layout.addWidget(self.member_table)
        self.add_member_btn.clicked.connect(self.add_member)
        self.edit_member_btn.clicked.connect(self.edit_member)
        self.delete_member_btn.clicked.connect(self.delete_member)
        self.tabs.addTab(self.members_tab, 'Mitglieder')

        self.status = self.statusBar()

    # -------------------- Trainings --------------------
    def load_trainings(self):
        # Haupt-Container leeren
        for i in reversed(range(self.trainings_tab.layout().count())):
            widget = self.trainings_tab.layout().itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # ScrollArea
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: palette(base);
            }
            QScrollArea > QWidget > QWidget {
                background-color: palette(base);
            }
        """)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)

        self.trainings_tab.layout().addWidget(scroll_area)

        # Trainings abrufen
        trainings = query_db('SELECT * FROM training ORDER BY startzeit DESC')

        for t in trainings:
            tid = t['training_id']
            start_dt = QDateTime.fromString(t['startzeit'], 'yyyy-MM-dd HH:mm:ss')
            end_dt = QDateTime.fromString(t['endzeit'], 'yyyy-MM-dd HH:mm:ss') if t['endzeit'] else None
            title_text = f"Training am {start_dt.toString('dd.MM.yyyy / HH:mm')} – {end_dt.toString('HH:mm') if end_dt else '?'} Uhr"

            # Ergebnisse abrufen
            results = query_db('''
                SELECT e.ergebnis_id, m.vorname, m.nachname,
                    k.name AS kategorie, a.name AS anschlag,
                    e.schussanzahl, e.gesamtpunktzahl
                FROM ergebnisse e
                LEFT JOIN mitglieder m ON e.mitglied_id = m.mitglieder_id
                LEFT JOIN kategorien k ON e.kategorie_id = k.kategorie_id
                LEFT JOIN anschlaege a ON e.anschlag_id = a.anschlag_id
                WHERE e.training_id = ?
                ORDER BY k.name, a.name, e.schussanzahl, e.gesamtpunktzahl DESC
            ''', (tid,))

            # Collapsible Container
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(8, 8, 8, 8)
            container.setStyleSheet("""
                QWidget {
                    background-color: palette(mid);
                    border: none;
                    border-radius: 8px;
                }
            """)

            # Header-Widget (Titel + Buttons)
            header_widget = QWidget()
            header_layout = QHBoxLayout(header_widget)
            header_layout.setContentsMargins(4, 4, 4, 4)
            header_widget.setStyleSheet("background-color: palette(mid); border-radius: 6px;")

            # --- Linker Bereich: Titel ---
            title_label = QLabel(title_text)
            title_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    font-size: 14px;
                    padding: 4px;
                }
                QLabel:hover {
                    background-color: palette(light);
                    border-radius: 4px;
                }
            """)
            title_label.setCursor(Qt.CursorShape.PointingHandCursor)
            header_layout.addWidget(title_label)
            header_layout.addStretch()

            # --- Rechter Bereich: Buttons ---
            btn_add = QPushButton()
            btn_add.setIcon(QIcon("assets/icons/plus.png"))
            btn_add.setToolTip("Ergebnis hinzufügen")
            btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_add.setStyleSheet("""
                QPushButton {
                    border: none;
                }
                QPushButton:hover {
                    background-color: palette(light);
                    border-radius: 4px;
                }
            """)
            header_layout.addWidget(btn_add)

            btn_print = QPushButton()
            btn_print.setIcon(QIcon("assets/icons/printer.png"))
            btn_print.setToolTip("Training drucken")
            btn_print.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_print.setStyleSheet("""
                QPushButton {
                    border: none;
                }
                QPushButton:hover {
                    background-color: palette(light);
                    border-radius: 4px;
                }
            """)
            if results:
                header_layout.addWidget(btn_print)

            # Inhalt (eingeklappt)
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(4, 4, 4, 4)

            if results:
                # Ergebnisse gruppieren
                from collections import defaultdict
                gruppen = defaultdict(list)
                for r in results:
                    key = (r['kategorie'], r['schussanzahl'], r['anschlag'] or '')
                    gruppen[key].append(r)

                # Tabellen aufbauen
                for (kategorie, schussanzahl, anschlag), group in gruppen.items():
                    subheader = QLabel(f"{kategorie} / {schussanzahl} Schuss" + (f" / {anschlag}" if anschlag else ""))
                    subheader.setStyleSheet("font-weight: bold; margin-top: 6px; margin-bottom: 3px;")
                    content_layout.addWidget(subheader)

                    table = QTableWidget()
                    table.setColumnCount(3)
                    table.setHorizontalHeaderLabels(["Vorname", "Nachname", "Ergebnis"])
                    header = table.horizontalHeader()
                    header.setStyleSheet("""
                        QHeaderView::section {
                            background-color: palette(dark);
                            font-weight: bold;
                            font-size: 14px;
                            padding-bottom: 2px;
                            padding-top: 2px;
                        }
                    """)
                    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
                    table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
                    table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
                    table.verticalHeader().setVisible(False)

                    table.setRowCount(len(group))
                    for i, r in enumerate(group):
                        table.setItem(i, 0, QTableWidgetItem(r['vorname']))
                        table.setItem(i, 1, QTableWidgetItem(r['nachname']))
                        table.setItem(i, 2, QTableWidgetItem(str(r['gesamtpunktzahl'])))

                    # Dynamische Höhe
                    total_height = table.horizontalHeader().height()
                    for i in range(table.rowCount()):
                        total_height += table.rowHeight(i)
                    table.setFixedHeight(total_height + 2)

                    content_layout.addWidget(table)
            else:
                content_layout.addWidget(QLabel("Noch keine Ergebnisse vorhanden"))

            content_widget.setVisible(False)

            def toggle_content(widget):
                widget.setVisible(not widget.isVisible())

            title_label.mousePressEvent = lambda event, w=content_widget: toggle_content(w)

            # Aufbau Container
            container_layout.addWidget(header_widget)
            container_layout.addWidget(content_widget)
            scroll_layout.addWidget(container)
            scroll_layout.addSpacing(10)



    def add_training(self):
        dlg = TrainingDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            query_db('INSERT INTO training (startzeit, endzeit) VALUES (?, ?)', (data['startzeit'], data['endzeit']))
            tid = query_db('SELECT last_insert_rowid() as id', single=True)['id']
            for cid in set(data['categories']):
                query_db(
                    'INSERT INTO training_kategorien (training_id, kategorie_id) VALUES (?, ?)', 
                    (tid, cid)
                )
            self.load_trainings()
            self.status.showMessage('Training hinzugefügt', 3000)

    def edit_training(self):
        sel = self.trainings_table.currentRow()
        if sel < 0:
            QMessageBox.information(self, 'Auswahl fehlt', 'Bitte wähle ein Training aus.')
            return
        tid = int(self.trainings_table.item(sel,0).text())
        rec = query_db('SELECT * FROM training WHERE training_id=?', (tid,), single=True)
        dlg = TrainingDialog(self, data=rec)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            query_db('UPDATE training SET startzeit=?, endzeit=? WHERE training_id=?', (data['startzeit'], data['endzeit'], tid))
            query_db('DELETE FROM training_kategorien WHERE training_id=?', (tid,))
            for cid in data['categories']:
                query_db('INSERT INTO training_kategorien (training_id, kategorie_id) VALUES (?, ?)', (tid, cid))
            self.load_trainings()
            self.status.showMessage('Training aktualisiert', 3000)

    def delete_training(self):
        sel = self.trainings_table.currentRow()
        if sel < 0:
            QMessageBox.information(self, 'Auswahl fehlt', 'Bitte wähle ein Training aus.')
            return
        tid = int(self.trainings_table.item(sel,0).text())
        ok = QMessageBox.question(self, 'Löschen', 'Willst du dieses Training wirklich löschen?')
        if ok == QMessageBox.StandardButton.Yes:
            query_db('DELETE FROM training WHERE training_id=?', (tid,))
            self.load_trainings()
            self.status.showMessage('Training gelöscht', 3000)

    # -------------------- Mitglieder --------------------
    def load_members(self):
        rows = query_db('SELECT * FROM mitglieder ORDER BY nachname')
        self.member_table.setRowCount(0)
        for r in rows:
            row_pos = self.member_table.rowCount()
            self.member_table.insertRow(row_pos)
            self.member_table.setItem(row_pos, 0, QTableWidgetItem(str(r['mitglieder_id'])))
            self.member_table.setItem(row_pos, 1, QTableWidgetItem(r['vorname']))
            self.member_table.setItem(row_pos, 2, QTableWidgetItem(r['nachname']))

            birthday = QDate.fromString(r['geburtsdatum'], 'yyyy-MM-dd')
            today = QDate.currentDate()
            age = today.year() - birthday.year()
            if (today.month(), today.day()) < (birthday.month(), birthday.day()):
                age -= 1
            display_text = birthday.toString('dd.MM.yyyy')
            item = QTableWidgetItem(display_text)
            if age >= 18:
                item.setText("⚠ " + display_text)
                item.setForeground(QBrush(QColor("red")))
            self.member_table.setItem(row_pos, 3, item)

        self.member_table.setColumnCount(4)
        self.member_table.setHorizontalHeaderLabels(['ID','Vorname','Nachname','Geburtsdatum'])
        self.member_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.member_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.status.showMessage(f'{len(rows)} Mitglieder geladen')

    def add_member(self):
        dlg = MemberDialog(self)
        if dlg.exec() == dlg.DialogCode.Accepted:
            data = dlg.get_data()
            query_db('INSERT INTO mitglieder (vorname, nachname, geburtsdatum) VALUES (?, ?, ?)',
                    (data['vorname'], data['nachname'], data['geburtsdatum']))
            self.load_members()
            self.status.showMessage('Mitglied hinzugefügt', 3000)

    def edit_member(self):
        sel = self.member_table.currentRow()
        if sel < 0:
            QMessageBox.information(self, 'Auswahl fehlt', 'Bitte wähle ein Mitglied aus.')
            return
        pid = int(self.member_table.item(sel,0).text())
        rec = query_db('SELECT * FROM mitglieder WHERE mitglieder_id=?', (pid,), single=True)
        dlg = MemberDialog(self, data=rec)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            query_db('UPDATE mitglieder SET vorname=?, nachname=?, geburtsdatum=? WHERE mitglieder_id=?',
                    (data['vorname'], data['nachname'], data['geburtsdatum'], pid))
            self.load_members()
            self.status.showMessage('Mitglied aktualisiert', 3000)

    def delete_member(self):
        sel = self.member_table.currentRow()
        if sel < 0:
            QMessageBox.information(self, 'Auswahl fehlt', 'Bitte wähle ein Mitglied aus.')
            return
        pid = int(self.member_table.item(sel,0).text())
        ok = QMessageBox.question(self, 'Löschen', 'Willst du dieses Mitglied wirklich löschen?')
        if ok == QMessageBox.StandardButton.Yes:
            query_db('DELETE FROM mitglieder WHERE mitglieder_id=?', (pid,))
            self.load_members()
            self.status.showMessage('Mitglied gelöscht', 3000)

    # -------------------- Drucken --------------------
    def print_selected_training(self):
        row = self.trainings_table.currentRow()
        if row >= 0:
            training_id = self.trainings_table.item(row, 0).text()
            print_training_results(training_id, self)

    def print_member_list(self):
        print_member_list(self)

    def load_all(self):
        self.load_trainings()
        self.load_members()
