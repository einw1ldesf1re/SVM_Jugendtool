from reportlab.lib.pagesizes import A4, A5
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QDateTime
from io import BytesIO
import os
import sys
import tempfile
from datetime import datetime, date
from db import query_db

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
    members = query_db("SELECT vorname, nachname, geburtsdatum FROM mitglieder ORDER BY nachname")
    member_data = [["ID", "Vorname", "Nachname", "Geburtsdatum", "Alter"]]
    for idx, m in enumerate(members, start=1):
        geburtsdatum = m['geburtsdatum']
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

        if(alter_int < 18):
            member_data.append([str(idx), m['vorname'], m['nachname'], geburtsdatum_str, alter_int])

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
    
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=16*font_scale, alignment=1, spaceAfter=5,leading=18)
    sub_title_style = ParagraphStyle('Header', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12*font_scale,  alignment=1, spaceBefore=0, spaceAfter=0, leading=14)
    header_style = ParagraphStyle('Header', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12 * font_scale)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontName='Helvetica', fontSize=10 * font_scale)

    usable_width = page_width - doc.leftMargin - doc.rightMargin

    # 🏷️ Titel
    title_text = f"Training vom {start_dt.toString('dd.MM.yyyy')}"
    elements.append(Paragraph(title_text, title_style))
    sub_title = f"{start_dt.toString('HH:mm')} - {end_dt.toString('HH:mm')} Uhr"
    elements.append(Paragraph(sub_title, sub_title_style))
    elements.append(Spacer(1, 10 * font_scale))

    # 👥 Teilnehmerliste
    participants = query_db("""
        SELECT DISTINCT m.vorname, m.nachname
        FROM ergebnisse e
        LEFT JOIN mitglieder m ON e.mitglied_id=m.mitglieder_id
        WHERE e.training_id=?
        ORDER BY m.nachname, m.vorname
    """, (training_id,))

    participant_data = [["ID", "Vorname", "Nachname"]]
    for idx, p in enumerate(participants, start=1):
        participant_data.append([idx, p['vorname'], p['nachname']])

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
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
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
        if disc['anschlag']:
            header_text = f"{disc['kategorie']} / {disc['schussanzahl']} Schuss / {disc['anschlag']}"
        else:
            header_text = f"{disc['kategorie']} / {disc['schussanzahl']} Schuss"
        elements.append(Paragraph(header_text, header_style))

        results = query_db("""
            SELECT m.vorname, m.nachname, e.gesamtpunktzahl
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
            table_data.append([idx, r['vorname'], r['nachname'], r['gesamtpunktzahl']])

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
