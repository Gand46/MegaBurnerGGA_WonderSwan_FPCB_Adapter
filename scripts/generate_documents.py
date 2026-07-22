#!/usr/bin/env python3
"""Generate the final validation report and verified 1:1 template."""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ASSETS = ROOT / "assets"
VALIDATION = ROOT / "validation"
REPORT = DOCS / "final_validation_report.pdf"
TEMPLATE = DOCS / "mechanical_template_verified_1to1.pdf"

REGULAR_PATH = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
BOLD_PATH = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")
if REGULAR_PATH.exists() and BOLD_PATH.exists():
    pdfmetrics.registerFont(TTFont("FinalRegular", str(REGULAR_PATH)))
    pdfmetrics.registerFont(TTFont("FinalBold", str(BOLD_PATH)))
    REGULAR = "FinalRegular"
    BOLD = "FinalBold"
else:
    REGULAR = "Helvetica"
    BOLD = "Helvetica-Bold"

NAVY = colors.HexColor("#18324A")
BLUE = colors.HexColor("#246BCE")
GREEN = colors.HexColor("#167C45")
LIGHT_GREEN = colors.HexColor("#E8F6EE")
AMBER = colors.HexColor("#915B00")
LIGHT_AMBER = colors.HexColor("#FFF4D8")
GREY = colors.HexColor("#5A6570")
LIGHT_GREY = colors.HexColor("#F3F5F7")
GOLD = colors.HexColor("#E8B33B")


def paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def table_style() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), BOLD),
        ("FONTNAME", (0, 1), (-1, -1), REGULAR),
        ("FONTSIZE", (0, 0), (-1, -1), 8.2),
        ("LEADING", (0, 0), (-1, -1), 10.5),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C9D0D6")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])


def footer(pdf_canvas, document) -> None:
    pdf_canvas.saveState()
    pdf_canvas.setStrokeColor(colors.HexColor("#D7DCE1"))
    pdf_canvas.line(18 * mm, 14 * mm, 192 * mm, 14 * mm)
    pdf_canvas.setFont(REGULAR, 7.5)
    pdf_canvas.setFillColor(GREY)
    pdf_canvas.drawString(18 * mm, 9 * mm, "WonderSwan FPCB adapter - final package - KiCad 9.0.9")
    pdf_canvas.drawRightString(192 * mm, 9 * mm, f"Pagina {document.page}")
    pdf_canvas.restoreState()


def generate_report() -> None:
    data = json.loads((VALIDATION / "structural_report.json").read_text(encoding="utf-8"))
    styles = getSampleStyleSheet()
    title = ParagraphStyle("Title", parent=styles["Title"], fontName=BOLD, fontSize=21, leading=25, textColor=NAVY, alignment=TA_LEFT, spaceAfter=5 * mm)
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName=BOLD, fontSize=15, leading=18, textColor=NAVY, spaceBefore=3 * mm, spaceAfter=3 * mm)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName=BOLD, fontSize=11, leading=14, textColor=BLUE, spaceBefore=3 * mm, spaceAfter=2 * mm)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontName=REGULAR, fontSize=9.2, leading=12.7, textColor=colors.HexColor("#25313B"), spaceAfter=2.2 * mm)
    small = ParagraphStyle("Small", parent=body, fontSize=7.7, leading=10.2, textColor=GREY)
    header = ParagraphStyle("Header", parent=small, fontName=BOLD, textColor=colors.white)
    success = ParagraphStyle("Success", parent=body, fontName=BOLD, fontSize=10, leading=13.8, textColor=GREEN, backColor=LIGHT_GREEN, borderColor=GREEN, borderWidth=0.7, borderPadding=6, spaceAfter=4 * mm)
    warning = ParagraphStyle("Warning", parent=body, fontName=BOLD, fontSize=9.1, leading=12.7, textColor=AMBER, backColor=LIGHT_AMBER, borderColor=AMBER, borderWidth=0.7, borderPadding=6, spaceBefore=2 * mm, spaceAfter=4 * mm)

    document = SimpleDocTemplate(
        str(REPORT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=19 * mm,
        title="Informe final de validacion del adaptador FPCB WonderSwan",
        author="Codex",
    )
    story = [
        paragraph("Informe final del adaptador FPCB", title),
        paragraph("SOP-44 a TSOP II-44 para cartucho WonderSwan", h1),
        paragraph(
            f"Resultado digital: ERC 0, DRC 0, sin conexiones abiertas, paridad completa y "
            f"{data['checks_passed']}/{data['checks_total']} comprobaciones estructurales aprobadas.",
            success,
        ),
    ]
    summary = [
        [paragraph("Parametro", header), paragraph("Resultado final", header)],
        ["Dimensiones desplegadas", "17,30 x 58,00 mm"],
        ["Bisagra", "10,00 x 10,90 mm"],
        ["Conectividad", "44 redes directas J1.N -> J2.N"],
        ["J1 SOP-44", "Vertical, B.Cu, giro 90 grados"],
        ["J2 TSOP II-44", "Vertical, F.Cu, giro 180 grados; pin 1 exterior"],
        ["Pads J2", "1,40 x 0,45 mm; paso 0,80 mm; cobre al borde"],
        ["Ruteo en pliegue", "22 pistas F.Cu + 22 pistas B.Cu; ancho 0,15 mm"],
        ["Vias", "44 totales; 0 dentro de la bisagra"],
        ["Herramienta", "KiCad 9.0.9"],
    ]
    table = Table(summary, colWidths=[65 * mm, 106 * mm], repeatRows=1)
    table.setStyle(table_style())
    story.extend([table, Spacer(1, 4 * mm)])
    image = Image(str(ASSETS / "pcb_top.png"), width=63 * mm, height=100.8 * mm)
    image.hAlign = "CENTER"
    story.extend([image, paragraph("Vista superior regenerada desde el PCB final. J2 conserva sus contactos planos al borde y el pin 1 apunta hacia el extremo exterior.", small)])

    story.extend([
        PageBreak(),
        paragraph("Validacion electrica y mecanica", h1),
        paragraph("El proyecto fue comprobado directamente con kicad-cli y con un analizador independiente de las S-expressions del PCB.", body),
    ])
    checks = [
        [paragraph("Comprobacion", header), paragraph("Estado", header)],
        ["ERC", "0 infracciones"],
        ["DRC", "0 infracciones"],
        ["Elementos sin conectar", "0"],
        ["Paridad esquema/PCB", "0 problemas"],
        ["Referencias internas", "J1 y J2 coherentes"],
        ["Pads por extremo", "44 + 44"],
        ["Mapeo pin N a pin N", "44/44"],
        ["Pistas que cruzan el pliegue", "44; una por red"],
        ["Vias y pads dentro del pliegue", "0 / 0"],
        ["Vertices de pista dentro del pliegue", "0"],
        ["Validacion estructural", f"{data['checks_passed']}/{data['checks_total']}"],
    ]
    check_table = Table(checks, colWidths=[105 * mm, 66 * mm], repeatRows=1)
    check_table.setStyle(table_style())
    story.extend([check_table, Spacer(1, 4 * mm)])
    story.extend([
        paragraph("Zona flexible", h2),
        paragraph("La bisagra contiene 44 pistas verticales y rectas de 0,15 mm: 22 en F.Cu y 22 en B.Cu. No contiene vias, pads ni cambios de direccion. El ancho es 10,90 mm y la longitud libre es 10,00 mm.", success),
        paragraph("Interfaz J2", h2),
        paragraph("Los 44 pads J2 son SMD F.Cu/F.Mask, miden 1,40 x 0,45 mm, usan paso de 0,80 mm y alcanzan Edge.Cuts. No son castellated holes y no contienen perforaciones.", body),
        paragraph("La regla personalizada de J2 debe conservarse. Su funcion es documentar que el contacto con Edge.Cuts es intencional; el fabricante debe aprobar el proceso de cobre/ENIG al borde.", warning),
    ])

    story.extend([
        PageBreak(),
        paragraph("Fabricacion, trazabilidad y cierre", h1),
        paragraph("Fuente maestra", h2),
        paragraph("Este repositorio se construyo exclusivamente desde el archivo proyecto_Final.zip aportado por el usuario. SHA-256: 9b885df1952037dbf72eb71f1b5ff8135ade8380866d47dbfeffbfe19e24a85a.", body),
        paragraph("Correccion no geometrica", h2),
        paragraph("Las etiquetas visibles habian sustituido los identificadores internos J1/J2. Se restauraron J1 y J2 para recuperar la paridad con el esquema y la regla de borde. Las etiquetas MX26L64-MX29L32 y TSOP44 II se conservaron como serigrafia independiente. No se cambio ninguna coordenada de pad, pista, via, huella o Edge.Cuts.", body),
        paragraph("Entregables regenerados", h2),
    ])
    deliverables = [
        [paragraph("Grupo", header), paragraph("Contenido", header)],
        ["Fuentes", "Proyecto KiCad, librerias locales y reglas personalizadas"],
        ["Fabricacion", "Gerbers, PTH/NPTH, mapas, informe de taladro e IPC-2581"],
        ["Documentacion", "Esquema, PCB 1:1, plantilla mecanica e informe final"],
        ["Imagenes", "SVG de capas y renderizados 3D superior/inferior"],
        ["Automatizacion", "Scripts reproducibles y workflow de GitHub Actions"],
    ]
    deliverables_table = Table(deliverables, colWidths=[50 * mm, 121 * mm], repeatRows=1)
    deliverables_table.setStyle(table_style())
    story.extend([deliverables_table, Spacer(1, 4 * mm)])
    story.extend([
        paragraph("Condiciones antes de fabricar", h2),
        paragraph(
            "1. Imprimir la plantilla verificada al 100 por ciento y medir la barra de 50,00 mm.<br/>"
            "2. Superponer fisicamente el SOP y la PCB host para confirmar pin 1 y separaciones.<br/>"
            "3. Confirmar pista/espacio 0,15/0,10 mm, cobre de 12 um, espesor <=0,10 mm y ENIG.<br/>"
            "4. Mantener radio estatico >=1,20 mm y no usar como bisagra dinamica.<br/>"
            "5. Obtener aprobacion DFM del fabricante para contactos de cobre al borde.",
            body,
        ),
        paragraph("Estado final", h2),
        paragraph("Proyecto aprobado digitalmente y organizado para control de versiones. La liberacion fisica continua condicionada a plantilla 1:1, prueba dentro del cartucho y DFM del fabricante FPCB.", success),
    ])
    document.build(story, onFirstPage=footer, onLaterPages=footer)


def board_xy(origin_x: float, origin_y: float, scale: float, x: float, y: float) -> tuple[float, float]:
    return origin_x + (x - 5.65) * scale, origin_y + (58.0 - y) * scale


def draw_board(pdf: canvas.Canvas, origin_x: float, origin_y: float, scale: float, detailed: bool) -> None:
    outline = [
        (5.65, 0.0), (22.95, 0.0), (22.95, 28.6), (19.75, 29.6),
        (19.75, 58.0), (8.85, 58.0), (8.85, 29.6), (5.65, 28.6), (5.65, 0.0),
    ]
    path = pdf.beginPath()
    path.moveTo(*board_xy(origin_x, origin_y, scale, *outline[0]))
    for point in outline[1:]:
        path.lineTo(*board_xy(origin_x, origin_y, scale, *point))
    pdf.setFillColor(colors.Color(0.91, 0.70, 0.23, alpha=0.18) if detailed else colors.white)
    pdf.setStrokeColor(NAVY)
    pdf.setLineWidth(0.25 * mm if detailed else 0.16 * mm)
    pdf.drawPath(path, fill=1, stroke=1)

    pdf.setFillColor(colors.Color(0.15, 0.42, 0.81, alpha=0.20))
    hx, hy = board_xy(origin_x, origin_y, scale, 8.85, 39.6)
    pdf.rect(hx, hy, 10.90 * scale, 10.0 * scale, fill=1, stroke=0)
    pdf.setStrokeColor(BLUE)
    pdf.setDash(2.2, 1.4)
    for y in (29.6, 39.6):
        x1, yy = board_xy(origin_x, origin_y, scale, 8.85, y)
        pdf.line(x1, yy, x1 + 10.90 * scale, yy)
    pdf.setDash()

    pdf.setFillColor(colors.HexColor("#8E969E"))
    for row in range(22):
        y = 0.965 + row * 1.27
        for x in (7.05, 21.55):
            px, py = board_xy(origin_x, origin_y, scale, x, y)
            pdf.rect(px - 1.10 * scale, py - 0.325 * scale, 2.20 * scale, 0.65 * scale, fill=1, stroke=0)

    pdf.setFillColor(GOLD)
    for row in range(22):
        y = 40.40 + row * 0.80
        for x in (9.55, 19.05):
            px, py = board_xy(origin_x, origin_y, scale, x, y)
            pdf.rect(px - 0.70 * scale, py - 0.225 * scale, 1.40 * scale, 0.45 * scale, fill=1, stroke=0)

    if detailed:
        pdf.setFillColor(NAVY)
        pdf.setFont(BOLD, 8)
        center_x = origin_x + (14.30 - 5.65) * scale
        pdf.saveState()
        pdf.translate(center_x, origin_y + (58.0 - 14.3) * scale)
        pdf.rotate(90)
        pdf.drawCentredString(0, -3, "J1 SOP-44 - BOTTOM")
        pdf.restoreState()
        pdf.saveState()
        pdf.translate(center_x, origin_y + (58.0 - 48.8) * scale)
        pdf.rotate(90)
        pdf.drawCentredString(0, -3, "J2 TSOP II-44 - TOP")
        pdf.restoreState()
        pdf.setFillColor(BLUE)
        pdf.drawCentredString(center_x, hy + 4.7 * scale, "PLIEGUE 10.00 mm")


def dimension(pdf: canvas.Canvas, x1: float, y1: float, x2: float, y2: float, text: str, vertical: bool = False) -> None:
    pdf.setStrokeColor(GREY)
    pdf.setFillColor(GREY)
    pdf.setLineWidth(0.18 * mm)
    pdf.line(x1, y1, x2, y2)
    pdf.setFont(REGULAR, 7.5)
    if vertical:
        pdf.line(x1 - 1.5 * mm, y1, x1 + 1.5 * mm, y1)
        pdf.line(x2 - 1.5 * mm, y2, x2 + 1.5 * mm, y2)
        pdf.saveState()
        pdf.translate(x1 + 2.2 * mm, (y1 + y2) / 2)
        pdf.rotate(90)
        pdf.drawCentredString(0, 0, text)
        pdf.restoreState()
    else:
        pdf.line(x1, y1 - 1.5 * mm, x1, y1 + 1.5 * mm)
        pdf.line(x2, y2 - 1.5 * mm, x2, y2 + 1.5 * mm)
        pdf.drawCentredString((x1 + x2) / 2, y1 + 1.8 * mm, text)


def generate_template() -> None:
    pdf = canvas.Canvas(str(TEMPLATE), pagesize=A4)
    width, height = A4
    pdf.setTitle("Plantilla mecanica verificada 1:1")
    pdf.setAuthor("Codex")
    pdf.setFillColor(NAVY)
    pdf.setFont(BOLD, 17)
    pdf.drawString(18 * mm, height - 22 * mm, "Plantilla mecanica final verificada")
    pdf.setFont(REGULAR, 9)
    pdf.setFillColor(GREY)
    pdf.drawString(18 * mm, height - 29 * mm, "Imprimir al 100 % y desactivar cualquier ajuste de pagina")

    pdf.setFillColor(NAVY)
    pdf.setFont(BOLD, 11)
    pdf.drawString(20 * mm, height - 48 * mm, "PATRON DE MEDICION 1:1")
    true_x = 38 * mm
    true_y = 142 * mm
    draw_board(pdf, true_x, true_y, 1.0 * mm, False)
    dimension(pdf, true_x, true_y + 63 * mm, true_x + 17.3 * mm, true_y + 63 * mm, "17.30 mm")
    dimension(pdf, true_x + 23 * mm, true_y, true_x + 23 * mm, true_y + 58 * mm, "58.00 mm", vertical=True)

    pdf.setFillColor(NAVY)
    pdf.setFont(BOLD, 11)
    pdf.drawString(96 * mm, height - 48 * mm, "REFERENCIA AMPLIADA 2.5X")
    pdf.setFillColor(GREY)
    pdf.setFont(REGULAR, 7.5)
    pdf.drawString(96 * mm, height - 54 * mm, "No usar esta vista para medir.")
    draw_board(pdf, 106 * mm, 58 * mm, 2.5 * mm, True)

    pdf.setFillColor(NAVY)
    pdf.setFont(BOLD, 9)
    pdf.drawString(20 * mm, 58 * mm, "BARRA DE CONTROL: 50.00 mm")
    pdf.setStrokeColor(NAVY)
    pdf.setLineWidth(0.35 * mm)
    pdf.line(20 * mm, 51 * mm, 70 * mm, 51 * mm)
    pdf.line(20 * mm, 48 * mm, 20 * mm, 54 * mm)
    pdf.line(70 * mm, 48 * mm, 70 * mm, 54 * mm)
    pdf.setFillColor(GREY)
    pdf.setFont(REGULAR, 8)
    checklist = [
        "[ ] Barra mide 50.00 mm",
        "[ ] Ancho maximo mide 17.30 mm",
        "[ ] Largo desplegado mide 58.00 mm",
        "[ ] Bisagra mide 10.00 x 10.90 mm",
        "[ ] J2 pin 1 apunta al extremo exterior",
        "[ ] Caras J1 bottom / J2 top confirmadas",
    ]
    for index, item in enumerate(checklist):
        pdf.drawString(20 * mm, (42 - index * 4.2) * mm, item)

    pdf.setStrokeColor(colors.HexColor("#D7DCE1"))
    pdf.line(18 * mm, 12 * mm, 192 * mm, 12 * mm)
    pdf.setFont(REGULAR, 7)
    pdf.drawString(18 * mm, 7 * mm, "Final | 17.30 x 58.00 mm | pliegue 10.00 mm | KiCad 9.0.9")
    pdf.drawRightString(192 * mm, 7 * mm, "Escala primaria 1:1")
    pdf.showPage()
    pdf.save()


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    generate_report()
    generate_template()
    print(REPORT)
    print(TEMPLATE)


if __name__ == "__main__":
    main()
