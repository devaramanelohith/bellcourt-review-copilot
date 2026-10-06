"""Tiny Markdown to PDF for the docs folder (headings, paragraphs, bullets, tables, bold, code spans).  python scripts/md_to_pdf.py docs/X.md docs/X.pdf"""
import re, sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
try:
    A = "/System/Library/Fonts/Supplemental/"; pdfmetrics.registerFont(TTFont("B", A + "Arial.ttf")); pdfmetrics.registerFont(TTFont("BB", A + "Arial Bold.ttf"))
    pdfmetrics.registerFontFamily("B", normal="B", bold="BB", italic="B", boldItalic="BB"); F, FB = "B", "BB"
except Exception: F, FB = "Helvetica", "Helvetica-Bold"
NAVY = colors.HexColor("#104281"); HAIR = colors.HexColor("#e1e0d9"); HEAD = colors.HexColor("#eef0f2"); W, H = A4; M = 15 * mm; CW = W - 2 * M
st = lambda n, **k: ParagraphStyle(n, **{**dict(fontName=F, fontSize=9.4, leading=13, textColor=colors.HexColor("#0b0b0b")), **k})
S = dict(t=st("t", fontName=FB, fontSize=20, leading=24, textColor=NAVY), h2=st("h2", fontName=FB, fontSize=13, leading=16, textColor=NAVY, spaceBefore=10, spaceAfter=2), h3=st("h3", fontName=FB, fontSize=10.5, leading=14, spaceBefore=8, spaceAfter=2),
         b=st("b", spaceAfter=5), bu=st("bu", leftIndent=11, bulletIndent=1, spaceAfter=2.5), c=st("c", fontSize=8.2, leading=10.6), cb=st("cb", fontName=FB, fontSize=8.2, leading=10.6), q=st("q", fontName=FB, spaceBefore=6, spaceAfter=1))
def inl(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"); t = re.sub(r"`([^`]+)`", r'<font face="Courier" size="8.5">\1</font>', t); return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
src = open(sys.argv[1]).read().split("\n"); E = []; i = 0; para = []
def flush():
    global para
    if para: E.append(Paragraph(inl(" ".join(para)), S["q"] if para[0].startswith("**Q:") else S["b"])); para = []
while i < len(src):
    ln = src[i]
    if ln.startswith("|"):
        flush(); rows = []
        while i < len(src) and src[i].startswith("|"):
            cells = [c.strip() for c in src[i].strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells): rows.append(cells)
            i += 1
        n = len(rows[0]); lens = [max(len(r[c]) for r in rows if c < len(r)) for c in range(n)]; tot = sum(min(l, 60) + 8 for l in lens); w = [CW * (min(l, 60) + 8) / tot for l in lens]
        t = Table([[Paragraph(inl(c), S["cb"] if k == 0 else S["c"]) for c in r + [""] * (n - len(r))] for k, r in enumerate(rows)], colWidths=w, repeatRows=1)
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, 0), HEAD), ("LINEBELOW", (0, 0), (-1, -1), 0.4, HAIR), ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        E += [t, Spacer(1, 6)]; continue
    if ln.startswith("!["):
        flush(); from reportlab.platypus import Image; from reportlab.lib.utils import ImageReader; import os
        mm_ = re.match(r"!\[.*?\]\((.+?)\)(?:\{(\d+)%\})?", ln); pth = mm_.group(1); frac = int(mm_.group(2) or 100) / 100
        pth = pth if os.path.isabs(pth) else os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "..", pth) if not os.path.exists(pth) else pth
        iw, ih = ImageReader(pth).getSize(); w = min(CW, iw) * frac; E += [Image(pth, width=w, height=w * ih / iw), Spacer(1, 6)]; i += 1; continue
    if ln.startswith("# "): flush(); E.append(Paragraph(inl(ln[2:]), S["t"])); E.append(Spacer(1, 4))
    elif ln.startswith("## "): flush(); E += [Paragraph(inl(ln[3:]), S["h2"]), HRFlowable(width="100%", thickness=0.8, color=NAVY, spaceAfter=4)]
    elif ln.startswith("### "): flush(); E.append(Paragraph(inl(ln[4:]), S["h3"]))
    elif ln.startswith("- "): flush(); E.append(Paragraph(inl(ln[2:]), S["bu"], bulletText="•"))
    elif re.match(r"^\d+\. ", ln): flush(); m = re.match(r"^(\d+)\. (.*)", ln); E.append(Paragraph(inl(m.group(2)), S["bu"], bulletText=m.group(1) + "."))
    elif ln.strip() in ("", "---"): flush()
    else: para.append(ln)
    i += 1
flush()
def foot(c, d): c.saveState(); c.setFont(F, 7.5); c.setFillColor(colors.HexColor("#52514e")); c.drawRightString(W - M, 8 * mm, f"Page {d.page}"); c.restoreState()
SimpleDocTemplate(sys.argv[2], pagesize=A4, leftMargin=M, rightMargin=M, topMargin=13 * mm, bottomMargin=14 * mm, title=sys.argv[2].split("/")[-1][:-4]).build(E, onFirstPage=foot, onLaterPages=foot); print("written", sys.argv[2])
