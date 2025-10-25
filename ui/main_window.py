from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QTabWidget, QMessageBox, QDialog, QScrollArea, QLabel
from PyQt6.QtCore import QDateTime, QDate, Qt
from PyQt6.QtGui import QIcon, QColor, QBrush
from dialogs.training_dialog import TrainingDialog
from dialogs.member_dialog import MemberDialog
import random

from db import query_db
from datetime import datetime

from pdf_export import export_youth_list, export_training_results, export_member_stats
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
        self.print_training_btn = QPushButton("Drucken")
        btn_row.addWidget(self.add_training_btn)
        btn_row.addWidget(self.edit_training_btn)
        btn_row.addWidget(self.delete_training_btn)
        self.print_training_btn.clicked.connect(self.print_selected_training)
        btn_row.addWidget(self.print_training_btn)
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

        # Ergebnis Tab
        self.results_tab = QWidget()
        r_layout = QVBoxLayout(self.results_tab)
        btn_row = QHBoxLayout()
        self.add_result_btn = QPushButton("Neues Ergebnis")
        self.edit_result_btn = QPushButton("Bearbeiten")
        self.delete_result_btn = QPushButton("Löschen")
        btn_row.addWidget(self.add_result_btn)
        btn_row.addWidget(self.edit_result_btn)
        btn_row.addWidget(self.delete_result_btn)
        btn_row.addStretch()
        r_layout.addLayout(btn_row)
        self.tabs.addTab(self.results_tab, "Ergebnisse")
        self.add_result_btn.clicked.connect(self.add_result)
        self.edit_result_btn.clicked.connect(self.edit_result)
        self.delete_result_btn.clicked.connect(self.delete_result)

    # -------------------- Trainings --------------------
    def load_trainings(self):
        rows = query_db('SELECT * FROM training ORDER BY startzeit')
        self.trainings_table.setRowCount(0)
        for r in rows:
            row_pos = self.trainings_table.rowCount()
            self.trainings_table.insertRow(row_pos)
            self.trainings_table.setItem(row_pos, 0, QTableWidgetItem(str(r['training_id'])))
            
            start_dt = QDateTime.fromString(r['startzeit'], 'yyyy-MM-dd HH:mm:ss')
            self.trainings_table.setItem(row_pos, 1, QTableWidgetItem(start_dt.toString('dd.MM.yyyy / HH:mm') + " Uhr"))
            
            if r['endzeit']:
                end_dt = QDateTime.fromString(r['endzeit'], 'yyyy-MM-dd HH:mm:ss')
                self.trainings_table.setItem(row_pos, 2, QTableWidgetItem(end_dt.toString('dd.MM.yyyy / HH:mm') + " Uhr"))
            else:
                self.trainings_table.setItem(row_pos, 2, QTableWidgetItem(''))
        
        self.status.showMessage(f'{len(rows)} Trainings geladen')

    def add_training(self):
        dlg = TrainingDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            query_db('INSERT INTO training (startzeit, endzeit) VALUES (?, ?)', (data['startzeit'], data['endzeit']))
            tid = query_db('SELECT last_insert_rowid() as id', single=True)['id']
            for cid in data['categories']:
                query_db('INSERT INTO training_kategorien (training_id, kategorie_id) VALUES (?, ?)', (tid, cid))
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

    # -------------------- Ergebnisse --------------------
    def load_results(self):
        # Clear existing layout
        for i in reversed(range(self.results_tab.layout().count())):
            widget = self.results_tab.layout().itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)
        self.results_tab.layout().addWidget(scroll_area)

        trainings = query_db('SELECT training_id, startzeit, endzeit FROM training ORDER BY startzeit DESC')

        self.training_tables.clear()
        self.current_result_row = None
        self.current_table = None

        for t in trainings:
            tid = t['training_id']

            # Trainingscontainer für visuellen Abstand
            training_frame = QWidget()
            training_layout = QVBoxLayout(training_frame)
            # training_frame.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 5px;")
            training_layout.setContentsMargins(5, 5, 5, 5)
            scroll_layout.addWidget(training_frame)
            scroll_layout.addSpacing(10)

            start_dt = QDateTime.fromString(t['startzeit'], 'yyyy-MM-dd HH:mm:ss')
            end_dt = QDateTime.fromString(t['endzeit'], 'yyyy-MM-dd HH:mm:ss') if t['endzeit'] else None
            title_text = f"Training am {start_dt.toString('dd.MM.yyyy / HH:mm')} – {end_dt.toString('HH:mm') if end_dt else '?'} Uhr"

            title_layout = QHBoxLayout()
            title_label = QLabel(title_text)
            title_label.setStyleSheet("font-weight: bold; font-size: 14pt;")
            title_layout.addWidget(title_label)
            title_layout.addStretch()
            training_layout.addLayout(title_layout)

            results = query_db('''
                SELECT e.ergebnis_id as id, m.vorname, m.nachname,
                    k.name AS kategorie, a.name AS anschlag,
                    e.schussanzahl, e.gesamtpunktzahl
                FROM ergebnisse e
                LEFT JOIN mitglieder m ON e.mitglied_id = m.mitglieder_id
                LEFT JOIN kategorien k ON e.kategorie_id = k.kategorie_id
                LEFT JOIN anschlaege a ON e.anschlag_id = a.anschlag_id
                WHERE e.training_id=?
                ORDER BY k.name, a.name, e.schussanzahl, e.gesamtpunktzahl DESC
            ''', (tid,))

            from collections import defaultdict
            gruppen = defaultdict(list)
            for r in results:
                key = (r['kategorie'], r['schussanzahl'], r['anschlag'] or '')
                gruppen[key].append(r)

            for (kategorie, schussanzahl, anschlag), group_results in gruppen.items():
                subheader = QLabel(f"{kategorie} / {schussanzahl} Schuss" + (f" / {anschlag}" if anschlag else ""))
                subheader.setStyleSheet("font-weight: bold; margin-top: 10px;")
                training_layout.addWidget(subheader)

                table = QTableWidget()
                table.setColumnCount(4)
                table.setHorizontalHeaderLabels(['ID', 'Vorname', 'Nachname', 'Ergebnis'])
                table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
                table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
                table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

                table.setRowCount(len(group_results))
                for row_idx, r in enumerate(group_results):
                    table.setItem(row_idx, 0, QTableWidgetItem(str(r['id'])))
                    table.setItem(row_idx, 1, QTableWidgetItem(r['vorname']))
                    table.setItem(row_idx, 2, QTableWidgetItem(r['nachname']))
                    table.setItem(row_idx, 3, QTableWidgetItem(str(r['gesamtpunktzahl'] or '')))

                table.setColumnHidden(0, True)  # ID-Spalte verstecken

                # Automatische Höhe
                table_height = table.horizontalHeader().height()
                for row in range(table.rowCount()):
                    table_height += table.rowHeight(row)
                table.setFixedHeight(table_height + 2)

                table.cellClicked.connect(lambda row, col, t=table: self.select_result_row(t, row))

                training_layout.addWidget(table)
                # Speicherung nach Tabellenobjekt, nicht nach ID
                self.training_tables[table] = True

    def select_result_row(self, table, row):
        self.current_table = table
        self.current_result_row = row

    def edit_result(self):
        if self.current_table is None or self.current_result_row is None:
            QMessageBox.information(self, "Auswahl fehlt", "Bitte wähle ein Ergebnis aus.")
            return
        eid_item = self.current_table.item(self.current_result_row, 0)
        eid = int(eid_item.text())
        from dialogs.result_dialog import ResultDialog
        rec = query_db('SELECT * FROM ergebnisse WHERE ergebnis_id=?', (eid,), single=True)
        dlg = ResultDialog(self, data=rec)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            query_db('''
                UPDATE ergebnisse
                SET training_id=?, mitglied_id=?, kategorie_id=?, anschlag_id=?, schussanzahl=?, gesamtpunktzahl=?
                WHERE ergebnis_id=?
            ''', (data['training_id'], data['mitglied_id'], data['kategorie_id'],
                data['anschlag_id'], data['schussanzahl'], data['gesamtpunktzahl'], eid))
            self.load_results()
            self.status.showMessage("Ergebnis aktualisiert", 3000)

    def delete_result(self):
        if self.current_table is None or self.current_result_row is None:
            QMessageBox.information(self, "Auswahl fehlt", "Bitte wähle ein Ergebnis aus.")
            return
        eid_item = self.current_table.item(self.current_result_row, 0)
        eid = int(eid_item.text())
        ok = QMessageBox.question(self, "Löschen", "Willst du dieses Ergebnis wirklich löschen?")
        if ok == QMessageBox.StandardButton.Yes:
            query_db('DELETE FROM ergebnisse WHERE ergebnis_id=?', (eid,))
            self.load_results()
            self.status.showMessage("Ergebnis gelöscht", 3000)



    def add_result(self):
        from dialogs.result_dialog import ResultDialog
        dlg = ResultDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            query_db('''
                INSERT INTO ergebnisse (training_id, mitglied_id, kategorie_id, anschlag_id, schussanzahl, gesamtpunktzahl)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (data['training_id'], data['mitglied_id'], data['kategorie_id'], data['anschlag_id'], data['schussanzahl'], data['gesamtpunktzahl']))
            self.load_results()
            self.status.showMessage("Ergebnis hinzugefügt", 3000)

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
        self.load_results()
