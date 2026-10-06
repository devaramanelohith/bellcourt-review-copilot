"""Flowchart of the agentic RAG loop as it is actually coded (copilot/pipeline.py + copilot/agent.py), in three lanes:
code (deterministic), model (Gemini 2.5 Flash), person. Writes docs/agentic_rag_flow.png and .pdf.   python scripts/build_flowchart.py"""
import os
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pypdfium2 as pdfium
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); DOCS = os.path.join(ROOT, "docs"); FONTS = os.path.join(DOCS, "fonts")
for n, f in (("I", "Inter-400.ttf"), ("IS", "Inter-600.ttf"), ("IB", "Inter-700.ttf")):
    pdfmetrics.registerFont(TTFont(n, os.path.join(FONTS, f)))
pdfmetrics.registerFontFamily("I", normal="I", bold="IB", italic="I", boldItalic="IB")
INK = colors.HexColor("#10232B"); MUTED = colors.HexColor("#5B6B76"); HAIR = colors.HexColor("#D5DBE0"); TEAL = colors.HexColor("#0F766E")
CODE = colors.HexColor("#E6F4F1"); MODEL = colors.HexColor("#E8F0FB"); HUMAN = colors.HexColor("#EAF6EC"); INPUT = colors.HexColor("#F3F4F6"); LOOP = colors.HexColor("#B4532A")
W, H = 1000, 1150; LX = {0: 40, 1: 365, 2: 690}; BW = 270
c = canvas.Canvas(os.path.join(DOCS, "agentic_rag_flow.pdf"), pagesize=(W, H))
c.setFillColor(colors.white); c.rect(0, 0, W, H, stroke=0, fill=1)
c.setFont("IB", 15); c.setFillColor(INK); c.drawString(40, H - 38, "Review Copilot: the agentic RAG loop, as coded")
c.setFont("I", 9.5); c.setFillColor(MUTED); c.drawString(40, H - 54, "copilot/pipeline.py run_case()  →  copilot/agent.py review()  →  copilot/core.py verify().  Three model calls on a typical case, up to six with corrections. About 6.5 s and a third of a cent.")
# lanes
for i, (t, col, sub) in enumerate([("CODE  ·  deterministic, unit-tested", CODE, "Python standard library. No model. Same answer every time."), ("MODEL  ·  Gemini 2.5 Flash, temperature 0, JSON mode", MODEL, "Bounded: can only read what code allows. Every answer verified."), ("PERSON", HUMAN, "Nurse, physician, intake. The only place a decision is made.")]):
    x = LX[i]; c.setFillColor(col); c.setStrokeColor(HAIR); c.roundRect(x - 10, 70, BW + 20, H - 150, 10, stroke=1, fill=1)
    c.setFont("IS", 9); c.setFillColor(INK); c.drawString(x, H - 96, t); c.setFont("I", 7.6); c.setFillColor(MUTED); c.drawString(x, H - 108, sub)
def para(t, x, y, w, s=8.3, col=INK):
    p = Paragraph(t, ParagraphStyle("p", fontName="I", fontSize=s, leading=s * 1.3, textColor=col)); _, h = p.wrap(w, 1000); p.drawOn(c, x, y - h); return h
STEPS = [  # (lane, title, body, height)
    (0, "0  Request arrives", "Fax image or PDF (46% of volume), portal form, phone keyed by intake, or a case file. Receipt time stamped: the clock starts here, on any channel.", 56),
    (1, "1  Transcribe (fax and text only)", "Vision call reads the form into 13 fields and returns empty strings for blanks. Sentences that address the reviewer are copied into embedded_instructions. Cached by image hash.", 56),
    (0, "2  Intake check, de-identify, scan", "Required fields, service matched to the service list, dates parsed. Name, DOB, MRN and phone removed. Regex scan for planted instructions.", 56),
    (0, "3  Member, clock, state", "Eligibility on the date of service from the nightly extract. 168 h MA, 360 h others, 72 h urgent; conflict between header and form flagged. AZ, TX, GA rules.", 50),
    (0, "4  Rule resolver", "Registry of 38 documents (type, client, version, effective dates, rank). Picks the governing set for client, service and date; lists retired versions and memos as excluded, with the reason.", 58),
    (1, "5  Plan the reads", "Given case facts, the governing list and each document's table of contents, the model asks for specific sections and up to two search queries, with a one-sentence reason.", 56),
    (0, "6  Read tool, safety net, search", "read_sections refuses any document not in the governing set. Mandatory reads are added whatever the model asked (exclusions, limits, amendments, criteria). Hybrid search: keyword + 256-dim cosine, rank-fused, labelled governing or not.", 80),
    (1, "7  Review", "Using only the section texts: coverage checks, each criterion MET, NOT_MET or NOT_DOCUMENTED with an exact quote from the record, outcome, rationale, letter paragraph, flags. Four outcomes; no deny.", 64),
    (0, "8  Verifier (V1 to V7)", "Outcome allowed; every citation in the governing set; every quote present in the record and not from planted text; outcome consistent with statuses; visit arithmetic; letter cites its source. Rejections go back to the model with reasons, at most twice.", 70),
    (1, "9  Second check (approvals only)", "An independent skeptical pass over a draft approval: reports only a contradiction in the record or a missed plan exclusion. If it finds one, the model re-evaluates and the verifier runs again.", 62),
    (0, "10  Overrides and drafts", "Not eligible on the date → not covered. Missing intake items or unverified member → an approval becomes need-information. State flags attached. Information-request fax drafted. Trace, tokens and latency stored.", 62),
    (2, "11  Decision", "Nurse approves, pends or routes. Physician decides every adverse case; Arizona MA needs an AZ-licensed director. A decision that differs from the recommendation needs a reason.", 56),
    (0, "12  Letter, audit, status", "Letter generated from the human decision: reason, provision, appeal rights, disclosures. PDF and email. Audit entry. Provider portal and status desk read the status, never the review.", 66)]
y = H - 122; pos = []
for lane, title, body, h in STEPS:
    x = LX[lane]; c.setFillColor(colors.white); c.setStrokeColor(HAIR); c.roundRect(x, y - h, BW, h, 6, stroke=1, fill=1)
    c.setFont("IS", 9); c.setFillColor(INK); c.drawString(x + 8, y - 13, title); para(body, x + 8, y - 18, BW - 16)
    pos.append((x + BW / 2, y, y - h)); y -= h + 16
def arrow(x1, y1, x2, y2):
    c.setStrokeColor(MUTED); c.setLineWidth(1)
    if abs(x1 - x2) < 1: c.line(x1, y1, x2, y2 + 4)
    else:
        ym = (y1 + y2) / 2; p = c.beginPath(); p.moveTo(x1, y1); p.lineTo(x1, ym); p.lineTo(x2, ym); p.lineTo(x2, y2 + 4); c.drawPath(p, stroke=1, fill=0)
    c.setFillColor(MUTED); p = c.beginPath(); p.moveTo(x2, y2); p.lineTo(x2 - 3.5, y2 + 6); p.lineTo(x2 + 3.5, y2 + 6); p.close(); c.drawPath(p, stroke=0, fill=1)
for i in range(len(pos) - 1): arrow(pos[i][0], pos[i][2], pos[i + 1][0], pos[i + 1][1])
# loops: verifier -> review, second check -> review
def loop(i_from, i_to, label, dx):
    x1, _, yb = pos[i_from]; x2, yt, _ = pos[i_to]; xr = LX[1] + BW + dx
    c.setStrokeColor(LOOP); c.setLineWidth(1); c.setDash(3, 2)
    p = c.beginPath(); p.moveTo(LX[0] + BW if i_from in (8,) else x1, pos[i_from][1] - 12);
    sx = LX[0] + BW if STEPS[i_from][0] == 0 else LX[1] + BW
    p = c.beginPath(); p.moveTo(sx, pos[i_from][1] - 14); p.lineTo(xr, pos[i_from][1] - 14); p.lineTo(xr, pos[i_to][1] - 14); p.lineTo(LX[1] + BW + 4, pos[i_to][1] - 14); c.drawPath(p, stroke=1, fill=0); c.setDash()
    c.setFillColor(LOOP); q = c.beginPath(); q.moveTo(LX[1] + BW, pos[i_to][1] - 14); q.lineTo(LX[1] + BW + 6, pos[i_to][1] - 10.5); q.lineTo(LX[1] + BW + 6, pos[i_to][1] - 17.5); q.close(); c.drawPath(q, stroke=0, fill=1)
    c.setFont("I", 7.4); c.setFillColor(LOOP); c.saveState(); c.translate(xr + 9, (pos[i_from][1] + pos[i_to][1]) / 2 - 14); c.rotate(90); c.drawCentredString(0, 0, label); c.restoreState()
loop(8, 7, "verifier rejected: fix, max 2", 14)
loop(9, 7, "second check found a problem: re-evaluate", 30)
c.setFont("I", 7.8); c.setFillColor(MUTED); c.drawString(40, 52, "Lanes show who owns each step. Solid arrows: the normal path. Dashed: correction loops. Nothing in the model lane can reach a document outside the governing set, and nothing outside the person lane can decide.")
c.save()
pg = pdfium.PdfDocument(os.path.join(DOCS, "agentic_rag_flow.pdf"))[0]; pg.render(scale=2.2).to_pil().save(os.path.join(DOCS, "agentic_rag_flow.png"))
print("flowchart written: docs/agentic_rag_flow.png")
