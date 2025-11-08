from reportlab.lib.pagesizes import A4, A5
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QDateTime, QDate
from io import BytesIO
import os
import sys
from io import BytesIO
import matplotlib.pyplot as plt
import tempfile
from datetime import datetime, date
from matplotlib.ticker import MaxNLocator
from itertools import groupby
from operator import itemgetter
from db import query_db

from badge_manager import BadgeManager

styles = getSampleStyleSheet()
style = styles["BodyText"]

def print_member_list(parent=None, format="A4"):
    page_size = A5 if format.upper() == "A5" else A4
    page_width, page_height = page_size

    # 📉 Skalierungsfaktor (Schrift und Tabellen)
    font_scale = 0.8 if format.upper() == "A5" else 1.0

    # === PDF IM SPEICHER GENERIEREN ===
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=page_size,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )
    elements = []
    styles = getSampleStyleSheet()

    # 🧾 Schriftarten
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=16*font_scale, alignment=1, spaceAfter=5,leading=18)
    sub_title_style = ParagraphStyle('Header', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12*font_scale,  alignment=1, spaceBefore=0, spaceAfter=0, leading=14)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontName='Helvetica', fontSize=10*font_scale)

    usable_width = page_width - doc.leftMargin - doc.rightMargin

    # Titel
    title_text = "Mitgliederliste Jugend"
    elements.append(Paragraph(title_text, title_style))

    # Untertitel
    jetzt = datetime.now()
    formatierte_zeit = jetzt.strftime("%d.%m.%Y %H:%M")
    sub_title = f"Stand: {formatierte_zeit} Uhr"
    elements.append(Paragraph(sub_title, sub_title_style))

    # Abstand nur zwischen Untertitel und Tabelle
    elements.append(Spacer(1, 15 * font_scale))

    def berechne_alter(geburtsdatum):
        # Wenn String aus der DB kommt (z. B. "2008-04-15")
        if isinstance(geburtsdatum, str):
            try:
                geburtsdatum = datetime.strptime(geburtsdatum, "%Y-%m-%d").date()
            except ValueError:
                return None  # falls Format nicht erkannt wird

        heute = date.today()
        alter = heute.year - geburtsdatum.year - (
            (heute.month, heute.day) < (geburtsdatum.month, geburtsdatum.day)
        )
        return alter

    # 👥 Mitglieder aus DB laden
    members = query_db("SELECT vorname, nachname, geburtsdatum, rolle FROM mitglieder ORDER BY nachname")
    member_data = [["ID", "Vorname", "Nachname", "Geburtsdatum", "Alter"]]

    counter = 1;

    for idx, m in enumerate(members, start=1):
        geburtsdatum = m['geburtsdatum']

        if(m['rolle'] == "gast"):
            continue

        # 🗓️ In dd.MM.yyyy umwandeln, falls Datumstyp oder ISO-String
        if isinstance(geburtsdatum, (datetime,)):
            geburtsdatum_str = geburtsdatum.strftime("%d.%m.%Y")
        elif isinstance(geburtsdatum, str):
            try:
                geburtsdatum_str = datetime.strptime(geburtsdatum, "%Y-%m-%d").strftime("%d.%m.%Y")
            except ValueError:
                geburtsdatum_str = geburtsdatum  # falls schon formatiert
        else:
            geburtsdatum_str = str(geburtsdatum)

        alter_int = berechne_alter(geburtsdatum)

        if alter_int < 0:
            alter_text = "-"
        elif alter_int < 18:
            alter_text = f"<font color='darkgreen'>✓ {alter_int}</font>"
        elif alter_int < 26:
            alter_text = f"<font color='darkorange'>! {alter_int}</font>"
        elif alter_int >= 26:
            alter_text = f"<font color='darkred'>X {alter_int}</font>"
        else:
            alter_text = str(alter_int)


        if(alter_int < 26):
            row = [
                Paragraph(str(counter), style),
                Paragraph(m['vorname'], style),
                Paragraph(m['nachname'], style),
                Paragraph(geburtsdatum_str, style),
                Paragraph(alter_text, style),  # 👈 hier wird Farbe korrekt dargestellt
            ]
            member_data.append(row)
            counter+=1

    col_widths = [
        usable_width * 0.08,  # ID schmal
        usable_width * 0.25,  # Vorname
        usable_width * 0.25,  # Nachname
        usable_width * 0.25,  # Geburtsdatum
        usable_width * 0.17,  # Alter
    ]
    member_table = Table(member_data, colWidths=col_widths, repeatRows=1)
    member_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9*font_scale),
    ]))
    elements.append(member_table)
    elements.append(Spacer(1, 10*font_scale))

    # 🖼️ Logo oben rechts
    def add_logo(canvas_obj, doc_obj):
        logo_path = "assets/images/logo.png"
        logo_width = 100 * font_scale
        logo_height = 70 * font_scale
        canvas_obj.drawImage(
            logo_path,
            page_width - logo_width - 10,
            page_height - logo_height - 10,
            width=logo_width,
            height=logo_height,
            mask='auto'
        )

    # 📘 PDF bauen
    doc.build(elements, onFirstPage=add_logo, onLaterPages=add_logo)

    zeit_str = jetzt.strftime("%d.%m.%Y_%H-%M")

    # === Temporäre PDF-Datei für Vorschau mit gewünschtem Namen ===
    tmp_filename = os.path.join(tempfile.gettempdir(), f"jugendliste_{zeit_str}.pdf")
    with open(tmp_filename, "wb") as f:
        f.write(pdf_buffer.getvalue())

    # === PDF in Standard-Viewer öffnen (für Vorschau) ===
    try:
        if sys.platform.startswith("win"):
            os.startfile(tmp_filename)
        elif sys.platform.startswith("darwin"):
            os.system(f"open '{tmp_filename}'")
        else:
            os.system(f"xdg-open '{tmp_filename}'")
    except Exception as e:
        QMessageBox.critical(parent, "Fehler", f"PDF konnte nicht geöffnet werden: {str(e)}")

def print_training_results(training_id, parent=None, format="A4"):
    # 📄 Seitenformat festlegen
    page_size = A5 if format.upper() == "A5" else A4
    page_width, page_height = page_size

    # 📉 Skalierungsfaktor (Schrift und Tabellen)
    font_scale = 0.8 if format.upper() == "A5" else 1.0

    # Training und Zeiten holen
    training = query_db("SELECT * FROM training WHERE training_id=?", (training_id,), single=True)
    if not training:
        QMessageBox.warning(parent, "Fehler", "Kein Training mit dieser ID gefunden.")
        return

    start_dt = QDateTime.fromString(training['startzeit'], 'yyyy-MM-dd HH:mm:ss')
    end_dt = QDateTime.fromString(training['endzeit'], 'yyyy-MM-dd HH:mm:ss')

    # === PDF IM SPEICHER GENERIEREN ===
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=page_size,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )
    elements = []
    styles = getSampleStyleSheet()

    # 🧾 Schriftarten mit Skalierung
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontName='Helvetica-Bold',
                                 fontSize=16*font_scale, alignment=1, spaceAfter=5, leading=18)
    sub_title_style = ParagraphStyle('Header', parent=styles['Heading2'], fontName='Helvetica-Bold',
                                     fontSize=12*font_scale, alignment=1, spaceBefore=0, spaceAfter=0, leading=14)
    header_style = ParagraphStyle('Header', parent=styles['Heading2'], fontName='Helvetica-Bold',
                                  fontSize=12 * font_scale)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontName='Helvetica',
                                  fontSize=10 * font_scale)

    usable_width = page_width - doc.leftMargin - doc.rightMargin

    # 🏷️ Titel
    title_text = f"Training vom {start_dt.toString('dd.MM.yyyy')}"
    elements.append(Paragraph(title_text, title_style))
    sub_title = f"{start_dt.toString('HH:mm')} - {end_dt.toString('HH:mm')} Uhr"
    elements.append(Paragraph(sub_title, sub_title_style))
    elements.append(Spacer(1, 10 * font_scale))

    participants = query_db("""
        SELECT DISTINCT m.vorname, m.nachname, m.rolle
        FROM ergebnisse e
        LEFT JOIN mitglieder m ON e.mitglied_id=m.mitglieder_id
        WHERE e.training_id=?
    """, (training_id,))

    # Teilnehmer nach Rolle trennen
    members = [p for p in participants if p.get('rolle', '').lower() != 'gast']
    guests = [p for p in participants if p.get('rolle', '').lower() == 'gast']

    # Alphabetisch sortieren
    members.sort(key=lambda x: (x['nachname'].lower(), x['vorname'].lower()))
    guests.sort(key=lambda x: (x['nachname'].lower(), x['vorname'].lower()))

    participant_data = [["ID", "Vorname", "Nachname"]]

    # Helferfunktion zum Hinzufügen in die Tabelle
    def add_participant_row(idx, p, is_guest):
        vorname = p['vorname']
        nachname = p['nachname']
        if is_guest:
            vorname += " (Gast)"
            vorname_para = Paragraph(f"<font color='grey'><i>{vorname}</i></font>",
                                    ParagraphStyle('LeftGuest', parent=normal_style, alignment=0))
            nachname_para = Paragraph(f"<font color='grey'><i>{nachname}</i></font>",
                                    ParagraphStyle('LeftGuest', parent=normal_style, alignment=0))
        else:
            vorname_para = Paragraph(vorname,
                                    ParagraphStyle('LeftNormal', parent=normal_style, alignment=0))
            nachname_para = Paragraph(nachname,
                                    ParagraphStyle('LeftNormal', parent=normal_style, alignment=0))
        participant_data.append([idx, vorname_para, nachname_para])

    # Mitglieder zuerst
    for idx, p in enumerate(members, start=1):
        add_participant_row(idx, p, is_guest=False)

    # Gäste danach
    for idx, p in enumerate(guests, start=len(members)+1):
        add_participant_row(idx, p, is_guest=True)

    id_width = 25 * font_scale
    remaining_width = usable_width - id_width
    col_widths = [id_width, remaining_width / 2, remaining_width / 2]

    participant_table = Table(participant_data, colWidths=col_widths, repeatRows=1)
    participant_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9 * font_scale),
    ]))
    elements.append(Paragraph("Teilnehmerliste:", header_style))
    elements.append(participant_table)
    elements.append(Spacer(1, 14 * font_scale))

    # 🎯 Ergebnisse nach Disziplin
    disciplines = query_db("""
        SELECT DISTINCT k.name AS kategorie, e.schussanzahl, a.name AS anschlag
        FROM ergebnisse e
        LEFT JOIN kategorien k ON e.kategorie_id=k.kategorie_id
        LEFT JOIN anschlaege a ON e.anschlag_id=a.anschlag_id
        WHERE e.training_id=?
        ORDER BY k.name, a.name, e.schussanzahl
    """, (training_id,))

    for disc in disciplines:
        header_text = f"{disc['kategorie']}" + (f" / {disc['schussanzahl']} Schuss" if disc['schussanzahl'] != 0 else "") + (f" / {disc['anschlag']}" if disc['anschlag'] else "")
        elements.append(Paragraph(header_text, header_style))

        results = query_db("""
            SELECT m.vorname, m.nachname, m.rolle, e.gesamtpunktzahl
            FROM ergebnisse e
            LEFT JOIN mitglieder m ON e.mitglied_id=m.mitglieder_id
            LEFT JOIN kategorien k ON e.kategorie_id=k.kategorie_id
            LEFT JOIN anschlaege a ON e.anschlag_id=a.anschlag_id
            WHERE e.training_id=? AND k.name=? AND e.schussanzahl=? 
            AND (a.name=? OR (a.name IS NULL AND ? IS NULL))
            ORDER BY e.gesamtpunktzahl DESC, m.nachname, m.vorname
        """, (training_id, disc['kategorie'], disc['schussanzahl'], disc['anschlag'], disc['anschlag']))

        table_data = [["Rang", "Vorname", "Nachname", "Ergebnis"]]
        for idx, r in enumerate(results, start=1):
            vorname = r['vorname']
            nachname = r['nachname']

            # Gast prüfen
            is_guest = r.get('rolle', '').lower() == 'gast'
            if is_guest:
                vorname_para = Paragraph(f"<font color='grey'><i>{vorname}</i></font>", ParagraphStyle('LeftGuest', parent=normal_style, alignment=0))
                nachname_para = Paragraph(f"<font color='grey'><i>{nachname}</i></font>", ParagraphStyle('LeftGuest', parent=normal_style, alignment=0))
            else:
                vorname_para = Paragraph(vorname, ParagraphStyle('LeftNormal', parent=normal_style, alignment=0))
                nachname_para = Paragraph(nachname, ParagraphStyle('LeftNormal', parent=normal_style, alignment=0))

            ergebnis = str(r['gesamtpunktzahl']).strip()
            if ergebnis in ("0", "0.0", "", "None", "null"):
                ergebnis = "k.A."

            table_data.append([idx, vorname_para, nachname_para, ergebnis])

        rank_width = 25 * font_scale
        points_width = 45 * font_scale
        remaining_width = usable_width - rank_width - points_width
        col_widths = [rank_width, remaining_width / 2, remaining_width / 2, points_width]

        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9 * font_scale),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 10 * font_scale))

    # 🖼️ Logo oben rechts
    def add_logo(canvas_obj, doc_obj):
        logo_path = "assets/images/logo.png"
        logo_width = 100 * font_scale
        logo_height = 70 * font_scale
        canvas_obj.drawImage(
            logo_path,
            page_width - logo_width - 10,
            page_height - logo_height - 10,
            width=logo_width,
            height=logo_height,
            mask='auto'
        )

    # 📘 PDF bauen
    doc.build(elements, onFirstPage=add_logo, onLaterPages=add_logo)

    # === Temporäre PDF-Datei für Vorschau mit gewünschtem Namen ===
    start_str = start_dt.toString("dd.MM.yyyy_HH-mm")
    end_str = end_dt.toString("HH-mm")
    tmp_filename = os.path.join(tempfile.gettempdir(), f"training_{start_str}_bis_{end_str}Uhr.pdf")

    with open(tmp_filename, "wb") as f:
        f.write(pdf_buffer.getvalue())

    # === PDF in Standard-Viewer öffnen (für Vorschau) ===
    try:
        if sys.platform.startswith("win"):
            os.startfile(tmp_filename)
        elif sys.platform.startswith("darwin"):
            os.system(f"open '{tmp_filename}'")
        else:
            os.system(f"xdg-open '{tmp_filename}'")
    except Exception as e:
        QMessageBox.critical(parent, "Fehler", f"PDF konnte nicht geöffnet werden: {str(e)}")

def print_member_statistics(mid, parent=None, format="A4"):
    # === Seiten & Schriftgrößen ===
    page_size = A5 if format.upper() == "A5" else A4
    page_width, page_height = page_size
    font_scale = 0.8 if format.upper() == "A5" else 1.0

    # === Mitgliedsdaten ===
    member = query_db("SELECT * FROM mitglieder WHERE mitglieder_id=?", (mid,), single=True)
    if not member:
        QMessageBox.warning(parent, "Fehler", "Mitglied nicht gefunden.")
        return

    name = f"{member['vorname']} {member['nachname']}"
    geburtsdatum = QDate.fromString(member['geburtsdatum'], "yyyy-MM-dd")
    age = QDate.currentDate().year() - geburtsdatum.year()
    if (QDate.currentDate().month(), QDate.currentDate().day()) < (geburtsdatum.month(), geburtsdatum.day()):
        age -= 1

    # === Ergebnisse laden ===
    results = query_db("""
        SELECT e.*, t.startzeit, k.name AS kategorie, a.name AS anschlag
        FROM ergebnisse e
        LEFT JOIN training t ON t.training_id = e.training_id
        LEFT JOIN kategorien k ON k.kategorie_id = e.kategorie_id
        LEFT JOIN anschlaege a ON a.anschlag_id = e.anschlag_id
        WHERE e.mitglied_id=?
        ORDER BY t.startzeit
    """, (mid,))

    if not results:
        QMessageBox.information(parent, "Keine Daten", "Für dieses Mitglied existieren keine Ergebnisse.")
        return

    total_trainings = len(set(r['training_id'] for r in results))
    stand_datum = QDateTime.currentDateTime().toString('dd.MM.yyyy HH:mm')

    # === PDF Setup ===
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=page_size,
        rightMargin=25, leftMargin=25, topMargin=90, bottomMargin=40
    )
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=16*font_scale, alignment=1, leading=18)
    header_style = ParagraphStyle('Header', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12*font_scale)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontName='Helvetica', fontSize=10*font_scale)

    # === Funktion für Header und Footer auf jeder Seite ===
    def add_page_info(canvas_obj, doc_obj):
        # Logo oben rechts
        logo_path = "assets/images/logo.png"
        logo_width = 100 * font_scale
        logo_height = 70 * font_scale
        canvas_obj.drawImage(
            logo_path,
            page_width - logo_width - 10,
            page_height - logo_height - 10,
            width=logo_width,
            height=logo_height,
            mask='auto'
        )

        # Überschrift + Basisdaten
        canvas_obj.setFont("Helvetica-Bold", 14*font_scale)
        canvas_obj.drawString(25, page_height - 50, f"Leistungsübersicht: {name}")

        canvas_obj.setFont("Helvetica", 10*font_scale)
        if age > 0:
            canvas_obj.drawString(25, page_height - 65, f"Geburtsdatum: {geburtsdatum.toString('dd.MM.yyyy')} ({age} Jahre)")
        else:
            canvas_obj.drawString(25, page_height - 65, f"Geburtsdatum: -")
        
        canvas_obj.drawString(25, page_height - 80, f"Trainings teilgenommen: {total_trainings}")

        # Stand-Zeile
        canvas_obj.setFont("Helvetica", 9*font_scale)
        canvas_obj.drawString(25, page_height - 95, f"Stand: {stand_datum} Uhr")

        # Seitenzahl unten
        canvas_obj.setFont("Helvetica", 9*font_scale)
        canvas_obj.drawRightString(page_width - 25, 25, f"Seite {doc_obj.page}")

    elements.append(Spacer(1, 20))

    # === Trainingsbeteiligung pro Disziplin (Tortendiagramm) ===
    disc_counts = query_db("""
        SELECT k.name AS kategorie, COUNT(DISTINCT e.training_id) AS trainings
        FROM ergebnisse e
        LEFT JOIN kategorien k ON k.kategorie_id=e.kategorie_id
        WHERE e.mitglied_id=?
        GROUP BY k.name
    """, (mid,))

    if disc_counts:
        labels = [d['kategorie'] for d in disc_counts]
        sizes = [d['trainings'] for d in disc_counts]
        
        # kleinere Figur
        fig, ax = plt.subplots(figsize=(3,3))  # vorher 4x4
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.set_title("Trainingsbeteiligung pro Disziplin", fontsize=10)
        plt.tight_layout()
        
        chart_path = os.path.join(tempfile.gettempdir(), f"pie_{mid}.png")
        plt.savefig(chart_path, dpi=150)
        plt.close(fig)
        
        # kleiner im PDF einfügen
        img_width = page_width / 3  # vorher page_width/2
        elements.append(Image(chart_path, width=img_width, height=img_width))
        elements.append(Spacer(1, 10))  # kleiner Spacer

    # === Bestes Ergebnis pro Disziplin ===
    best_results = query_db("""
        SELECT 
            k.name AS kategorie, 
            e.anschlag_id, 
            e.schussanzahl, 
            e.gesamtpunktzahl, 
            t.startzeit, 
            COALESCE(a.name, '') AS anschlag
        FROM ergebnisse e
        LEFT JOIN kategorien k ON k.kategorie_id = e.kategorie_id
        LEFT JOIN training t ON t.training_id = e.training_id
        LEFT JOIN anschlaege a ON a.anschlag_id = e.anschlag_id
        WHERE e.mitglied_id=?
        AND e.schussanzahl > 0
        AND e.gesamtpunktzahl = (
            SELECT MAX(e2.gesamtpunktzahl)
            FROM ergebnisse e2
            WHERE e2.mitglied_id=? 
                AND e2.kategorie_id = e.kategorie_id
                AND (e2.anschlag_id = e.anschlag_id OR (e2.anschlag_id IS NULL AND e.anschlag_id IS NULL))
                AND e2.schussanzahl = e.schussanzahl
        )
        ORDER BY k.name, anschlag, e.schussanzahl
    """, (mid, mid))

    if(best_results):
        elements.append(Paragraph("Bestes Ergebnis pro Disziplin:", header_style))
        table_data = [["Disziplin", "Anschlag", "Schussanzahl", "Punkte", "Datum"]]
        for r in best_results:

            date_str = QDateTime.fromString(r['startzeit'], 'yyyy-MM-dd HH:mm:ss').toString('dd.MM.yyyy')
            table_data.append([r['kategorie'], r['anschlag'] or "-", r['schussanzahl'], r['gesamtpunktzahl'], date_str])

        col_widths = [
            (page_width - 50) * 0.25,
            (page_width - 50) * 0.15,
            (page_width - 50) * 0.20,
            (page_width - 50) * 0.15,
            (page_width - 50) * 0.25,
        ]
        t = Table(table_data, colWidths=col_widths, hAlign='CENTER')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('ALIGN', (2,1), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10*font_scale),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 14))

    # === Badges laden und darstellen ===
    badge_manager = BadgeManager()
    badges = badge_manager.get_badges(mid)

    if badges:
        elements.append(Spacer(1, 14))
        elements.append(Paragraph("Erreichte Auszeichnungen:", header_style))
        elements.append(Spacer(1, 6))

        badge_elements = []
        row = []
        max_cols = 4
        icon_size = 50 * font_scale

        for b in badges:
            badge_key = b['badge_key']
            current_level = b['current_level']

            badge_info = badge_manager.badges.get(badge_key)
            if not badge_info:
                continue

            levels = badge_info.get('levels', {})
            level_key = current_level
            if level_key not in levels:
                continue

            level_data = levels[level_key]
            ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets", "badges")
            icon_rel_path = level_data['icon']
            icon_path = os.path.join(ASSETS_PATH, icon_rel_path)
            label = level_data['label']

            description = level_data['description']

            img = Image(icon_path, width=icon_size, height=icon_size)
            label_para = Paragraph(f"<b>{label}</b>", ParagraphStyle('badgeLabel', parent=normal_style, alignment=1, fontSize=8*font_scale))
            desc_para = Paragraph(description, ParagraphStyle('badgeDesc', parent=normal_style, alignment=1, fontSize=6*font_scale, leading=7*font_scale))

            cell = [img, label_para, desc_para]
            row.append(cell)

            if len(row) == max_cols:
                badge_elements.append(row)
                row = []

        if row:
            while len(row) < max_cols:
                row.append(Spacer(1, icon_size + 20))
            badge_elements.append(row)

        if badge_elements:
            table = Table(badge_elements, colWidths=[(page_width - 50)/max_cols]*max_cols, hAlign='CENTER')
            table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 14))

    # === Verlaufdiagramme 2 nebeneinander ===

    valid_results = [
        r for r in results
        if r.get('schussanzahl') and r['schussanzahl'] > 0
    ]

    results_sorted = sorted(
        valid_results,
        key=lambda r: (
            r['kategorie'] or '',
            r['anschlag'] or '',
            r['schussanzahl']
        )
    )
    line_charts = []
    for (disc, anschlag, schussanzahl), group in groupby(
        results_sorted,
        key=lambda r: (
            r['kategorie'] or '',
            r['anschlag'] or '',
            r['schussanzahl']
        )
    ):
        disc_results = list(group)
        if len(disc_results) < 2:
            continue

        dates = [QDateTime.fromString(r['startzeit'], 'yyyy-MM-dd HH:mm:ss').toString('dd.MM.yy') for r in disc_results]
        points = [r['gesamtpunktzahl'] for r in disc_results]

        width_inch = min(max(len(dates) * 1.2, 5), 7)
        height_inch = 2.7

        fig, ax = plt.subplots(figsize=(width_inch, height_inch), dpi=150)
        ax.plot(dates, points, marker='o', linestyle='-', color='blue')
        title_str = f"{disc} ({anschlag or '-'} / {schussanzahl} Schüsse)"
        ax.set_title(title_str, fontsize=10*font_scale)
        ax.set_xlabel("Datum", fontsize=9*font_scale)
        ax.set_ylabel("Punkte", fontsize=9*font_scale)
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=min(len(dates), 6)))
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=8*font_scale)
        plt.tight_layout()

        chart_path = os.path.join(tempfile.gettempdir(), f"line_{mid}_{disc}_{anschlag}_{schussanzahl}.png")
        plt.savefig(chart_path, dpi=150)
        plt.close(fig)

        img = Image(chart_path, width=page_width/2 - 40, height=height_inch*80)
        line_charts.append(img)

    for i in range(0, len(line_charts), 2):
        row = line_charts[i:i+2]
        if len(row) == 1:
            row.append(Spacer(1, height_inch*90))
        elements.append(Table([row], colWidths=[page_width/2 - 30]*2, hAlign='CENTER'))
        elements.append(Spacer(1, 12))

    # === PDF bauen ===
    doc.build(elements, onFirstPage=add_page_info, onLaterPages=add_page_info)

    # === Datei speichern & öffnen ===
    tmp_filename = os.path.join(tempfile.gettempdir(), f"mitglied_{member['nachname']}_{member['vorname']}.pdf")
    with open(tmp_filename, "wb") as f:
        f.write(pdf_buffer.getvalue())

    try:
        if sys.platform.startswith("win"):
            os.startfile(tmp_filename)
        elif sys.platform.startswith("darwin"):
            os.system(f"open '{tmp_filename}'")
        else:
            os.system(f"xdg-open '{tmp_filename}'")
    except Exception as e:
        QMessageBox.critical(parent, "Fehler", f"PDF konnte nicht geöffnet werden: {e}")
