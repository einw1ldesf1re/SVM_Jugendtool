from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QTabWidget, QMessageBox, QDialog, QScrollArea, QLabel, QToolButton, QSizePolicy
from PyQt6.QtCore import QDateTime, QDate, Qt, QSize
from PyQt6.QtGui import QIcon, QColor, QBrush
from dialogs.training_dialog import TrainingDialog
from dialogs.member_dialog import MemberDialog
from dialogs.result_dialog import ResultDialog
from db import query_db
from datetime import datetime
from functools import partial

from pdf_printer import print_training_results, print_member_list, print_member_statistics


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
        self.add_training_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_training_btn.setStyleSheet("""
                    QPushButton {
                        padding: 3px 6px;
                    }
                    QPushButton:hover {
                        background-color: palette(light);
                        border-radius: 4px;
                    }
                """)
        btn_row.addWidget(self.add_training_btn)
        btn_row.addStretch()
        t_layout.addLayout(btn_row)
        self.trainings_table = QTableWidget(0, 3)
        self.trainings_table.setHorizontalHeaderLabels(['ID','Startzeit','Endzeit'])
        self.trainings_table.setColumnHidden(0, True)
        self.trainings_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.trainings_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t_layout.addWidget(self.trainings_table)
        self.add_training_btn.clicked.connect(self.add_training)
        self.tabs.addTab(self.trainings_tab, 'Trainings')

        # Mitglieder Tab
        self.members_tab = QWidget()
        m_layout = QVBoxLayout(self.members_tab)
        m_btn_row = QHBoxLayout()
        self.add_member_btn = QPushButton('Neues Mitglied')
        self.add_member_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_member_btn.setStyleSheet("""
                    QPushButton {
                        padding: 3px 6px;
                    }
                    QPushButton:hover {
                        background-color: palette(light);
                        border-radius: 4px;
                    }
                """)
        self.export_youth_btn = QPushButton("Drucken")
        self.export_youth_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_youth_btn.setStyleSheet("""
                    QPushButton {
                        padding: 3px 6px;
                    }
                    QPushButton:hover {
                        background-color: palette(light);
                        border-radius: 4px;
                    }
                """)
        m_btn_row.addWidget(self.add_member_btn)
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
        self.tabs.addTab(self.members_tab, 'Mitglieder')
        self.status = self.statusBar()

    # -------------------- Trainings --------------------
    def load_trainings(self):
        # --- Haupt-Container leeren ---
        for i in reversed(range(self.trainings_tab.layout().count())):
            widget = self.trainings_tab.layout().itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # --- ScrollArea ---
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

        # --- Trainings laden ---
        trainings = query_db('SELECT * FROM training ORDER BY startzeit DESC')

        for t in trainings:
            tid = t['training_id']
            start_dt = QDateTime.fromString(t['startzeit'], 'yyyy-MM-dd HH:mm:ss')
            end_dt = QDateTime.fromString(t['endzeit'], 'yyyy-MM-dd HH:mm:ss') if t['endzeit'] else None
            title_text = f"Training am {start_dt.toString('dd.MM.yyyy / HH:mm')} – {end_dt.toString('HH:mm') if end_dt else '?'} Uhr"

            # --- Ergebnisse abrufen ---
            results = query_db('''
                SELECT e.ergebnis_id, m.vorname, m.nachname, m.rolle,
                    k.name AS kategorie, a.name AS anschlag,
                    e.schussanzahl, e.gesamtpunktzahl
                FROM ergebnisse e
                LEFT JOIN mitglieder m ON e.mitglied_id = m.mitglieder_id
                LEFT JOIN kategorien k ON e.kategorie_id = k.kategorie_id
                LEFT JOIN anschlaege a ON e.anschlag_id = a.anschlag_id
                WHERE e.training_id = ?
                ORDER BY k.name, a.name, e.schussanzahl, e.gesamtpunktzahl DESC
            ''', (tid,))

            # --- Container ---
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(8, 8, 8, 8)
            container.setStyleSheet("""
                QWidget {
                    background-color: palette(mid);
                    border-radius: 8px;
                }
            """)

            # === Header ===
            header_widget = QWidget()
            header_layout = QHBoxLayout(header_widget)
            header_layout.setContentsMargins(4, 4, 4, 4)
            header_widget.setStyleSheet("background-color: palette(mid); border-radius: 6px;")

            # Titel
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

            # Buttons
            def make_btn(icon, tooltip, slot):
                btn = QPushButton()
                btn.setIcon(QIcon(icon))
                btn.setToolTip(tooltip)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setFixedSize(24, 24)
                btn.setStyleSheet("""
                    QPushButton {
                        border: none;
                        padding-top: 2px;
                        padding-bottom: 2px;
                    }
                    QPushButton:hover {
                        background-color: palette(light);
                        border-radius: 4px;
                    }
                """)
                btn.clicked.connect(slot)
                return btn

            btn_add = make_btn("assets/icons/plus.png", "Ergebnis hinzufügen", lambda checked, tid=tid: self.add_results_by_id(tid))
            btn_edit = make_btn("assets/icons/edit.png", "Training bearbeiten", lambda checked, tid=tid: self.edit_training_by_id(tid))
            btn_delete = make_btn("assets/icons/trash.png", "Training löschen", lambda checked, tid=tid: self.delete_training_by_id(tid))
            header_layout.addWidget(btn_add)
            header_layout.addWidget(btn_edit)
            header_layout.addWidget(btn_delete)

            if results:
                btn_print = make_btn("assets/icons/printer.png", "Training drucken", lambda checked, tid=tid: self.print_training_by_id(tid))
                header_layout.addWidget(btn_print)

            # === Inhalt (eingeklappt) ===
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(4, 4, 4, 4)

            if results:
                from collections import defaultdict
                gruppen = defaultdict(list)
                for r in results:
                    key = (r['kategorie'], r['schussanzahl'], r['anschlag'] or '')
                    gruppen[key].append(r)

                for (kategorie, schussanzahl, anschlag), group in gruppen.items():
                    subheader = QLabel(f"{kategorie} / {schussanzahl} Schuss" + (f" / {anschlag}" if anschlag else ""))
                    subheader.setStyleSheet("""
                        font-weight: bold;
                        margin: 0;
                        margin-top: 10px;
                        margin-bottom: 2px;
                        padding: 2px 0;
                    """)
                    content_layout.addWidget(subheader)

                    table = QTableWidget()
                    table.setColumnCount(4)
                    table.setHorizontalHeaderLabels(["Vorname", "Nachname", "Ergebnis", ""])

                    header = table.horizontalHeader()
                    header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Vorname
                    header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Nachname
                    header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Ergebnis
                    header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Buttons fixieren
                    table.setColumnWidth(3, 48)  # feste Breite für Buttons-Spalte

                    table.setStyleSheet("""
                        QTableView::item {
                            padding-left: 6px;
                            padding-right: 6px;
                        }
                    """)

                    header.setStyleSheet("""
                        QHeaderView::section {
                            background-color: palette(dark);
                            font-weight: bold;
                            font-size: 13px;
                            padding: 2px 0;
                        }
                    """)

                    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
                    table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
                    table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
                    table.verticalHeader().setVisible(False)

                    table.setRowCount(len(group))
                    for i, r in enumerate(group):
                        item_vor = QTableWidgetItem(r['vorname'])
                        item_nach = QTableWidgetItem(r['nachname'])

                        # Gäste leicht grau + kursiv anzeigen
                        if r['rolle'] and r['rolle'].lower() == 'gast':
                            guest_brush = QBrush(QColor("#888888"))
                            for item in (item_vor, item_nach):
                                item.setForeground(guest_brush)
                                f = item.font()
                                f.setItalic(True)
                                item.setFont(f)

                        table.setItem(i, 0, item_vor)
                        table.setItem(i, 1, item_nach)
                        table.setItem(i, 2, QTableWidgetItem(str(r['gesamtpunktzahl'])))

                        # --- Button-Cell ---
                        btn_widget = QWidget()
                        btn_layout = QHBoxLayout(btn_widget)
                        btn_layout.setContentsMargins(0, 0, 0, 0)
                        btn_layout.setSpacing(2)

                        btn_edit = make_btn("assets/icons/edit.png", "Ergebnis bearbeiten",
                                            lambda checked, eid=r['ergebnis_id']: self.edit_result_by_id(eid))
                        btn_delete = make_btn("assets/icons/trash.png", "Ergebnis löschen",
                                            lambda checked, eid=r['ergebnis_id']: self.delete_result_by_id(eid))
                        btn_layout.addWidget(btn_edit)
                        btn_layout.addWidget(btn_delete)
                        btn_layout.addStretch()

                        table.setCellWidget(i, 3, btn_widget)

                    # Höhe der Tabelle anpassen
                    table_height = table.horizontalHeader().height()
                    for row in range(table.rowCount()):
                        table_height += table.rowHeight(row)
                    table.setFixedHeight(table_height)
                    table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

                    # --- Nachträgliche Breitenkorrektur ---
                    extra_padding = 12
                    for col in (2, 3):  # Ergebnis & Button-Spalte
                        table.resizeColumnToContents(col)
                        w = header.sectionSize(col)
                        header.resizeSection(col, w + extra_padding)

                    content_layout.addWidget(table)
            else:
                lbl_empty = QLabel("Noch keine Ergebnisse vorhanden")
                lbl_empty.setContentsMargins(0, 0, 0, 0)
                content_layout.addWidget(lbl_empty)

            content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            content_widget.adjustSize()
            content_widget.setVisible(False)

            def toggle_content(widget):
                widget.setVisible(not widget.isVisible())

            title_label.mousePressEvent = lambda event, w=content_widget: toggle_content(w)

            container_layout.addWidget(header_widget)
            container_layout.addWidget(content_widget)
            scroll_layout.addWidget(container)
            scroll_layout.addSpacing(10)

    def add_results_by_id(self, tid):
        # tid wird hier direkt übergeben
        dlg = ResultDialog(self, tid=tid)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()

            # Prüfen, ob das Ergebnis schon existiert
            exists = query_db('''
                SELECT 1 FROM ergebnisse
                WHERE training_id=? AND mitglied_id=? AND kategorie_id=? 
                AND anschlag_id IS ? AND schussanzahl=?
            ''', (
                data['training_id'], data['mitglied_id'], data['kategorie_id'],
                data['anschlag_id'], data['schussanzahl']
            ), single=True)

            if exists:
                QMessageBox.warning(
                    self, 
                    "Fehler", 
                    "Für dieses Mitglied existiert bereits ein Ergebnis mit diesen Angaben!"
                )
                return

            # Ergebnis einfügen
            query_db('''
                INSERT INTO ergebnisse (training_id, mitglied_id, kategorie_id, anschlag_id, schussanzahl, gesamtpunktzahl)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                data['training_id'], data['mitglied_id'], data['kategorie_id'], 
                data['anschlag_id'], data['schussanzahl'], data['gesamtpunktzahl']
            ))

            gast_check = query_db('''
                SELECT vorname, nachname, rolle FROM mitglieder WHERE mitglieder_id=?
            ''', (data['mitglied_id'],), single=True)

            if gast_check and gast_check.get('rolle', '').lower() == 'gast':
                # Anzahl der bisherigen Ergebnisse für diesen Gast zählen
                result_count = query_db('''
                    SELECT COUNT(*) AS count FROM ergebnisse
                    WHERE mitglied_id=?
                ''', (data['mitglied_id'],), single=True)['count']

                if result_count >= 3:
                    vorname = gast_check['vorname']
                    nachname = gast_check['nachname']
                    QMessageBox.information(
                        self,
                        "Gast-Ergebnisse",
                        f"{vorname} {nachname} ist noch nicht im Verein und hat bereits {result_count} Ergebnisse eingetragen!"
                    )
                    
            self.load_trainings()
            self.status.showMessage("Ergebnis hinzugefügt", 3000)

    def add_training(self):

        dlg = TrainingDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()

            # Sekunden auf 00 setzen
            from datetime import datetime
            start_dt = datetime.strptime(data['startzeit'], "%Y-%m-%d %H:%M:%S")
            start_dt = start_dt.replace(second=0)
            end_dt = None
            if data['endzeit']:
                end_dt = datetime.strptime(data['endzeit'], "%Y-%m-%d %H:%M:%S")
                end_dt = end_dt.replace(second=0)

            # Prüfen, ob zu dieser Startzeit schon ein Training existiert
            exists = query_db(
                'SELECT 1 FROM training WHERE startzeit = ?',
                (start_dt.strftime("%Y-%m-%d %H:%M:%S"),),
                single=True
            )
            if exists:
                QMessageBox.warning(
                    self,
                    'Fehler',
                    'Zu dieser Startzeit existiert bereits ein Training!'
                )
                return

            # Training einfügen
            tid = query_db(
                'INSERT INTO training (startzeit, endzeit) VALUES (?, ?)',
                (start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                end_dt.strftime("%Y-%m-%d %H:%M:%S") if end_dt else None),
                commit=True,
                return_id=True
            )

            # Kategorien einfügen (ohne Duplikate)
            for cid in set(data['categories']):
                query_db(
                    'INSERT INTO training_kategorien (training_id, kategorie_id) VALUES (?, ?)',
                    (tid, cid),
                    commit=True
                )

            self.load_trainings()
            self.status.showMessage('Training hinzugefügt', 3000)

    def edit_result_by_id(self, eid):
        """Ergebnis bearbeiten."""
        # Ergebnis-Daten abrufen
        data = query_db('SELECT * FROM ergebnisse WHERE ergebnis_id=?', (eid,), single=True)
        if not data:
            QMessageBox.warning(self, "Fehler", "Das Ergebnis existiert nicht mehr.")
            self.load_trainings()
            return

        tid = data['training_id']  # Training-ID aus dem Ergebnis

        # Dialog zum Bearbeiten öffnen und tid übergeben
        dlg = ResultDialog(self, tid=tid, data=data)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_data = dlg.get_data()

            # Prüfen, ob identisches Ergebnis bereits existiert
            exists = query_db('''
                SELECT 1 FROM ergebnisse
                WHERE training_id=? AND mitglied_id=? AND kategorie_id=? 
                AND anschlag_id IS ? AND schussanzahl=? AND ergebnis_id != ?
            ''', (
                new_data['training_id'], new_data['mitglied_id'], new_data['kategorie_id'],
                new_data['anschlag_id'], new_data['schussanzahl'], eid
            ), single=True)

            if exists:
                QMessageBox.warning(self, "Fehler", "Für dieses Mitglied existiert bereits ein Ergebnis mit diesen Angaben!")
                return

            # Ergebnis aktualisieren
            query_db('''
                UPDATE ergebnisse
                SET mitglied_id=?, kategorie_id=?, anschlag_id=?, schussanzahl=?, gesamtpunktzahl=?
                WHERE ergebnis_id=?
            ''', (
                new_data['mitglied_id'], new_data['kategorie_id'], new_data['anschlag_id'],
                new_data['schussanzahl'], new_data['gesamtpunktzahl'], eid
            ))

            self.load_trainings()
            self.status.showMessage("Ergebnis aktualisiert", 3000)

    def delete_result_by_id(self, eid):
        """Ergebnis löschen."""
        confirm = QMessageBox.question(
            self,
            "Ergebnis löschen",
            "Willst du dieses Ergebnis wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            query_db('DELETE FROM ergebnisse WHERE ergebnis_id=?', (eid,))
            self.load_trainings()
            self.status.showMessage("Ergebnis gelöscht", 3000)

    def delete_training_by_id(self, tid):
        ok = QMessageBox.question(
            self, 
            'Löschen', 
            'Willst du dieses Training wirklich löschen?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ok != QMessageBox.StandardButton.Yes:
            return

        query_db('DELETE FROM ergebnisse WHERE training_id=?', (tid,))

        query_db('DELETE FROM training_kategorien WHERE training_id=?', (tid,))

        query_db('DELETE FROM training WHERE training_id=?', (tid,))

        # Trainingsliste neu laden
        self.load_trainings()
        self.status.showMessage('Training und alle zugehörigen Daten gelöscht', 3000)

    def print_training_by_id(self, tid):
            print_training_results(tid, self)
    
    def edit_training_by_id(self, tid):
        # Aktuelle Daten abrufen
        rec = query_db('SELECT * FROM training WHERE training_id=?', (tid,), single=True)
        dlg = TrainingDialog(self, data=rec)
        
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()

            # 1️⃣ Start- und Endzeit auf volle Minuten setzen (Sekunden = 00)
            start_dt = datetime.strptime(data['startzeit'], '%Y-%m-%d %H:%M:%S').replace(second=0)
            end_dt = None
            if data['endzeit']:
                end_dt = datetime.strptime(data['endzeit'], '%Y-%m-%d %H:%M:%S').replace(second=0)

            start_str = start_dt.strftime('%Y-%m-%d %H:%M:%S')
            end_str = end_dt.strftime('%Y-%m-%d %H:%M:%S') if end_dt else None

            # 2️⃣ Prüfen auf doppelte Startzeit (außer beim aktuellen Training)
            duplicate = query_db(
                'SELECT training_id FROM training WHERE startzeit=? AND training_id<>?',
                (start_str, tid),
                single=True
            )
            if duplicate:
                QMessageBox.warning(self, 'Fehler', 'Für diese Startzeit existiert bereits ein Training!')
                return

            # 3️⃣ Update in Datenbank
            query_db('UPDATE training SET startzeit=?, endzeit=? WHERE training_id=?', (start_str, end_str, tid))

            # 4️⃣ Kategorien aktualisieren
            query_db('DELETE FROM training_kategorien WHERE training_id=?', (tid,))
            for cid in set(data['categories']):
                query_db('INSERT INTO training_kategorien (training_id, kategorie_id) VALUES (?, ?)', (tid, cid))

            # 5️⃣ UI aktualisieren
            self.load_trainings()
            self.status.showMessage('Training aktualisiert', 3000)

    # -------------------- Mitglieder --------------------
    def load_members(self):
        rows = query_db('SELECT * FROM mitglieder ORDER BY nachname')
        self.member_table.setRowCount(0)
        self.member_table.setColumnCount(6)

        # --- Tabellenkopf ---
        self.member_table.setHorizontalHeaderLabels(['ID', 'Vorname', 'Nachname', 'Geburtsdatum', 'Status', ''])
        header = self.member_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.member_table.setColumnWidth(5, 72)

        # Padding per Stylesheet (gilt für alle Zellen)
        self.member_table.setStyleSheet("""
            QTableView::item {
                padding-left: 6px;
                padding-right: 6px;
            }
        """)

        self.member_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.member_table.verticalHeader().setVisible(False)
        self.member_table.setIconSize(QSize(16, 16))

        for r in rows:
            row_pos = self.member_table.rowCount()
            self.member_table.insertRow(row_pos)

            # --- Prüfen, ob Gast ---
            is_guest = r.get('rolle', '').lower() == 'gast'

            # --- Spalten befüllen ---
            id_item = QTableWidgetItem(str(r['mitglieder_id']))
            vor_item = QTableWidgetItem(r['vorname'])
            nach_item = QTableWidgetItem(r['nachname'])

            for item in (id_item, vor_item, nach_item):
                if is_guest:
                    font = item.font()
                    font.setItalic(True)
                    item.setFont(font)
                    item.setForeground(QBrush(QColor("#888888")))  # hellgrau
            self.member_table.setItem(row_pos, 0, id_item)
            self.member_table.setItem(row_pos, 1, vor_item)
            self.member_table.setItem(row_pos, 2, nach_item)

            # --- Geburtstag + Alter ---
            birthday = QDate.fromString(r['geburtsdatum'], 'yyyy-MM-dd')
            today = QDate.currentDate()
            if birthday.isValid():
                age = today.year() - birthday.year()
                if (today.month(), today.day()) < (birthday.month(), birthday.day()):
                    age -= 1
                display_text = birthday.toString('dd.MM.yyyy')
                bday_item = QTableWidgetItem(display_text)
                if age >= 18:
                    bday_item.setText(f"⚠ {display_text}")
                    bday_item.setForeground(QBrush(QColor("red")))
            else:
                bday_item = QTableWidgetItem("–")

            if is_guest:
                font = bday_item.font()
                font.setItalic(True)
                bday_item.setFont(font)
                bday_item.setForeground(QBrush(QColor("#888888")))
            self.member_table.setItem(row_pos, 3, bday_item)

            # --- Rolle / Status ---
            role_text = r.get('rolle', 'Mitglied')
            role_item = QTableWidgetItem(role_text)
            if is_guest:
                font = role_item.font()
                font.setItalic(True)
                role_item.setFont(font)
                role_item.setForeground(QBrush(QColor("#888888")))
            self.member_table.setItem(row_pos, 4, role_item)

            # --- Buttons ---
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(4)

            btn_stats = QPushButton()
            btn_stats.setIcon(QIcon("assets/icons/diagram.png"))
            btn_stats.setToolTip("Mitglied statistiken")
            btn_stats.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_stats.setFixedSize(24, 24)
            btn_stats.setStyleSheet("""
                    QPushButton {
                        border: none;
                        padding-top: 2px;
                        padding-bottom: 2px;
                    }
                    QPushButton:hover {
                        background-color: palette(light);
                        border-radius: 4px;
                    }
                """)
            btn_stats.clicked.connect(lambda checked, mid=r['mitglieder_id']: self.print_member_stats_by_id(mid))
            btn_layout.addWidget(btn_stats, alignment=Qt.AlignmentFlag.AlignCenter)

            btn_edit = QPushButton()
            btn_edit.setIcon(QIcon("assets/icons/edit.png"))
            btn_edit.setToolTip("Mitglied bearbeiten")
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.setFixedSize(24, 24)
            btn_edit.setStyleSheet("""
                    QPushButton {
                        border: none;
                        padding-top: 2px;
                        padding-bottom: 2px;
                    }
                    QPushButton:hover {
                        background-color: palette(light);
                        border-radius: 4px;
                    }
                """)
            btn_edit.clicked.connect(lambda checked, mid=r['mitglieder_id']: self.edit_member_by_id(mid))
            btn_layout.addWidget(btn_edit, alignment=Qt.AlignmentFlag.AlignCenter)

            btn_delete = QPushButton()
            btn_delete.setIcon(QIcon("assets/icons/trash.png"))
            btn_delete.setToolTip("Mitglied löschen")
            btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_delete.setFixedSize(24, 24)
            btn_delete.setStyleSheet("""
                    QPushButton {
                        border: none;
                        padding-top: 2px;
                        padding-bottom: 2px;
                    }
                    QPushButton:hover {
                        background-color: palette(light);
                        border-radius: 4px;
                    }
                """)
            btn_delete.clicked.connect(lambda checked, mid=r['mitglieder_id']: self.delete_member_by_id(mid))
            btn_layout.addWidget(btn_delete, alignment=Qt.AlignmentFlag.AlignCenter)

            btn_widget.setLayout(btn_layout)
            self.member_table.setCellWidget(row_pos, 5, btn_widget)
            self.member_table.setRowHeight(row_pos, 28)

        # --- Nach dem Befüllen: resizeToContents + padding-Kompensation ---
        extra_padding = 12  # passt zu deinem stylesheet padding-left+right
        for col in (0, 4, 5):
            self.member_table.resizeColumnToContents(col)
            w = header.sectionSize(col)
            header.resizeSection(col, w + extra_padding)

        self.status.showMessage(f"{len(rows)} Mitglieder geladen", 3000)

    def add_member(self):
        """Fügt ein neues Mitglied hinzu."""
        dlg = MemberDialog(self)
        if dlg.exec() == dlg.DialogCode.Accepted:
            data = dlg.get_data()
            query_db(
                'INSERT INTO mitglieder (vorname, nachname, geburtsdatum, rolle) VALUES (?, ?, ?, ?)',
                (data['vorname'], data['nachname'], data['geburtsdatum'], data['rolle'])
            )
            self.load_members()
            self.status.showMessage("Mitglied hinzugefügt", 3000)

    def edit_member_by_id(self, mid):
        """Bearbeitet das aktuell ausgewählte Mitglied."""
        rec = query_db('SELECT * FROM mitglieder WHERE mitglieder_id=?', (mid,), single=True)
        if not rec:
            QMessageBox.warning(self, "Fehler", "Das ausgewählte Mitglied existiert nicht mehr.")
            self.load_members()
            return

        dlg = MemberDialog(self, data=rec)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            query_db(
                'UPDATE mitglieder SET vorname=?, nachname=?, geburtsdatum=?, rolle=? WHERE mitglieder_id=?',
                (data['vorname'], data['nachname'], data['geburtsdatum'], data['rolle'], mid)
            )
            self.load_members()
            self.status.showMessage("Mitglied aktualisiert", 3000)

    def delete_member_by_id(self, mid):
        """Löscht ein Mitglied und alle zugehörigen Ergebnisse nach Bestätigung."""
        # Sicherheitsabfrage
        confirm = QMessageBox.question(
            self,
            "Mitglied löschen",
            "Willst du dieses Mitglied wirklich löschen?\n\n"
            "⚠ Dabei werden auch alle Ergebnisse dieses Mitglieds dauerhaft gelöscht!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            # --- Zuerst Ergebnisse löschen ---
            query_db("DELETE FROM ergebnisse WHERE mitglied_id=?", (mid,))

            # --- Dann Mitglied löschen ---
            query_db("DELETE FROM mitglieder WHERE mitglieder_id=?", (mid,))

            # --- UI aktualisieren ---
            self.load_trainings()
            self.load_members()
            self.status.showMessage("Mitglied und zugehörige Ergebnisse gelöscht", 3000)

        except Exception as e:
            QMessageBox.critical(self, "Fehler beim Löschen", f"Beim Löschen ist ein Fehler aufgetreten:\n{e}")

    # -------------------- Drucken --------------------

    def print_member_list(self):
        print_member_list(self)

    def print_member_stats_by_id(self, mid):
        print_member_statistics(mid)

    def load_all(self):
        self.load_trainings()
        self.load_members()
