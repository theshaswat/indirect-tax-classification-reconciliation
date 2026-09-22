"""Markdown -> PDF renderer for reports/*.md, using reportlab Platypus.
Adapted from the ecommerce-rto-risk-model project's renderer (same house style).
Usage: python3 build_pdf.py
"""
import re
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, KeepTogether)

REPORTS = Path(__file__).resolve().parents[1] / "reports"

NAVY = colors.HexColor("#1B2430")
LGREY = colors.HexColor("#F2F2F2")
DGREY = colors.HexColor("#6B7280")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, textColor=NAVY,
                          spaceBefore=2, spaceAfter=6, fontName="Helvetica-Bold", keepWithNext=1))
styles.add(ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12.5, textColor=NAVY,
                          spaceBefore=11, spaceAfter=5, fontName="Helvetica-Bold", keepWithNext=1))
styles.add(ParagraphStyle("H3", parent=styles["Heading3"], fontSize=11, textColor=NAVY,
                          spaceBefore=8, spaceAfter=4, fontName="Helvetica-Bold", keepWithNext=1))
styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.3, leading=12.4,
                          spaceAfter=5, alignment=TA_LEFT, allowWidows=0, allowOrphans=0))
styles.add(ParagraphStyle("BulletItem", parent=styles["Body"], leftIndent=14, bulletIndent=4, spaceAfter=3))
styles.add(ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8.3, leading=10.6, alignment=TA_LEFT))
styles.add(ParagraphStyle("CellHead", parent=styles["Cell"], fontName="Helvetica-Bold", textColor=colors.white))
styles.add(ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, textColor=DGREY,
                          fontName="Helvetica-Oblique", spaceAfter=6, leading=11))

UNICODE_SAFE = {
    "→": "->", "≈": "~", "×": " x ", "–": "-", "—": " - ", "−": "-", "‑": "-",
    "’": "'", "‘": "'", '"': '"', '"': '"', "…": "...",
}


def inline(text):
    text = re.sub(r"^\s*—\s*", "\x00IND\x00", text)
    text = re.sub(r"₹(?=\d)", "Rs ", text)
    text = text.replace("₹", "Rs")
    for bad, good in UNICODE_SAFE.items():
        text = text.replace(bad, good)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+?)`", r'<font face="Courier">\1</font>', text)
    text = re.sub(r"\s{2,}", " ", text)
    text = text.replace("\x00IND\x00", "&nbsp;&nbsp;&nbsp;")
    return text


def parse_table(lines, i):
    rows = []
    header = [c.strip() for c in lines[i].strip().strip("|").split("|")]
    rows.append(header)
    i += 2
    while i < len(lines) and lines[i].strip().startswith("|"):
        rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
        i += 1
    return rows, i


def make_table(rows, avail_width):
    if rows and all(not c.strip() for c in rows[0]):
        rows = rows[1:]
        has_header = False
    else:
        has_header = True
    if not rows:
        return Spacer(1, 0)
    ncols = len(rows[0])
    body_start = 1 if has_header else 0

    def is_numeric_col(c):
        vals = [rows[r][c] for r in range(body_start, len(rows)) if c < len(rows[r])]
        hits = sum(1 for v in vals if re.match(r"^[\$₹\-\(]?[\d,\.]+[%\)]?x?$|^[+\-]?[\d,\.]+%?$",
                   v.replace(",", "").replace(" ", "")) or v in ("—", "-", ""))
        return hits >= max(1, len(vals) * 0.6)

    numeric_cols = [is_numeric_col(c) for c in range(ncols)]
    first_col_width = min(avail_width * 0.32, 2.5 * inch)
    other_width = (avail_width - first_col_width) / max(1, ncols - 1)
    col_widths = [first_col_width] + [other_width] * (ncols - 1)

    data = []
    for r, row in enumerate(rows):
        cells = []
        for c in range(ncols):
            val = row[c] if c < len(row) else ""
            style = styles["CellHead"] if (has_header and r == 0) else styles["Cell"]
            cells.append(Paragraph(inline(val), style))
        data.append(cells)

    t = Table(data, colWidths=col_widths, repeatRows=1 if has_header else 0)
    ts = [("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
          ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 3),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("LEFTPADDING", (0, 0), (-1, -1), 5),
          ("RIGHTPADDING", (0, 0), (-1, -1), 5)]
    if has_header:
        ts += [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
               ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    first_body = 1 if has_header else 0
    for r in range(first_body, len(data)):
        if (r - first_body) % 2 == 1:
            ts.append(("BACKGROUND", (0, r), (-1, r), LGREY))
    for c in range(ncols):
        if numeric_cols[c] and c > 0:
            ts.append(("ALIGN", (c, first_body), (c, -1), "RIGHT"))
    t.setStyle(TableStyle(ts))
    return t


def build_story(md_text, avail_width):
    lines = md_text.split("\n")
    story, i, n = [], 0, len(md_text.split("\n"))
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("### "):
            story.append(Paragraph(inline(stripped[4:]), styles["H3"])); i += 1; continue
        if stripped.startswith("## "):
            story.append(Paragraph(inline(stripped[3:]), styles["H2"])); i += 1; continue
        if stripped.startswith("# "):
            story.append(Paragraph(inline(stripped[2:]), styles["H1"])); i += 1; continue
        if stripped.startswith("---") and set(stripped) <= {"-"}:
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#D9D9D9")))
            story.append(Spacer(1, 8)); i += 1; continue
        if stripped.startswith("|") and i + 1 < n and re.match(r"^\|?[\s:\-\|]+\|?$", lines[i + 1].strip()):
            rows, i = parse_table(lines, i)
            story.append(Spacer(1, 2))
            story.append(KeepTogether([make_table(rows, avail_width)]))
            story.append(Spacer(1, 6))
            continue
        if stripped.startswith("*") and stripped.endswith("*") and not stripped.startswith("**") and stripped.count("*") == 2:
            story.append(Paragraph(inline(stripped[1:-1]), styles["Small"])); i += 1; continue
        if re.match(r"^(\d+\.|[-*])\s+", stripped):
            bullet_text = re.sub(r"^(\d+\.|[-*])\s+", "", stripped)
            marker = re.match(r"^(\d+\.|[-*])\s+", stripped).group(1)
            bullet_char = marker if marker[0].isdigit() else "-"
            buf = [bullet_text]; i += 1
            while i < n and lines[i].strip() and not lines[i].strip().startswith(("#", "|", "---")) \
                    and not re.match(r"^(\d+\.|[-*])\s+", lines[i].strip()):
                buf.append(lines[i].strip()); i += 1
            story.append(Paragraph(f"{bullet_char}&nbsp;&nbsp;{inline(' '.join(buf))}", styles["BulletItem"]))
            continue
        buf = [stripped]; i += 1
        while i < n and lines[i].strip() and not lines[i].strip().startswith(("#", "|")) \
                and not re.match(r"^(\d+\.|[-*])\s+", lines[i].strip()):
            buf.append(lines[i].strip()); i += 1
        story.append(Paragraph(inline(" ".join(buf)), styles["Body"]))
    return story


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D9D9D9"))
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, 0.45 * inch, LETTER[0] - doc.rightMargin, 0.45 * inch)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(DGREY)
    canvas.drawString(doc.leftMargin, 0.30 * inch, doc.title)
    canvas.drawRightString(LETTER[0] - doc.rightMargin, 0.30 * inch, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def render(md_path, pdf_path, title, max_pages=None, min_scale=0.80):
    text = Path(md_path).read_text()
    scale = 1.0
    while True:
        doc = SimpleDocTemplate(str(pdf_path), pagesize=LETTER, topMargin=0.55 * inch,
                                bottomMargin=0.62 * inch, leftMargin=0.7 * inch,
                                rightMargin=0.7 * inch, title=title,
                                author="Shaswat Sharma", subject="Independent analysis")
        avail_width = LETTER[0] - doc.leftMargin - doc.rightMargin
        story = build_story(text, avail_width)
        doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
        pages = doc.page
        if max_pages is None or pages <= max_pages or scale <= min_scale:
            break
        scale = round(max(min_scale, scale - 0.03), 2)
        for name in ("H1", "H2", "H3", "Body", "BulletItem", "Cell", "CellHead", "Small"):
            st = styles[name]
            st.fontSize = round(st.fontSize * 0.97, 2)
            st.leading = round(st.leading * 0.97, 2)
    print(f"Wrote {pdf_path} ({pages} page(s))")


def main(title_prefix):
    render(REPORTS / "00_EXECUTIVE_SUMMARY.md", REPORTS / "00_EXECUTIVE_SUMMARY.pdf",
          f"{title_prefix} — Executive Summary", max_pages=1)
    render(REPORTS / "01_RECOMMENDATION_MEMO.md", REPORTS / "01_RECOMMENDATION_MEMO.pdf",
          f"{title_prefix} — Recommendation Memo")
    render(REPORTS / "02_DATA_DICTIONARY.md", REPORTS / "02_DATA_DICTIONARY.pdf",
          f"{title_prefix} — Data Dictionary", max_pages=1)
    render(REPORTS / "03_SOURCE_REGISTER.md", REPORTS / "03_SOURCE_REGISTER.pdf",
          f"{title_prefix} — Source Register", max_pages=1)
    render(REPORTS / "LIMITATIONS.md", REPORTS / "LIMITATIONS.pdf",
          f"{title_prefix} — Limitations", max_pages=1)


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "Report")
