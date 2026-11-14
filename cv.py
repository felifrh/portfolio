#!/usr/bin/env python3
"""
cv.py: erzeugt den Lebenslauf als PDF für die About-Seite.

Aufruf:   python3 cv.py
Eingabe:  content/about.json (Text und Listen der About-Seite), content/projects/*.json (Projektliste)
Ausgabe:  assets/Felicitas-Ferch-CV.pdf

Warum so: Der Lebenslauf hat dieselbe Quelle wie die About-Seite. Wer dort etwas ändert, führt dieses
Skript noch einmal aus, und beides stimmt wieder überein. Im PDF stehen bewusst weder Geburtsdatum
noch Telefonnummer noch Anschrift. Braucht ReportLab:  pip3 install reportlab
"""
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

ROOT = Path(__file__).parent
about = json.loads((ROOT / "content/about.json").read_text(encoding="utf-8"))
site = json.loads((ROOT / "content/site.json").read_text(encoding="utf-8"))
projects = sorted((json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "content/projects").glob("*.json")),
                  key=lambda p: (-p["sortKey"], p.get("order", 0)))

# Dieselben Schriften wie auf der Website
pdfmetrics.registerFont(TTFont("Sans", str(ROOT / "assets/fonts/InstrumentSans-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Mono", str(ROOT / "assets/fonts/DMMono-Regular.ttf")))
BLACK, GREY, LILAC = HexColor("#0e0e10"), HexColor("#6b6b70"), HexColor("#5b5fe0")

name = ParagraphStyle("name", fontName="Sans", fontSize=30, leading=32, textColor=BLACK)
line = ParagraphStyle("line", fontName="Sans", fontSize=11, leading=15, textColor=BLACK)
mono = ParagraphStyle("mono", fontName="Mono", fontSize=7.5, leading=11, textColor=GREY)
head = ParagraphStyle("head", fontName="Mono", fontSize=7.5, leading=11, textColor=BLACK)
lead = ParagraphStyle("lead", fontName="Sans", fontSize=9.5, leading=13, textColor=BLACK)
text = ParagraphStyle("text", fontName="Sans", fontSize=8.5, leading=12, textColor=GREY)

contact = about["contact"]
email = f'{contact["emailUser"]}@{contact["emailDomain"]}'
website = site["url"].replace("https://", "www.")

story = [
    Paragraph(escape(site["name"]), name),
    Spacer(1, 4 * mm),
    Paragraph(escape(site["description"]), line),
    Spacer(1, 2 * mm),
    Paragraph(f'<a href="mailto:{email}" color="#5b5fe0">{email}</a>  ·  <a href="{site["url"]}" color="#5b5fe0">{website}</a>', mono),
    Spacer(1, 8 * mm),
]

def block(title, rows):
    """Ein Abschnitt: links die Überschrift, in der Mitte die Einträge, rechts die Zeitangabe."""
    data = []
    for i, (main, detail, meta) in enumerate(rows):
        cell = [Paragraph(escape(main), lead)] + ([Paragraph(escape(detail), text)] if detail else [])
        data.append([Paragraph(escape(title) if i == 0 else "", head), cell, Paragraph(escape(meta), mono)])
    table = Table(data, colWidths=[34 * mm, 104 * mm, 36 * mm])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE", (0, 0), (-1, 0), 0.5, BLACK),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
    ]))
    return [table, Spacer(1, 5 * mm)]

for section in about["sections"]:
    story += block(section["title"], [(i["lead"], i["text"], i["meta"]) for i in section["items"]])
story += block("Selected projects", [(p["title"], p["oneLiner"], p["year"]) for p in projects])

doc = SimpleDocTemplate(str(ROOT / "assets/Felicitas-Ferch-CV.pdf"), pagesize=A4,
                        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=16 * mm,
                        title=f'CV {site["name"]}', author=site["name"])
doc.build(story)
print("geschrieben: assets/Felicitas-Ferch-CV.pdf")
