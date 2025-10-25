from reportlab.lib.pagesizes import A4, A5
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, Flowable, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from PyQt6.QtCore import QDateTime
from db import query_db

# 1. Liste aller Jugendlichen
def export_youth_list(pdf_path="jugendliche.pdf"):
    rows = query_db("SELECT vorname, nachname, geburtsdatum FROM mitglieder ORDER BY nachname")
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    elements = []
    data = [["Vorname", "Nachname", "Geburtsdatum"]]
    for r in rows:
        data.append([r['vorname'], r['nachname'], r['geburtsdatum']])
    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ]))
    elements.append(t)
    doc.build(elements)

# 2. Einzelnes Training exportieren

from reportlab.lib.pagesizes import A4, A5
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from PyQt6.QtCore import QDateTime

def export_training_results(training_id, format="A4"):
    # 📄 Seitenformat festlegen
    page_size = A5 if format.upper() == "A5" else A4
    page_width, page_height = page_size

    # 📉 Skalierungsfaktor (Schrift und Tabellen)
    font_scale = 0.8 if format.upper() == "A5" else 1.0

    # Training und Zeiten holen
    training = query_db("SELECT * FROM training WHERE training_id=?", (training_id,), single=True)
    start_dt = QDateTime.fromString(training['startzeit'], 'yyyy-MM-dd HH:mm:ss')
    end_dt = QDateTime.fromString(training['endzeit'], 'yyyy-MM-dd HH:mm:ss')

    # 📁 PDF-Dateiname automatisch erstellen
    start_str = start_dt.toString("dd.MM.yyyy_HH-mm")
    end_str = end_dt.toString("HH-mm")
    pdf_file = f"training_{start_str}_bis_{end_str}Uhr_{format.upper()}.pdf"

    # 🧱 PDF-Dokument vorbereiten
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=page_size,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )
    elements = []
    styles = getSampleStyleSheet()

    # 🧾 Schriftarten mit Skalierung
    title_style = ParagraphStyle('Title', parent=styles['Title'],
                                 fontName='Helvetica-Bold',
                                 fontSize=16 * font_scale,
                                 alignment=1)
    header_style = ParagraphStyle('Header', parent=styles['Heading2'],
                                  fontName='Helvetica-Bold',
                                  fontSize=12 * font_scale)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'],
                                  fontName='Helvetica',
                                  fontSize=10 * font_scale)

    usable_width = page_width - doc.leftMargin - doc.rightMargin

    # 🏷️ Titel
    title_text = f"Training vom {start_dt.toString('dd.MM.yyyy')}<br/>{start_dt.toString('HH:mm')} - {end_dt.toString('HH:mm')} Uhr"
    title_paragraph = Paragraph(title_text, title_style)
    elements.append(title_paragraph)
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

    # 🖼️ Logo zeichnen (oben rechts)
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

    # 📘 PDF bauen mit Logo im Hintergrund
    doc.build(elements, onFirstPage=add_logo, onLaterPages=add_logo)
    return pdf_file



# 3. Statistik einzelner Mitglieder
def export_member_stats(member_id, pdf_path="mitglied_stats.pdf"):
    results = query_db("""
        SELECT k.name AS kategorie, e.gesamtpunktzahl
        FROM ergebnisse e
        LEFT JOIN kategorien k ON e.kategorie_id = k.kategorie_id
        WHERE e.mitglied_id=?
    """, (member_id,))
    
    stats = {}
    for r in results:
        stats.setdefault(r['kategorie'], []).append(r['gesamtpunktzahl'])
    
    categories = list(stats.keys())
    avg_points = [sum(stats[c])/len(stats[c]) for c in categories]
    
    with PdfPages(pdf_path) as pdf:
        fig, ax = plt.subplots(figsize=(8,4))
        ax.bar(categories, avg_points, color='skyblue')
        ax.set_ylabel('Durchschnittspunkte')
        ax.set_title('Durchschnitt pro Kategorie')
        plt.xticks(rotation=45)
        plt.tight_layout()
        pdf.savefig(fig)
        plt.close()
