"""Builds the presentation deck docs/Presentation_Deck.pdf (16:9, 10 slides) for the evaluator's 8-minute flow.
Editorial style: small uppercase kicker, serif headline, serif display numbers, light cards, dark opening and closing slides.
Fonts: Inter (interface text) and Source Serif 4 (headlines, numbers) from docs/fonts; falls back to Arial and Georgia.   python scripts/build_deck.py"""
import os, json, glob
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.utils import ImageReader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); DOCS = os.path.join(ROOT, "docs"); SHOTS = os.path.join(DOCS, "shots"); FONTS = os.path.join(DOCS, "fonts")
E = json.load(open(os.path.join(ROOT, "data/results/eval.json"))); S = E["summary"]; SC = json.load(open(os.path.join(ROOT, "data/results/open_score.json")))
OUT = os.path.join(DOCS, "Presentation_Deck.pdf"); LOGO = os.path.join(DOCS, "logo.png")

# ---------------------------------------------------------------- fonts
def reg(name, candidates):
    for c in candidates:
        for p in (os.path.join(FONTS, c), "/System/Library/Fonts/Supplemental/" + c, "/Library/Fonts/" + c):
            if os.path.exists(p):
                try: pdfmetrics.registerFont(TTFont(name, p)); return True
                except Exception: pass
    return False
ok_sans = reg("I", ["Inter-400.ttf", "Arial.ttf"]) and reg("IM", ["Inter-500.ttf", "Inter-400.ttf", "Arial.ttf"]) and reg("IS", ["Inter-600.ttf", "Arial Bold.ttf"]) and reg("IB", ["Inter-700.ttf", "Arial Bold.ttf"])
ok_serif = reg("SS", ["SourceSerif4-400.ttf", "Georgia.ttf"]) and reg("SSB", ["SourceSerif4-600.ttf", "Georgia Bold.ttf"]) and reg("SSX", ["SourceSerif4-700.ttf", "SourceSerif4-600.ttf", "Georgia Bold.ttf"]) and reg("SSI", ["SourceSerif4-400i.ttf", "Georgia Italic.ttf"])
if not ok_sans:
    for n in ("I", "IM", "IS", "IB"): pdfmetrics.registerFont(TTFont(n, "/System/Library/Fonts/Supplemental/Arial.ttf"))
if not ok_serif:
    for n in ("SS", "SSB", "SSX", "SSI"): pdfmetrics.registerFont(TTFont(n, "/System/Library/Fonts/Supplemental/Georgia.ttf"))
pdfmetrics.registerFontFamily("I", normal="I", bold="IB", italic="I", boldItalic="IB"); pdfmetrics.registerFontFamily("SS", normal="SS", bold="SSB", italic="SSI", boldItalic="SSB")

# ---------------------------------------------------------------- palette (warm paper, deep teal ink, copper for the bad numbers)
PAPER = colors.HexColor("#F7F5F0"); INK = colors.HexColor("#10232B"); TEAL = colors.HexColor("#0F766E"); TEAL2 = colors.HexColor("#2DD4BF"); COPPER = colors.HexColor("#B4532A")
GREEN = colors.HexColor("#15803D"); MUTED = colors.HexColor("#5B6B76"); HAIR = colors.HexColor("#DED9CF"); CARD = colors.white; DARK = colors.HexColor("#0A1F2B"); DARK2 = colors.HexColor("#123241")
CREAM = colors.HexColor("#F3EFE6"); DMUTED = colors.HexColor("#9FB3BC"); AMBER = colors.HexColor("#B45309"); TINT = colors.HexColor("#E6F4F1"); VIOLET = colors.HexColor("#6D28D9")
W, H = 960, 540; M = 54; CW = W - 2 * M
c = canvas.Canvas(OUT, pagesize=(W, H)); c.setTitle("Bellcourt Review Copilot: presentation"); c.setAuthor("Lohith Devaramane")
n = [0]

def wrap(t, f, s, w):
    out, cur = [], ""
    for x in t.split():
        y = (cur + " " + x).strip()
        if stringWidth(y, f, s) <= w: cur = y
        else: out.append(cur); cur = x
    return out + [cur]
def text(x, y, t, f="I", s=11, col=INK, align="left"):
    c.setFont(f, s); c.setFillColor(col)
    (c.drawString if align == "left" else c.drawRightString if align == "right" else c.drawCentredString)(x, y, t)
def para(t, x, y, w, s=11.5, col=INK, f="I", lead=None, align=0):
    p = Paragraph(t, ParagraphStyle("p", fontName=f, fontSize=s, leading=lead or s * 1.4, textColor=col, alignment=align)); _, h = p.wrap(w, 2000); p.drawOn(c, x, y - h); return y - h
def slide(kicker, title, dark=False, source="", tsize=27, tw=None):
    if n[0]: c.showPage()
    n[0] += 1
    c.setFillColor(DARK if dark else PAPER); c.rect(0, 0, W, H, stroke=0, fill=1)
    if dark: c.setFillColor(DARK2); c.circle(W + 60, -40, 300, stroke=0, fill=1)
    text(M, H - 44, kicker.upper(), "IS", 8.5, TEAL2 if dark else TEAL)
    c.setFont("IS", 8.5)
    y = H - 72 - max(0, tsize - 27) * 0.9
    for line in wrap(title, "SSB", tsize, tw or CW): text(M, y, line, "SSB", tsize, CREAM if dark else INK); y -= tsize * 1.15
    c.drawImage(LOGO, M, 15.5, 11, 11, mask="auto")
    text(M + 16, 20, source or "Bellcourt Health Administrators  ·  FDE Academy case study  ·  Lohith Devaramane  ·  synthetic data", "I", 7.5, DMUTED if dark else MUTED)
    text(W - M, 20, str(n[0]), "I", 7.5, DMUTED if dark else MUTED, "right")
    return y - 10
def card(x, y, w, h, fill=CARD, stroke=HAIR, r=8):
    c.setFillColor(fill); c.setStrokeColor(stroke); c.setLineWidth(0.8); c.roundRect(x, y, w, h, r, stroke=1, fill=1)
def bignum(x, y, num, label, sub="", col=INK, size=40, w=200, lab_col=None):
    text(x, y, num, "SSB", size, col); yy = para(label, x, y - 8, w, 10.5, lab_col or INK, "IM")
    if sub: para(sub, x, yy - 1, w, 9, MUTED)
def image(path, x, y, w, border=True, h_max=None):
    img = ImageReader(path); iw, ih = img.getSize(); h = w * ih / iw
    if h_max and h > h_max: h = h_max; w = h * iw / ih
    c.drawImage(img, x, y - h, w, h, mask="auto")
    if border: c.setStrokeColor(HAIR); c.setLineWidth(0.8); c.rect(x, y - h, w, h, stroke=1, fill=0)
    return y - h, w
def tbl(rows, x, y, widths, s=9.6, head=True, lead=1.3, pad=4, dark=False):
    st = lambda i: ParagraphStyle("t", fontName="IS" if (i == 0 and head) else "I", fontSize=s, leading=s * lead, textColor=(TEAL2 if dark else MUTED) if (i == 0 and head) else (CREAM if dark else INK))
    t = Table([[Paragraph(str(v), st(i)) for v in r] for i, r in enumerate(rows)], colWidths=widths)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#2E4A57") if dark else HAIR), ("TOPPADDING", (0, 0), (-1, -1), pad), ("BOTTOMPADDING", (0, 0), (-1, -1), pad), ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 6)]
    if head: style.append(("LINEBELOW", (0, 0), (-1, 0), 1, TEAL))
    t.setStyle(TableStyle(style)); _, h = t.wrap(sum(widths), 2000); t.drawOn(c, x, y - h); return y - h
def bullets(items, x, y, w, s=11, gap=7, col=INK, dot=TEAL, f="I"):
    for t in items:
        c.setFillColor(dot); c.circle(x + 3, y - s * 0.6, 2.2, stroke=0, fill=1); y = para(t, x + 14, y, w - 14, s, col, f) - gap
    return y
def hbar(x, y, w, label, val, maxv, col, lw=150, s=10):
    text(x, y, label, "I", s, INK); bw = (w - lw - 34) * val / maxv
    c.setFillColor(col); c.roundRect(x + lw, y - 3, bw, 11, 2, stroke=0, fill=1); text(x + lw + bw + 6, y, str(val), "IS", s, INK)

pct = lambda a, b: f"{100 * a / b:.1f}%"
LIVE = "bellcourt-review-copilot.vercel.app"; REPO = "github.com/devaramanelohith/bellcourt-review-copilot"

# ================================================================ 1. title (dark)
slide("FDE Academy  ·  case study presentation  ·  Bellcourt Health Administrators", "Prior authorization under pressure", dark=True, tsize=38, source=f"Live demo: {LIVE}   ·   Code: {REPO}")
c.drawImage(LOGO, W - M - 64, H - 118, 64, 64, mask="auto"); text(W - M - 76, H - 78, "Review Copilot", "IB", 15, CREAM, "right"); text(W - M - 76, H - 94, "for Bellcourt Health Administrators", "IM", 9, DMUTED, "right")
para("A review copilot that <b>picks the governing rule in code</b>, checks every criterion against the clinical record with a quoted citation, and leaves <b>every decision to a person</b>.", M, H - 150, 560, 15, CREAM, "SS", 22)
card(M, 110, 400, 150, DARK2, colors.HexColor("#2E4A57"))
text(M + 18, 236, "SUBMISSION", "IS", 8, TEAL2)
tbl([["Presented by", "Lohith Devaramane"], ["Programme", "FDE Academy, IIT Roorkee cohort"], ["Evaluator", "Sumit Shukla, FDE Academy"], ["Date", "7 October 2026"], ["Format", "8 minutes, then questions"]], M + 14, 226, [95, 275], 9.6, head=False, pad=3, dark=True)
card(M + 420, 110, 432, 150, DARK2, colors.HexColor("#2E4A57"))
text(M + 438, 236, "WHAT IS IN THE BOX", "IS", 8, TEAL2)
bullets(["Working app: provider portal, intake and reviewer workspace, physician decisions, status desk, decision letters by PDF and email",
         "Evaluation against Bellcourt's own 120 audited cases, 30 live cases and 24 hostile inputs", "Documentation, architecture, design note, evidence pack and this deck"], M + 438, 222, 400, 10.2, 5, CREAM, TEAL2)

# ================================================================ 2. the problem
y = slide("1 · The problem", "Riverbend is penalising Bellcourt for decisions that are late and wrong. Leadership says it is a staffing problem.", source="Sources: pa_requests_2025_2026, qa_audit_sample_2026, financials, Riverbend addendum, interviews")
cols = [("90.1%", "Medicare Advantage decisions on time", "Contract standard 97%. Corrective Action Plan open since July 2026.", COPPER),
        ("56.7%", "Decisions correct in Bellcourt's own QA audit", "68 of 120 cases. Contract standard 95%.", COPPER),
        ("56.2%", "Riverbend denials overturned on appeal", "Root-cause review is triggered at 30%. Wrong-version denials are overturned 91% of the time.", COPPER),
        ("$1.9M", "Service credits paid to Riverbend this year", "About a fifth of operating profit. Zero before 2026.", INK)]
cw = (CW - 3 * 14) / 4
for i, (a, b, s_, col) in enumerate(cols): bignum(M + i * (cw + 14), y - 36, a, b, s_, col, 38, cw - 6)
y2 = y - 150
card(M, 70, 270, y2 - 70); card(M + 284, 70, 270, y2 - 70); card(M + 568, 70, CW - 568, y2 - 70)
text(M + 14, y2 - 20, "WHO BELLCOURT IS", "IS", 8, TEAL)
para("A third-party administrator in Nashville. It runs self-funded health plans for <b>38 employers</b> (453,000 people) and, since 2023, decides prior authorization requests for <b>Riverbend Health Plan</b> (153,700 members). About <b>310,000 requests a year</b>, 46% arriving by fax.", M + 14, y2 - 30, 242, 10, INK)
text(M + 298, y2 - 20, "WHAT IS AT STAKE", "IS", 8, TEAL)
para("Riverbend's contract ends <b>31 December 2026</b> and may go out to bid this month. Harlan, the largest employer (about $8.1M a year), renews on 1 January with satisfaction at 5 of 10. Operating margin has fallen from <b>14% to 8%</b> in three years.", M + 298, y2 - 30, 242, 10, INK)
text(M + 582, y2 - 20, "THE CLAIM I HAD TO TEST", "IS", 8, TEAL)
para("<i>\"It's a staffing problem, full stop.\"</i> The VP of Operations wants 20 more nurses, about $2.2M a year. The CEO is not convinced and wants decisions that are <i>\"faster and more defensible, not just faster\"</i>.", M + 582, y2 - 30, CW - 596, 10, INK, "SS", 13.5)

# ================================================================ 3. how I found it
y = slide("2 · How I found it", "I tested the staffing claim against the data pack, not the interviews.", source="Analysis script: FDE_Briefing/evidence_analysis.py. 2,400 requests, 120 audited cases, 90 weeks of staffing, 3,200 calls, 38 documents")
text(M, y - 14, "METHOD", "IS", 8, TEAL)
yy = bullets(["<b>Reconcile every claim to a file.</b> Staffing to <i>nurse_staffing_weekly</i>, timeliness to <i>pa_requests</i>, accuracy to the <i>QA audit</i>, calls to the <i>call log</i>.",
              "<b>Cut timeliness by completeness at receipt</b>, not by nurse hours. That one cut explained every missed Medicare deadline.",
              "<b>Classify the 52 QA errors by the auditor's own error type</b>, then ask which are clinical judgement and which are rule lookup.",
              "<b>Rebuild the clock from receipt time</b>, as the Riverbend addendum defines it, instead of PACE's keying time.",
              "<b>Confirm with the people who live it.</b> The senior nurse: <i>\"The hard part is figuring out which rules apply.\"</i>"], M, y - 26, 400, 10.4, 6)
card(M + 430, 92, CW - 430, y - 100)
text(M + 446, y - 24, "THE 52 AUDITED ERRORS, BY THE AUDITOR'S OWN LABEL", "IS", 8, TEAL)
by = y - 48
for lab, v, col in [("Memo overrode policy", 18, COPPER), ("Outdated policy version", 14, COPPER), ("Criteria misread", 10, INK), ("Client plan rule missed", 7, COPPER), ("Missing info not requested", 3, INK)]:
    hbar(M + 446, by, CW - 462, lab, v, 18, col, 150, 9.6); by -= 22
para("<font color='#B4532A'><b>39 of 52</b></font> errors are about <b>which rule</b> was applied, not clinical judgement. UM-MEMO-2025-19 kept a 6-week lumbar MRI rule after MP-101 v2 moved to 4 weeks: 72 wrongful denials.", M + 446, by - 2, CW - 462, 9.4, INK)
yb = 92 + 60
c.setStrokeColor(HAIR); c.line(M + 446, yb + 6, W - M - 16, yb + 6)
for i, (a, b) in enumerate([("64 of 64", "missed MA standard deadlines were incomplete on receipt"), ("99.8%", "of complete requests decided on time"), ("r = -0.05", "nurse count vs on-time rate, 90 weeks")]):
    xx = M + 446 + i * 148; text(xx, yb - 16, a, "SSB", 17, GREEN if i == 1 else INK); para(b, xx, yb - 24, 140, 8.2, MUTED)

# ================================================================ 4. diagnosis
y = slide("2 · What the data says", "Two root causes, one thread: nobody can say which rule applies, and the clock starts late.", source="Staffing is not the main driver: headcount fell 57.7 to 50.6 FTE while on-time stayed flat. Requests that arrived complete are overturned more often than incomplete ones, so appeals are not 'new information'.")
card(M, 96, 412, y - 104); card(M + 428, 96, CW - 428, y - 104)
text(M + 16, y - 26, "ROOT CAUSE 1 · THE WRONG RULEBOOK", "IS", 8, COPPER)
bullets(["<b>34% of 2026 denials</b> cite a policy version that was already retired. Appeals against them succeed <b>91%</b> of the time.",
         "A memo overrode a policy for a year. Governance (GOV-01) says memos cannot change criteria; PACE screens still show the old rule.",
         "Kestrel started covering bariatric surgery in January. Nobody told the reviewers: <b>8 wrongful \"not covered\" denials</b>.",
         "<b>20 glucose-monitor denials</b> for Medicare members under the stricter Bellcourt rule, when the addendum says Medicare criteria apply. All 11 appeals overturned.",
         "<b>14.2 of 38 minutes</b> per case go on finding the rule. That is 18.9 of 50.6 nurses, almost the 20 the VP wants to hire."], M + 16, y - 40, 384, 10.2, 6)
text(M + 444, y - 26, "ROOT CAUSE 2 · THE LATE CLOCK", "IS", 8, COPPER)
bullets(["Riverbend's clock starts when the fax <b>arrives</b>. PACE starts it when someone <b>types it in</b>, about 17 hours later.",
         "A third of faxes are missing something, and nobody tells the provider until a person has opened the image.",
         "In late cases, <b>122 of 199 hours</b> were spent waiting for missing information. Nurse review took about 40 hours whether the case was late or not.",
         "Every one of the <b>64 missed Medicare deadlines</b> started with an incomplete request; across all clients, 66 of 69 late decisions did.",
         "PACE dashboards therefore flatter Bellcourt: the Analytics team had to recompute turnaround from receipt time by hand."], M + 444, y - 40, CW - 460, 10.2, 6)
card(M, 56, CW, 30, TINT, TINT)
para("<b>So what:</b> fix the rule and the clock. Code can pick the governing document by client, service and date of service; code can stamp receipt and list what is missing in the first minute. Hiring nurses addresses neither.", M + 14, 79, CW - 28, 10.2, INK)

# ================================================================ 5. demo
y = slide("3 · Live demo", "One request, from the provider's desk to the written decision.", source="Demo runs live at " + LIVE + ". Demo clock pinned to 26 September 2026 so deadlines are reproducible.")
yl, w1 = image(os.path.join(SHOTS, "coverage.jpg"), M, y - 6, 268)
yl2, _ = image(os.path.join(SHOTS, "case_8100.jpg"), M + 282, y - 6, 268)
yl3, _ = image(os.path.join(SHOTS, "letters.jpg"), M + 564, y - 6, 268)
for xx, t in [(M, "Provider portal: coverage check before filing, then submit"), (M + 282, "Nurse workspace: governing rule, criteria with quotes, decision"), (M + 564, "Decision letter from the human decision, PDF and email")]: para(t, xx, yl - 4, 268, 8.6, MUTED)
steps = [("1", "Provider", "Coverage check for Harlan bariatric surgery: <b>not covered</b>, SPD-HARLAN §6.4, before anything is filed."),
         ("2", "Provider", "Submit the Juniper spinal-stimulator request. Receipt, request number and the clock at once; plan pre-check flags the second-opinion rule."),
         ("3", "Intake", "Queue sorted by hours left. Open the new request, <b>run the review</b>: Need information, citing SPD-JUNIPER §5.6. Pend it; the notice is created."),
         ("4", "Nurse", "Case 8100, lumbar MRI: the memo and PACE say 6 weeks; the copilot picked MP-101 v2 by date of service and lists v1 and the memo as excluded. Approve."),
         ("5", "Physician", "Case 8105 routed for Arizona sign-off. Deny with the stated reason; the letter carries criteria, citation and appeal rights.")]
ys = yl - 24
for num_, who, what in steps:
    c.setFillColor(TEAL); c.circle(M + 7, ys - 3, 7, stroke=0, fill=1); text(M + 7, ys - 6, num_, "IB", 8, colors.white, "center")
    text(M + 22, ys - 6, who, "IS", 9.4, TEAL); para(what, M + 92, ys + 4, CW - 92, 9.4, INK); ys -= 20
card(M, 48, CW, 34, TINT, TINT)
para("<b>Budget: 3 minutes 30 seconds.</b> Steps 1 to 4 are the story; step 5 is optional. If the clock shows 7:00 and the demo is still running, stop and go to evaluation, the slide the evaluator asked for by name.", M + 14, 74, CW - 28, 9.6, INK)

# ================================================================ 6. key elements (technical)
y = slide("4 · Key elements of the build", "Six elements. Code picks the rule, the model checks the evidence, a person decides.", source="Python standard library on Vercel · Gemini 2.5 Flash via OpenRouter (temperature 0, JSON mode) · 256-dim embeddings fused with keyword search · Supabase Postgres · 36 unit tests, no model call")
# pipeline drawing
bx = M; by = y - 112; bw = (CW - 5 * 10) / 6; bh = 92
boxes = [("1  Intake", "Fax image or PDF read by a vision model into fields. Form and file upload. Completeness check and receipt stamp in code.", CARD, "code + vision"),
         ("2  Member and clock", "Eligibility on the date of service. Clock from receipt: 168 h MA, 360 h others, 72 h urgent. State rules AZ, TX, GA.", CARD, "code"),
         ("3  Rule resolver", "Registry of 38 documents with type, client, version, effective dates, authority rank. Picks what governs on the date; excludes the rest with a reason.", TINT, "code"),
         ("4  Bounded agent", "Plans its reads, calls a read tool that refuses non-governing documents, searches a filtered index, tests each criterion with an exact quote.", colors.HexColor("#EAF2FB"), "model"),
         ("5  Verifier", "Citations in force, quotes present in the record, outcome consistent, visit arithmetic recomputed. Second skeptical pass on approvals.", TINT, "code"),
         ("6  Human decision", "Four outcomes, no deny. Nurse approves or pends, physician decides adverse cases, letter generated from the decision.", colors.HexColor("#EAF6EC"), "person")]
for i, (t, d, fill, who) in enumerate(boxes):
    x = bx + i * (bw + 10); card(x, by, bw, bh, fill)
    text(x + 8, by + bh - 14, t, "IS", 9, INK); text(x + bw - 8, by + bh - 14, who, "I", 7, MUTED, "right"); para(d, x + 8, by + bh - 20, bw - 16, 7.6, INK, lead=9.6)
    if i < 5: c.setFillColor(MUTED); c.setStrokeColor(MUTED); c.line(x + bw + 1, by + bh / 2, x + bw + 9, by + bh / 2); c.circle(x + bw + 9, by + bh / 2, 1.6, stroke=0, fill=1)
yb = by - 16
bullets(["<b>Deterministic where it matters.</b> Which document governs is never a model judgement; it is a lookup over effective dates and rank, and it is unit-tested.",
         "<b>Agentic RAG, bounded.</b> The model decides what to read and how to weigh evidence, inside a document set it cannot widen. Retrieval is filtered by the governing set, so a retired version cannot surface.",
         "<b>Every output is checked by code</b> before a person sees it, and every run stores inputs, documents, trace, output and verifier report."], M, yb, 420, 10, 5)
bullets(["<b>Roles enforced on the server:</b> provider, intake, nurse, physician, member-services agent, auditor. Reviewers cannot raise cases; providers cannot see the review.",
         "<b>Portable:</b> one environment variable switches the model provider; the vector index and store sit behind one interface each.",
         "<b>Runs beside PACE</b>, read-only. Nothing is written back; PACE stays the system of record until its 2028 replacement."], M + 440, yb, CW - 440, 10, 5)

# ================================================================ 7. what I introduced
y = slide("5 · What the build introduces", "Something for each person in the picture, and nothing that takes a decision away from them.", source="All six roles are live in the demo. Passwords are held by the presenter; nothing is shown on screen.")
feats = [("Provider portal", "Coverage check before filing: eligibility, plan exclusions and conditions, the policy version that will apply, the documents to send. Submit by fax upload or form. Receipt and request number at once. Status and written notices, no phone call.", "provider_home.jpg"),
         ("Status desk", "For member-services agents. Request number and date of birth must both match before anything is disclosed. Status, due date and missing items only; never the clinical review. Every lookup audited.", "status_desk.jpg"),
         ("Priority queue", "Sorted by hours left on a clock that starts at receipt, on any channel. Overdue, urgent, due soon. Urgency conflicts between cover sheet and form are flagged and resolved to the stricter clock.", "queue.jpg"),
         ("Review copilot", "Governing documents with the reason each applies, and the ones deliberately not used. Each criterion met, not met or not documented with an exact quote. One click opens the source section.", "case_8100.jpg"),
         ("Human decision and letters", "Approve, pend, route, or physician-only deny. Overrides need a reason. The decision letter states the specific reason, the provision relied on and appeal rights; PDF download and email.", "letters.jpg"),
         ("Governance page and audit log", "Eleven live controls you can click to watch the server refuse, redact, flag or reject. Per-run trace: plan, reads, refusals, verifier, second check, tokens, latency.", "governance.jpg")]
cw3 = (CW - 2 * 14) / 3; ch = (y - 60) / 2 - 6
for i, (t, d, img) in enumerate(feats):
    col, row = i % 3, i // 3; x = M + col * (cw3 + 14); yy = y - row * (ch + 10)
    card(x, yy - ch, cw3, ch)
    yl, iw = image(os.path.join(SHOTS, img), x + 10, yy - 12, cw3 - 20, h_max=ch * 0.42)
    text(x + 10, yl - 16, t, "IS", 10.5, INK); para(d, x + 10, yl - 22, cw3 - 20, 8, INK, lead=10)

# ================================================================ 8. governance and security
y = slide("6 · Governance and security", "Every constraint is enforced in code, and the app lets you watch it happen.", source="Riverbend addendum §3, §4, §5 · GOV-01 · REG-02 (AZ, TX, GA) · SPD §5.5. Production: Azure tenant under the existing HIPAA BAA, Entra ID single sign-on, 60-day notice before go-live.")
rows = [["Constraint", "How it is enforced", "Proof on the Governance page"],
        ["No automated denial, delay or modification (addendum §5)", "The outcome schema has no deny value; the verifier rejects anything else. The tool drafts; it never sends.", "Submit DENY: verifier rejection V1"],
        ["Only physicians deny; Arizona MA needs an AZ-licensed director (§4)", "Decision permissions by role on the server; state flag AZ_MD_SIGNOFF_REQUIRED routes the case and marks the letter.", "Dry-run deny as a nurse: 403"],
        ["Hierarchy of authority (GOV-01); memos never change criteria", "Rule resolver by rank and effective date; read tool refuses non-governing documents; memos excluded with a reason.", "Read MP-101 v1 for a 2026 date: REFUSED"],
        ["Segregation of duties", "Intake and providers raise requests; nurses and physicians decide; auditors read. Enforced on every request, not only in the interface.", "Role matrix and live attempt"],
        ["PHI minimisation", "Name, date of birth, record number and phone stripped before the review model; only age passed. Fax images served only to signed-in users.", "Before and after on a sample note"],
        ["Untrusted provider content", "Text that tries to direct the reviewer is flagged, shown to the human, and barred as evidence by the verifier.", "Planted 'pre-approved' sentence flagged"],
        ["Authentication and sessions", "Salted PBKDF2 hashes, 200,000 rounds; HMAC-signed 8-hour sessions; constant-time checks.", "Tampered and forged tokens rejected"],
        ["Audit on request (addendum §5)", "Every action with user, role and time; each review stores inputs, governing set, trace, output and verifier report.", "Audit log and per-run trace"]]
tbl(rows, M, y - 2, [168, 300, 132], 8.4, pad=3)
yl, _ = image(os.path.join(SHOTS, "governance.jpg"), M + 616, y - 6, CW - 616)
para("The Governance and security page. Each row above is a button; the server answers live.", M + 616, yl - 6, CW - 616, 8.2, MUTED)
yl2, _ = image(os.path.join(SHOTS, "governance_deid.jpg"), M + 616, yl - 30, CW - 616)

# ================================================================ 9. evaluation
y = slide("7 · How I evaluated it", "Tested against the auditor's answers, hostile inputs and time travel, with every run traced.", source="scripts/run_eval.py and scripts/run_open.py; raw results in data/results. Evidence pack: docs/Evidence_It_Works.pdf")
nums = [(f"{S['tool_correct']}/{S['n']}", "agree with the QA auditor", f"Human reviewers on the same cases: {S['human_correct']}/{S['n']}", GREEN),
        (f"{S['source_correct']}/{S['n']}", "governing document and version correct", "Document ID and version exact, section by prefix", INK),
        (str(len(S["wrong_approvals"])), "wrongful approvals", "No denial is possible by design", INK),
        (f"{S['adversarial_passed']}/{S['adversarial_total']}", "adversarial, incomplete and wrong-input tests", "10 planted instructions all ignored; 7 time-travel cases right", INK),
        (f"{SC['matched']}/{SC['total']}", "open queue against my answer key", "13 image-only faxes read, not guessed", INK)]
cw5 = (CW - 4 * 12) / 5
for i, (a, b, s_, col) in enumerate(nums): bignum(M + i * (cw5 + 12), y - 34, a, b, s_, col, 32, cw5 - 6)
yb = y - 140
card(M, 70, 400, yb - 70); card(M + 416, 70, CW - 416, yb - 70)
text(M + 14, yb - 18, "WHERE THE HUMANS WENT WRONG, THE COPILOT WAS RIGHT", "IS", 8, TEAL)
by = yb - 40
for k, lab in [("MEMO_CONFLICT", "Memo overrode policy"), ("OUTDATED_POLICY_VERSION", "Outdated policy version"), ("CRITERIA_MISREAD", "Criteria misread"), ("CLIENT_RULE_MISSED", "Client rule missed"), ("MISSING_INFO_NOT_REQUESTED", "Missing info not requested"), ("NONE", "No human error")]:
    a, b = S["by_error_type"][k]; text(M + 14, by, lab, "I", 9.4, INK); bw = 150 * b / 68
    c.setFillColor(HAIR); c.roundRect(M + 190, by - 3, bw, 10, 2, stroke=0, fill=1); c.setFillColor(GREEN); c.roundRect(M + 190, by - 3, 150 * a / 68, 10, 2, stroke=0, fill=1); text(M + 190 + bw + 6, by, f"{a} of {b}", "IS", 9.2, INK); by -= 19
text(M + 430, yb - 18, "WHAT EACH NUMBER MEASURES", "IS", 8, TEAL)
tbl([["Accuracy", "Outcome equals the auditor's qa_correct_decision on 120 cases"], ["Safety", "Wrongful approvals and tool denials, both zero"], ["Robustness", "Planted text, missing fields, wrong dates, retired versions"],
     ["Consistency", "Repeat runs: 27 to 29 of 30, every miss toward a person"], ["Observability", "Plan, reads, refusals, verifier, second check, tokens, latency per run"], ["Cost and speed", f"{S['avg_latency']}s and about a third of a cent per case"]], M + 430, yb - 26, [82, CW - 416 - 110], 8.3, head=False, pad=2.2)
miss = [q for q in E["qa"] if q["tool"] != q["truth"]]
text(M + 430, 122, "THE THREE MISSES, ALL TOWARD A PERSON", "IS", 8, TEAL)
para("<br/>".join(f"{q['id']} {q['client']} · {q['service'].split(' (')[0][:30]} · auditor {q['truth'].replace('_', ' ').lower()}, copilot {q['tool'].replace('_', ' ').lower()}" for q in miss), M + 430, 113, CW - 444, 7.6, INK, lead=9.4)
para("<b>Limits I state openly:</b> results vary slightly between runs; prompts were tuned while looking at these cases, so a fresh random audit sample is the next test; the open-case key is my own reading of the policies; 6 of 38 employer plan documents are in the pack.", M, 60, CW, 8.6, MUTED)

# ================================================================ 10. closing (dark)
y = slide("8 · What Bellcourt should do next", "Three decisions.", dark=True, tsize=34, source=f"Questions  ·  {LIVE}  ·  {REPO}")
cards = [("This week, no technology", ["Withdraw UM-MEMO-2025-19", "Tell UM Operations about the Kestrel amendment", "Re-review denials still open to appeal under the old versions", "Report Riverbend timeliness from receipt time"]),
         ("90 days, recommend-only, beside PACE", ["Send the 60-day notice to Riverbend on day 1", "Registry of documents owned by the Clinical Policy Committee", "Shadow mode with senior nurses, then self-funded clients, then Riverbend", "Provider portal and status desk to cut status calls"]),
         ("Measure it, from receipt", ["MA on-time from about 90% to 97% or better", "QA accuracy from 56.7% to 95% or better", "Wrong-version citations to zero; overturns below 30%", "Stop rule: pause if accuracy on sampled cases falls under 90%"])]
cw3 = (CW - 2 * 14) / 3
for i, (t, items) in enumerate(cards):
    x = M + i * (cw3 + 14); card(x, 170, cw3, y - 180, DARK2, colors.HexColor("#2E4A57"))
    text(x + 14, y - 30, t, "SSB", 14, CREAM); bullets(items, x + 14, y - 46, cw3 - 28, 10, 6, CREAM, TEAL2)
text(M, 118, "Fix the rule and the clock. Staffing follows.", "SSI", 22, CREAM)
text(M, 90, "Thank you. Questions?", "IM", 12, DMUTED); c.drawImage(LOGO, W - M - 44, 72, 44, 44, mask="auto")
c.save()
from pypdf import PdfReader
print(OUT, len(PdfReader(OUT).pages), "slides", "fonts:", "Inter" if ok_sans else "Arial", "/", "Source Serif 4" if ok_serif else "Georgia")
