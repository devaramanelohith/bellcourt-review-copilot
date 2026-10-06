"""Builds the submission PDFs in docs/ from the saved evaluation results.  python scripts/build_docs.py"""
import os, sys, json, math
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); DOCS = os.path.join(ROOT, "docs")
E = json.load(open(os.path.join(ROOT, "data/results/eval.json"))); S = E["summary"]; SC = json.load(open(os.path.join(ROOT, "data/results/open_score.json")))
pct = lambda a, b: f"{100*a/b:.1f}%"
try:
    A = "/System/Library/Fonts/Supplemental/"; pdfmetrics.registerFont(TTFont("B", A + "Arial.ttf")); pdfmetrics.registerFont(TTFont("BB", A + "Arial Bold.ttf"))
    pdfmetrics.registerFontFamily("B", normal="B", bold="BB", italic="B", boldItalic="BB"); F, FB = "B", "BB"
except Exception: F, FB = "Helvetica", "Helvetica-Bold"
NAVY = colors.HexColor("#104281"); SEC = colors.HexColor("#52514e"); HAIR = colors.HexColor("#e1e0d9"); HEAD = colors.HexColor("#eef0f2"); TINT = colors.HexColor("#f1f6fd"); INK = colors.HexColor("#0b0b0b")
W, H = A4; M = 15 * mm; CW = W - 2 * M
st = lambda n, **k: ParagraphStyle(n, **{**dict(fontName=F, fontSize=9.2, leading=12.4, textColor=INK), **k})
ST = dict(t=st("t", fontName=FB, fontSize=20, leading=24, textColor=NAVY), sub=st("s", fontSize=10.5, textColor=SEC, leading=14), h=st("h", fontName=FB, fontSize=12.5, leading=16, textColor=NAVY, spaceBefore=9, spaceAfter=2),
          b=st("b", spaceAfter=4), bu=st("bu", leftIndent=11, bulletIndent=1, spaceAfter=2), c=st("c", fontSize=7.9, leading=10), cb=st("cb", fontName=FB, fontSize=7.9, leading=10), cap=st("cap", fontSize=7.6, textColor=SEC, leading=10, spaceAfter=4))
P = lambda t, s="b": Paragraph(t, ST[s]); BL = lambda items: [Paragraph(t, ST["bu"], bulletText="•") for t in items]
def Hd(t): return [Paragraph(t, ST["h"]), HRFlowable(width="100%", thickness=0.8, color=NAVY, spaceAfter=4)]
def T(rows, widths):
    t = Table([[Paragraph(str(x), ST["cb" if i == 0 else "c"]) for x in r] for i, r in enumerate(rows)], colWidths=[w * mm for w in widths], repeatRows=1)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, 0), HEAD), ("LINEBELOW", (0, 0), (-1, -1), 0.4, HAIR),
                           ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6)])); return t
def CALL(t):
    x = Table([[Paragraph(t, ST["b"])]], colWidths=[CW]); x.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), TINT), ("LINEBEFORE", (0, 0), (0, -1), 2.5, colors.HexColor("#2a78d6")), ("LEFTPADDING", (0, 0), (-1, -1), 8)])); return x
def foot(title):
    def f(c, d):
        c.saveState(); c.setFont(F, 7.5); c.setFillColor(SEC); c.drawString(M, 8 * mm, title + "  |  Lohith Devaramane  |  fictional company, synthetic data"); c.drawRightString(d.pagesize[0] - M, 8 * mm, f"Page {d.page}"); c.restoreState()
    return f

# ---------------------------------------------------------------- architecture drawing
def wrap(t, f, s, w):
    out, cur = [], ""
    for x in t.split():
        y = (cur + " " + x).strip()
        if stringWidth(y, f, s) <= w: cur = y
        else: out.append(cur); cur = x
    return out + [cur]
def box(d, x, y, w, h, title, text, fill="#ffffff", stroke="#898781", ts=8, bs=7):
    d.add(Rect(x, y, w, h, rx=3, ry=3, fillColor=colors.HexColor(fill), strokeColor=colors.HexColor(stroke), strokeWidth=0.8)); ty = y + h - 11
    for l in wrap(title, FB, ts, w - 9): d.add(String(x + 4.5, ty, l, fontName=FB, fontSize=ts, fillColor=NAVY)); ty -= ts + 1.6
    ty -= 1
    for l in wrap(text, F, bs, w - 9): d.add(String(x + 4.5, ty, l, fontName=F, fontSize=bs, fillColor=INK)); ty -= bs + 1.8
def arrow(d, x1, y1, x2, y2, head=True):
    d.add(Line(x1, y1, x2, y2, strokeColor=SEC, strokeWidth=0.9))
    if head:
        a = math.atan2(y2 - y1, x2 - x1); s = 4.5
        d.add(Polygon([x2, y2, x2 - s * math.cos(a - .45), y2 - s * math.sin(a - .45), x2 - s * math.cos(a + .45), y2 - s * math.sin(a + .45)], fillColor=SEC, strokeColor=SEC))
def architecture(Wd, scale=1.0):
    Hd_ = 300; d = Drawing(Wd, Hd_); g = 9; sw = (Wd - 5 * g) / 6; X = [i * (sw + g) for i in range(6)]; C = [x + sw / 2 for x in X]
    lab = lambda x, y, t: d.add(String(x, y, t, fontName=FB, fontSize=7, fillColor=SEC))
    lab(0, Hd_ - 8, "BELLCOURT SYSTEMS (READ-ONLY). PACE STAYS THE SYSTEM OF RECORD."); iy = Hd_ - 66; ih = 50
    box(d, X[0], iy, sw, ih, "Fax share", "640 fax images a day, no OCR", "#f6f6f4")
    box(d, X[1], iy, sw, ih, "Portal webhook + PACE read replica", "Structured requests, case data", "#f6f6f4")
    box(d, X[2], iy, sw, ih, "Eligibility files", "Nightly file per client", "#f6f6f4")
    box(d, X[3], iy, 2 * sw + g, ih, "UM Library: policies, plan documents, addendum, memos", "Ingested into sections + a metadata registry (type, client, version, effective dates, authority rank) + a vector index", "#f6f6f4")
    box(d, X[5], iy, sw, ih, "PACE", "Human keys the final decision. The tool never writes here.", "#f6f6f4")
    sh = 104; sy = iy - 26 - sh; lab(C[4] + 2, sy + sh + 8, "REVIEW COPILOT")
    steps = [("1 Intake", "Read fax into fields. Completeness check. Draft fax-back for missing items. Flag planted text. Remove identifiers.", True),
             ("2 Member + clock", "Eligibility on the service date. Clock starts at receipt. State rules (AZ, TX, GA).", False),
             ("3 Rule resolver", "CODE picks the governing documents by client, service and date. Retired versions and memos are excluded with a reason.", False),
             ("4 Review agent", "MODEL plans what to read, uses read and search tools, checks each criterion with an exact quote.", True),
             ("5 Verifier", "CODE checks citations, quotes, consistency. Second check on approvals. No denial outcome exists.", False),
             ("6 Reviewer screen", "HUMAN DECIDES. Nurse confirms approvals. Physician signs adverse decisions.", False)]
    for i, (t, b, m_) in enumerate(steps):
        box(d, X[i], sy, sw, sh, t, b, "#f1f6fd" if m_ else ("#eaf6ea" if i == 5 else "#ffffff"), "#2a78d6" if m_ else ("#0a7a0a" if i == 5 else "#898781"))
        if i < 5: arrow(d, X[i] + sw + 1, sy + sh * .6, X[i] + sw + g - 1, sy + sh * .6)
    arrow(d, C[0], iy, C[0], sy + sh + 1); arrow(d, C[1], iy, C[0] + 14, sy + sh + 1); arrow(d, C[2], iy, C[1], sy + sh + 1)
    arrow(d, C[3], iy, C[2], sy + sh + 1); arrow(d, C[4] - 10, iy, C[3], sy + sh + 1); arrow(d, C[5], sy + sh, C[5], iy - 1)
    ly = sy - 9; arrow(d, C[4] - 12, sy, C[4] - 12, ly, False); arrow(d, C[4] - 12, ly, C[3] + 12, ly, False); arrow(d, C[3] + 12, ly, C[3] + 12, sy - 1)
    d.add(String(C[3] + 16, ly - 8, "rejected, with reasons", fontName=F, fontSize=6.6, fillColor=SEC))
    bh = 44; by = sy - 36 - bh
    box(d, X[2], by, 4 * sw + 3 * g, bh, "Audit log", "Every run: inputs, governing documents and versions, tool trace, model output, verifier report, human decision. This is what Riverbend can request on audit (Addendum Section 5).")
    for i in (3, 5): arrow(d, C[i] - 14 if i == 3 else C[i], sy, C[i] - 14 if i == 3 else C[i], by + bh + 1)
    arrow(d, C[4] + 12, sy, C[4] + 12, by + bh + 1)
    box(d, X[0], by, 2 * sw, bh, "Legend", "Blue = calls the model. White = ordinary code. Green = human decision.", "#ffffff", "#e1e0d9")
    return d

def build(name, story, title, size=A4):
    SimpleDocTemplate(os.path.join(DOCS, name), pagesize=size, leftMargin=M, rightMargin=M, topMargin=13 * mm, bottomMargin=14 * mm, title=title, author="Lohith Devaramane").build(story, onFirstPage=foot(title), onLaterPages=foot(title))

# ================================================================ 1. architecture (one landscape page)
LW = landscape(A4)[0] - 2 * M
build("Architecture_Diagram.pdf", [P("Bellcourt Review Copilot: architecture", "t"), P("Components, data flow, where PACE, fax and the portal plug in, and where the human decides", "sub"), Spacer(1, 10), architecture(LW), Spacer(1, 8),
      T([["Question", "Answer"],
         ["Where do fax and portal plug in?", "Step 1 reads images from the fax share and structured requests from the portal webhook. Both are read-only. The clock starts at the fax timestamp, not at keying."],
         ["Where does PACE plug in?", "Case data is read from a PACE read replica. The copilot never writes to PACE. The reviewer records the decision in PACE as today."],
         ["Where does the human decide?", "Step 6. The tool has four outcomes and none is a denial. A nurse confirms approvals. Only a physician signs an adverse determination. Intake staff review and send the fax-back."],
         ["What does the model do, and not do?", "It reads the fax, plans which sections to read, and checks criteria against the record. It does not choose which policy version governs: code does that from the registry."]], [62, 205])],
      "Bellcourt Review Copilot: architecture", landscape(A4))
import pypdfium2 as pdfium
pdfium.PdfDocument(os.path.join(DOCS, "Architecture_Diagram.pdf"))[0].render(scale=2.2).to_pil().save(os.path.join(DOCS, "architecture.png"))

# ================================================================ 2. documentation (max 8 pages)
from reportlab.platypus import Image as _Img
from reportlab.lib.utils import ImageReader as _IR
def FIG(name, wmm, cap):
    p_ = os.path.join(DOCS, "charts", name); iw, ih = _IR(p_).getSize(); w_ = wmm * mm
    return KeepTogether([_Img(p_, width=w_, height=w_ * ih / iw), Paragraph(cap, ST["cap"])])
def KP(items):
    t = Table([[[Paragraph(f'<font size="17" color="{c_}"><b>{a}</b></font>', st("k", leading=20)), Paragraph(f"<b>{b}</b>", ST["c"]), Paragraph(s_, st("ks", fontSize=7.4, leading=9.4, textColor=SEC))] for a, b, s_, c_ in items]], colWidths=[CW / len(items)] * len(items))
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, HAIR), ("INNERGRID", (0, 0), (-1, -1), 0.6, HAIR), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7), ("LEFTPADDING", (0, 0), (-1, -1), 8)])); return t
by = S["by_error_type"]; D = []
D += [P("Bellcourt Health Administrators: prior authorization under pressure", "t"), P("Data-backed diagnosis and solution. FDE hackathon, US healthcare. Lohith Devaramane, 6 October 2026.", "sub"), Spacer(1, 4),
      CALL("<b>Summary.</b> Bellcourt is late because requests arrive incomplete, and wrong because reviewers cannot find the rule that governs. It is not mainly a staffing problem. "
           "I built the <b>Bellcourt Review Copilot</b>, an Agentic RAG workspace that runs beside PACE. Code selects the governing rules by client, service and date. A model reads those sections and checks each criterion with quoted evidence. "
           "Incomplete requests are caught at intake. A nurse or physician makes every decision, and the decision letter is generated from it. "
           f"On the 120 cases Bellcourt's own QA team audited, the copilot agrees with the auditor on <b>{pct(S['tool_correct'], S['n'])}</b>; the original human decisions agreed on <b>{pct(S['human_correct'], S['n'])}</b>. It made zero wrongful approvals and it cannot deny."), Spacer(1, 5),
      KP([("56.7%", "Decisions correct in QA audit", "68 of 120. Contract standard 95%", "#b42a2a"), ("90.1%", "Riverbend MA decisions on time", "Q2 2026. Standard 97%", "#b42a2a"), ("56.2%", "Riverbend MA denials overturned", "41 of 73. Review trigger 30%", "#b42a2a"), ("$1.9M", "Service credits paid, FY2026", "About 21% of forecast profit", "#b42a2a")])]
D += Hd("1. The business and the prior authorization process")
D += [P("<b>What Bellcourt is.</b> A third-party administrator (TPA) founded in 2004 in Nashville, about 310 staff, FY2025 revenue $112.2M. It does not insure anyone. It runs health plans on behalf of others and is paid fees for doing so."),
      T([["Customer", "What Bellcourt does for them", "How Bellcourt is paid", "What they care about"],
         ["38 self-funded employers, about 453,000 people. Largest: Harlan Freight Lines", "Processes claims, tracks eligibility, answers members, and reviews care requests. The employer pays the medical bills from its own money (governed by ERISA).", "$34 to $46 per employee per month. About two-thirds of revenue ($75.1M).", "No wasteful approvals (it is their money) and no wrongful denials (their staff complain to HR). Contracts renew every 1 to 3 years."],
         ["Riverbend Health Plan: Medicare Advantage (92,400 members, AZ and TX) and Marketplace (61,300 members, GA)", "Decides prior authorization requests on Riverbend's behalf (delegated utilization management) since 2023.", "Per member per month plus per case. UM fees are $13.9M, the growth line.", "Timeliness (97%), accuracy (95%), appeal outcomes. Riverbend stays accountable to CMS, audits quarterly, and charges service credits."]], [42, 52, 38, 48]),
      P("<b>What prior authorization is.</b> A check before an expensive service such as an MRI or a knee replacement. It answers two separate questions: is the service <b>covered</b> under this member's plan, and is it <b>medically necessary</b> under written criteria? A nurse can approve. Only a physician can deny on medical necessity. "
        "Decisions have legal deadlines counted from receipt: 7 days for Medicare Advantage, 15 days for Marketplace and employer plans, 72 hours if urgent. Bellcourt handles about 310,000 requests a year."),
      T([["Step", "Today", "Where it breaks (from the data pack)"],
         ["1 Intake", "Requests arrive by fax (46%), portal (31%), phone (15%), electronic (8%). A coordinator retypes 14 fields from each fax into PACE.", "Faxes wait 16.9 hours on average before keying. PACE starts its clock at keying; the contract clock started at receipt."],
         ["2 Completeness", "Incomplete requests are pended and the provider is contacted.", "22.7% arrive incomplete (fax 32.3%). The wait for missing information averages about 3.5 days."],
         ["3 Nurse review", "Nurse works out which rules apply (plan document, Riverbend addendum, policy version, Medicare rule), reads the record, approves or refers.", "14.2 of 38 minutes per case go on finding the rules. PACE criteria screens are months out of date. The library has 1,100 files and file-name search."],
         ["4 Physician review", "A physician decides proposed denials.", "Only 2 of 6 medical directors hold Arizona licenses; Arizona is 66% of Riverbend MA requests."],
         ["5 Letter", "Staff copy the reason from the PACE note into a Word template.", "Letters are vague. Members read a plan exclusion as a medical judgement."],
         ["6 Status, appeals", "Providers phone for status. A separate team handles appeals.", "57% of calls are status checks, 20% abandoned. More than half of appeals are overturned."]], [26, 76, 78]),
      P("<b>The money.</b> Revenue grew 9.3% in three years while clinical staff cost grew 27.7% and intake and call-center cost 23.7%. Operating margin fell from 14.0% to a forecast 8.0%. Riverbend opened a Corrective Action Plan in July 2026, and its contract ends on 31 December 2026.", "b")]
D += Hd("2. Diagnosis, backed by the data pack")
D += [P("Leadership disagrees about the cause, so I tested each claim against the files: 2,400 requests, 120 QA-audited cases, 90 weeks of staffing, 3,200 calls, 38 knowledge base documents and 8 interviews."),
      T([["Claim", "What the data shows", "Verdict"],
         ["VP Operations: \"It's a staffing problem, full stop.\"", "Nurse FTE fell from 57.7 to 50.6 and the nurse stage did slow (32.5 to 38.1 hours). But the on-time rate does not move with staffing (weekly correlation -0.05), and it was already 87.0% in Q1 2025 at 98% of budgeted staff. All 64 late Riverbend MA standard decisions arrived incomplete.", "Mostly wrong"],
         ["VP Operations: overturns come from new information at appeal.", "Requests that arrived complete are overturned more often (56.7%) than incomplete ones (48.7%). Denials citing a retired policy version are overturned 91% of the time (30 of 33).", "Not supported"],
         ["Riverbend: \"That's a wrong-decision problem.\"", "QA audit: 68 of 120 decisions correct (56.7%) against a 95% standard; 72% on MA cases. 39% of 2026 MA denials cite a retired version.", "Supported"],
         ["Senior nurse: the hard part is which rules apply.", "39 of 52 audited errors are wrong-rule errors. Time study: 14.2 of 38.0 minutes locating rules, equal to 18.9 of 50.6 nurse FTE.", "Supported"],
         ["Intake: a third of faxes are missing something.", "66 of 69 late decisions arrived incomplete. Requests that arrive complete are on time 99.8% of the time.", "Supported"]], [44, 112, 24]),
      FIG("staffing.png", 150, "Figure 1. Staffing fell through 2026, but timeliness was already below standard at full staffing and did not fall with it. Sources: nurse_staffing_weekly.csv, pa_requests_2025_2026.csv (662 Riverbend MA standard requests)."),
      P("<b>Root cause 1: reviewers apply the wrong rule.</b> The rule that governs a case depends on the client, the service and the date of service. None of Bellcourt's tools tracks all three."),
      *BL(["<b>Retired versions.</b> 94 of 274 denials in 2026 (34%) cite a policy version that was no longer in force on the date of service.",
           "<b>A memo overrode policy.</b> UM-MEMO-2025-19 told nurses to keep a 6-week rule after the policy changed to 4 weeks. 72 lumbar MRI requests were denied under it; 18 of 21 appeals were overturned. GOV-01 says a memo cannot change criteria.",
           "<b>Plan changes did not reach reviewers.</b> Kestrel began covering bariatric surgery on 1 January 2026. The email went to another team. All 8 requests since were denied as excluded.",
           "<b>Medicare rules missed.</b> 20 glucose-monitor denials for Medicare Advantage members under the stricter Bellcourt rule; all 11 appeals overturned. Without rule errors the MA overturn rate would be 29%, under the 30% trigger."]),
      FIG("qa_errors.png", 150, "Figure 2. Three quarters of audited errors are failures to find the governing rule, not failures of clinical judgement. Source: qa_audit_sample_2026.csv."),
      P("<b>Root cause 2: the clock runs out before a nurse sees the case.</b> Late cases spend 122 of 199 hours waiting for missing information, while nurse review takes about 40 hours whether the case is late or not. Recomputing the real cases: keying faxes within an hour and shortening the wait by a quarter lifts the on-time rate from 90.3% to 97.7%; cutting nurse time by a third reaches only 94.0%."),
      FIG("hours.png", 158, "Figure 3. Riverbend MA standard requests: where the hours go. Source: pa_requests_2025_2026.csv."),
      P("Caveat stated openly: the pack does not say the QA sample is random, so I do not extrapolate 56.7% to all decisions. The request file shows the retired-version problem independently.", "cap")]
D += Hd("3. Priorities and business impact")
D += [T([["Rank", "Problem", "Evidence", "Business impact", "Fix and AI pattern"],
         ["1", "<b>Wrong rule applied.</b> Reviewers cannot find which plan document, policy version or Medicare rule governs.", "QA accuracy 56.7% vs 95%. MA overturn rate 56.2% vs a 30% trigger. 34% of 2026 denials on a retired version.", "Riverbend contract and CMS audit exposure. The \"algorithm denies care\" headline the CEO fears, in reverse: humans denying wrongly. 18.9 nurse FTE spent hunting rules.", "Governing-rule and criteria copilot. <b>Agentic RAG</b>. Built."],
         ["2", "<b>Clock lost at intake.</b> Fax, incomplete, days of waiting.", "66 of 69 late decisions arrived incomplete. MA timeliness 90.1% vs 97%.", "Direct cause of the $1.9M credits (4% of quarterly fees per point) and the Corrective Action Plan.", "Read the fax on arrival, check completeness, draft the request for missing items. <b>AI agent</b> step. Built as a slice."],
         ["3", "<b>No visibility.</b> Providers phone for status; employers get a quarterly PDF.", "67% of calls ask where a request is. 20% abandoned.", "Call-center cost up 24%. Harlan ($8.1M a year, satisfaction 5 of 10) renews 1 January 2027.", "Status lookup, requirements assistant (plain RAG), dashboard. Next phase."]], [10, 42, 44, 46, 38]),
      P("<b>Why problem 1 first.</b> It is the only fix that makes Bellcourt both faster and more defensible, which is the CEO's brief (\"not just faster\"). It is the cause Riverbend named, and accuracy below 95% triggers a Corrective Action Plan on its own. It returns nurse capacity without hiring: recovering half the rule-hunting time is worth 9.3 FTE against a vacancy gap of 7.4. Its rule engine is the foundation for problems 2 and 3. Because problem 2 drives the penalties, the build also includes its highest-value slice: catching incompleteness in the first minute.")]
D += Hd("4. The solution and where it fits")
D += [P("The <b>Bellcourt Review Copilot</b> is a signed-in workspace that runs beside PACE and never writes to it. It covers the whole path from request to decision letter."),
      architecture(CW), P("Figure 4. Architecture. Fax share, portal webhook, PACE read replica and eligibility files plug in read-only. Blue boxes call the model, white boxes are code, green is the human decision. Full page: Architecture_Diagram.pdf.", "cap"),
      T([["Stage", "What happens", "Who or what does it"],
         ["Raise a case", "Three ways in: upload a fax image or PDF, upload a case file, or fill the form (phone requests). A fax is read by a vision model into fields; code validates the member ID, service and dates. Every channel becomes the same case record.", "Intake, nurse, or the provider feed. Model for faxes only."],
         ["Intake check and queue", "Missing fields are listed at once and a request to the provider is drafted. The clock starts at receipt. The case joins a priority queue: overdue, urgent, due soon, standard.", "Code"],
         ["Which rules govern", "A registry of all 38 documents (type, client, version, effective dates, authority rank per GOV-01) selects the plan document and amendments, the Riverbend addendum and Medicare rule, and the policy version in force on the date of service. Retired versions and memos are excluded and shown with the reason.", "Code. The model never chooses a version."],
         ["Review", "The model plans which sections to read, reads only governing documents, follows cross-references, and marks each criterion met, not met or not documented with an exact quote from the record. Identifiers are removed first.", "Model with tools"],
         ["Verify", "Citations must be in force. Quotes must exist in the record. The outcome must match the checklist. Visit-limit arithmetic is recomputed. Every approval gets a skeptical second pass. A failure goes to manual review.", "Code plus a second model pass"],
         ["Human decision", "The reviewer sees the recommendation, the reasons, each criterion with its evidence, and the source documents one click away. Approve, pend for information, route to physician, or (physician only) deny. Differing from the recommendation needs a reason.", "Nurse or physician"],
         ["Decision letter and audit", "The letter is generated from the human decision: specific reason, provision relied on, appeal rights, Texas AI disclosure. PDF download and email. Every action is logged with user, role and time.", "Code, triggered by a person"]], [30, 112, 38]),
      P("<b>Why Agentic RAG.</b> Plain RAG retrieves by similarity, but versions 1 and 2 of a policy are near-identical text and the void memo looks highly relevant, so it would repeat today's error. An autonomous agent is not allowed: no tool may deny, delay or modify a request. So code selects the rules, the model reads and reasons within them, code verifies, and a person decides. The four outcomes are approve-ready, need information, route to physician and route as not covered. There is no deny outcome.")]
D += Hd("5. Evidence it works")
D += [FIG("results.png", 150, "Figure 5. Agreement with the QA auditor's correct decision. The grey bars for the three error groups are zero by definition: those are the cases where the auditor found the human decision wrong for that reason."),
      T([["Test", "Data", "Result"],
         ["Agreement with the QA auditor", "120 audited cases with the auditor's correct decision and governing source", f"<b>{S['tool_correct']} of {S['n']} ({pct(S['tool_correct'], S['n'])})</b>. Original human decisions: {S['human_correct']} of {S['n']} ({pct(S['human_correct'], S['n'])}). Governing document and version correct on {S['source_correct']}."],
         ["Safety", "Same 120 cases", f"{len(S['wrong_approvals'])} wrongful approvals. {S['outside_allowed']} denials issued (not possible by design)."],
         ["Open queue", "30 live cases including 13 fax images, against my own answer key", f"{SC['matched']} of {SC['total']}. Across runs 27 to 29; misses fall on the cautious side."],
         ["Adversarial inputs", "10 planted instructions (fake approvals, fake memos, \"ignore previous instructions\"), plus two real faxes in the pack", "10 of 10 flagged and ignored. Outcome unchanged."],
         ["Wrong and incomplete inputs", "Policy time-travel (7), missing therapy record, empty notes, unknown service, no date, unknown member, wrong client", f"{S['adversarial_passed']} of {S['adversarial_total']} in total. The one failure ended in manual review, not a wrong answer."],
         ["Deterministic tests", "Resolver, clock, eligibility, de-identification, verifier, sign-in and roles, case workflow, letters", "36 of 36 pass, with no model call."]], [44, 70, 66]),
      P(f"Model: {S['model']}, about {S['avg_latency']} seconds and a third of a US cent per case. Limits: prompts were tuned while looking at these cases, so a fresh random audit sample is the right next test; only 6 of 38 employer plan documents were in the pack. Details: Evidence_It_Works.pdf.", "cap")]
D += Hd("6. Success metrics")
D += [T([["Measure", "Today", "Target", "How measured"],
         ["Riverbend audit accuracy", "72% on MA cases in the QA sample", "At least 95%", "Monthly QA audit of tool-assisted cases"],
         ["MA appeal overturn rate", "56.2%", "Under 30%", "Appeals file"],
         ["MA standard decisions on time", "90.1% (Q2 2026)", "At least 97%", "Clock from receipt, not keying"],
         ["Denials citing a retired policy version", "34% of 2026 denials", "Zero", "Audit log"],
         ["Nurse minutes per case", "38.0, of which 14.2 finding rules", "About 25", "Repeat the time study"],
         ["Hours from fax receipt to missing-information request", "About 17 before keying", "Under 1", "Audit log timestamps"],
         ["Service credits to Riverbend", "$1.9M a year", "Zero", "Finance"],
         ["Adverse decisions made by the tool", "n/a", "Zero, always", "Audit log and tests"]], [58, 48, 28, 46])]
D += Hd("7. Compliance and risk")
D += [T([["Rule", "Source", "How the design meets it"],
         ["No tool may deny, delay or modify a request; a qualified human makes every adverse decision", "Riverbend addendum s5; CEO brief", "No denial outcome exists. Only the physician role can record a denial, enforced on the server. Requests to providers are drafts a person sends."],
         ["60 days' written notice before any AI tool is used", "Riverbend addendum s5", "Send notice on day 0. Pilot on self-funded plans (ERISA; state AI laws do not bind them) while the notice runs."],
         ["Produce inputs and outputs for any case on audit", "Riverbend addendum s5", "Each review stores inputs, governing documents and versions, tool trace, output and verifier report. Each human action is logged."],
         ["Arizona: licensed medical director signs denials. Texas: disclose AI use. Georgia: human review before denial", "Addendum s4; REG-02", "State flags on the case. Denial letters carry the Arizona sign-off line and the AI disclosure."],
         ["Denial notices state the specific reason, the provision relied on and appeal rights", "CMS-0057-F; ERISA; SPD s5.5", "Letters are generated from the cited provision and the criteria that failed."],
         ["Patient data is PHI", "IT interview; HIPAA", "Sign-in and roles. Name, date of birth, phone, record number and member ID are removed before the review step. Production runs in the Azure tenant under the existing agreement."],
         ["Provider content is outside Bellcourt's control", "Pack README; intake interview", "Treated as data. Planted instructions are flagged, cannot be evidence, and do not change the outcome."]], [62, 34, 84]),
      T([["Risk", "Mitigation"],
         ["The model misreads a record", "Rules chosen by code; quotes verified; second check on approvals; a person decides; monthly QA on tool-assisted cases."],
         ["The registry goes stale", "A policy is not live until its effective dates are in the registry. Plan amendments are filed there by account managers and copied to UM Operations."],
         ["Reviewers over-trust the recommendation", "The screen shows the evidence and the excluded documents, not just the answer. Overrides are easy and recorded."],
         ["Riverbend's January 2027 API obligation", "Not solved by this build. Named as a risk needing a vendor gateway; the structured case data is a first step."]], [52, 128])]
build("Bellcourt_Case_Documentation.pdf", D, "Bellcourt case documentation")

# ================================================================ 3. implementation strategy + one-page design note
I = [P("Implementation strategy: deploying within 90 days", "t"), P("Bellcourt Review Copilot. PACE stays; the copilot runs beside it.", "sub"), Spacer(1, 6)]
I += [T([["When", "What happens", "Why / exit test"],
         ["Day 0", "Send Riverbend the 60-day written notice. Rescind UM-MEMO-2025-19. Re-review the 72 lumbar MRI denials, the 8 Kestrel bariatric denials and the MA glucose-monitor denials. Report timeliness from receipt, not keying.", "The notice period is the critical path. The memo fix needs no technology."],
         ["Days 1 to 30: build and prove", "Host in the Azure tenant that already has a signed agreement for patient data. Connect read-only: fax share, portal webhook, PACE read replica, eligibility files. Load all 38 plan documents into the registry with the account managers. Replay closed cases.", "Exit: at least 95% agreement on a fresh, random QA sample of 200 closed cases, zero wrongful approvals."],
         ["Days 31 to 60: pilot on self-funded plans", "8 senior nurses and 2 intake coordinators use it on employer queues. Intake sends the drafted fax-back within the hour. Measure minutes per case, agreement and override reasons weekly.", "ERISA plans are not bound by the state AI laws or the notice clause. Exit: nurse minutes per case down by 25%."],
         ["Days 61 to 90: Riverbend go-live", "Notice has run. Turn on for Riverbend with Arizona routing and the Texas disclosure in letters. Share audit-log extracts with Riverbend oversight. Train all reviewers.", "Exit: MA on-time rate at least 97% and audit accuracy at least 95% for the month."],
         ["After day 90", "Provider status page and requirements assistant, employer dashboard, policy-change alerts that re-check open cases.", "Problems 2 and 3, on the same rule engine."]], [36, 92, 52]), Spacer(1, 6)]
I += Hd("Who does what") + BL(["<b>Chief Medical Officer</b> owns the registry: a policy is not live until its effective dates are in it.", "<b>Account managers</b> file every plan amendment into the registry and copy UM Operations.",
     "<b>IT (4 people)</b> provides the read replica, fax share access and Azure hosting. No change to PACE.", "<b>QA team</b> audits a monthly sample of tool-assisted cases and owns the go/no-go numbers.",
     "<b>Staffing:</b> fill the 7.4 vacant nurse FTE rather than add 20. Recovering half of the 14.2 minutes spent finding rules is worth 9.3 FTE. License more medical directors in Arizona."]) + [PageBreak()]
I += [P("Design note: technology choices", "t"), P("One page. The stack is deliberately small so it can be explained, audited and replaced.", "sub"), Spacer(1, 6),
      T([["Choice", "What I used", "Why", "In production at Bellcourt"],
         ["Pattern", "Agentic RAG with a deterministic rule resolver", "Plain RAG retrieves by similarity and would return the retired version or the memo. An autonomous agent is not allowed to decide. So: code selects, the model reads and reasons, a person decides.", "Same"],
         ["Metadata registry", "JSON built from each PDF's header plus a small overlay", "Effective dates, client and authority rank are the missing piece in the UM Library. Filtering on them is what prevents wrong-rule errors.", "Owned by the Clinical Policy Committee"],
         ["Vector store", "322 section embeddings (text-embedding-3-small, 256 dimensions) in a JSON file, cosine similarity in plain Python, fused with keyword rank", "The corpus is 38 documents. A hosted vector database adds a key, a network hop and a failure point with no retrieval gain at this size. The index interface is one function.", "Azure AI Search or Pinecone with the same metadata filters at 1,100+ documents"],
         ["Model", f"{S['model']}, via OpenRouter or the Gemini API directly", "Fast (about 6 seconds a case), cheap (about $0.004 a case), reads fax images. One environment variable swaps the provider or the model; I tested Claude models too.", "A model hosted in the Azure tenant under the existing agreement"],
         ["Agent loop", "Three to five calls: plan retrieval, review, verifier fixes, second check on approvals", "Bounded and fully logged. Every step is visible in the audit trail.", "Same"],
         ["Verifier", "Plain code", "Citations must be in force, quotes must exist in the record, outcome must match the checklist, arithmetic on visit limits is recomputed. The model cannot talk its way past code.", "Same"],
         ["Backend", "Python standard library only, two serverless functions", "Zero dependencies means nothing to break at deploy time and a tiny attack surface.", "Azure Functions or a container"],
         ["Screen and access", "One static HTML page. Sign-in with salted password hashes and signed 8-hour sessions; roles enforced on the server", "Case data and fax images are served only to signed-in users. A nurse cannot sign an adverse decision; an auditor cannot run a review.", "Single sign-on with Entra ID, same roles"],
         ["Storage", "Supabase (Postgres) through its REST API, one table for cases, letters and the audit log. Falls back to a local file", "Serverless functions keep no state, so cases, decisions and letters need a database. One generic table keeps the prototype simple.", "Azure SQL or Postgres inside the tenant, with proper tables"],
         ["Letters and email", "Letter text built in code from the human decision and the cited provision. A small built-in PDF writer. Gmail SMTP for the demo, delivered only to a configured demo mailbox", "A letter is never generated by the model alone and never sent without a human decision. No extra dependency.", "Bellcourt's correspondence system and print vendor"],
         ["Evidence", "Scripts that write JSON and the PDFs from the same run", "Numbers in the documents cannot drift from the numbers in the app.", "Monthly QA job"]], [26, 44, 70, 40]),
      Spacer(1, 6), P("<b>What I would change with more time:</b> a database-backed audit log instead of browser storage; a fresh held-out audit sample; a stronger model for the review step if the fresh sample shows drift; plan documents for the other 32 employers.")]
build("Implementation_Strategy_and_Design_Note.pdf", I, "Implementation strategy and design note")

# ================================================================ 4. EVIDENCE.md
L = ["# Evidence it works", "", f"Model `{S['model']}`. Generated by `scripts/run_open.py` and `scripts/run_eval.py`. Raw results: `data/results/*.json`.", "",
     "## 1. 120 cases audited by Bellcourt's QA team", "", "The auditor's `qa_correct_decision` is the ground truth. `original_decision` is what the human reviewer did.", "",
     "| | Correct | Rate |", "|---|---|---|", f"| Review Copilot | {S['tool_correct']} of {S['n']} | {pct(S['tool_correct'], S['n'])} |", f"| Original human decision | {S['human_correct']} of {S['n']} | {pct(S['human_correct'], S['n'])} |",
     f"| Copilot: governing document and version | {S['source_correct']} of {S['n']} | {pct(S['source_correct'], S['n'])} |", "",
     f"Wrongful approvals: **{len(S['wrong_approvals'])}**. Denials issued by the tool: **{S['outside_allowed']}**. Sent to manual review: {S['manual_review']}.", "",
     "| Auditor's error type on the human decision | Copilot correct |", "|---|---|"] + [f"| {k} | {v[0]} of {v[1]} |" for k, v in by.items()] + ["", "Misses:", "", "| Case | Service | Auditor | Copilot |", "|---|---|---|---|"] + \
    [f"| {r['id']} {r['client']} | {r['service']} | {r['truth']} | {r['tool']} |" for r in E["qa"] if r["tool"] != r["truth"]] + ["",
     "## 2. Open queue: 30 live cases, 13 of them fax images", "", f"{SC['matched']} of {SC['total']} match the answer key in `tests/open_cases_answer_key.csv` (my own reading of the policies).", "",
     "| Case | Expected | Got | | Flags |", "|---|---|---|---|---|"] + [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |" for r in SC["rows"]] + ["",
     "## 3. Adversarial, incomplete and wrong inputs", "", f"{S['adversarial_passed']} of {S['adversarial_total']} pass.", "", "| Test | Expected | Got | |", "|---|---|---|---|"] + \
    [f"| {a['test']} | {a['expected']} | {a['got']} | {'PASS' if a['passed'] else 'FAIL'} |" for a in E["adversarial"]] + ["",
     "## 4. Deterministic tests", "", "`python -m pytest -q` runs 36 tests with no model call: version by date of service, excluded documents, read-tool refusal, eligibility, clock, de-identification, planted-text detection, every verifier check, and no denial in saved results.", "",
     "## Honest limits", "", "- Results vary slightly between runs because the model is not fully deterministic. Across runs the open queue scored 27 to 29 of 30. Misses were on the cautious side (manual review, need information or physician referral).",
     "- Prompts were tuned while looking at these cases. The right next test is a fresh, random audit sample.", "- The open-case answer key is my reading of the policies, not an official key.", "- Only 6 of 38 employer plan documents are in the pack."]
open(os.path.join(DOCS, "EVIDENCE.md"), "w").write("\n".join(L) + "\n")
from pypdf import PdfReader
for f in ("Bellcourt_Case_Documentation.pdf", "Implementation_Strategy_and_Design_Note.pdf", "Architecture_Diagram.pdf"): print(f, len(PdfReader(os.path.join(DOCS, f)).pages), "pages")

# ================================================================ 5. pitch deck (14 slides, landscape)
from reportlab.pdfgen import canvas as _cv
PW_, PH_ = landscape(A4); BLUE = colors.HexColor("#2a78d6"); GOODC = colors.HexColor("#0a7a0a"); BADC = colors.HexColor("#b42a2a")
c = _cv.Canvas(os.path.join(DOCS, "Pitch_Deck.pdf"), pagesize=(PW_, PH_)); c.setTitle("Bellcourt Review Copilot: pitch deck"); c.setAuthor("Lohith Devaramane")
n_slide = [0]
def slide(title, kicker=""):
    if n_slide[0]: c.showPage()
    n_slide[0] += 1
    c.setFillColor(NAVY); c.rect(0, PH_ - 62, PW_, 62, stroke=0, fill=1); c.setFillColor(colors.white); c.setFont(FB, 22); c.drawString(36, PH_ - 40, title)
    if kicker: c.setFont(F, 10.5); c.setFillColor(colors.HexColor("#cde2fb")); c.drawString(36, PH_ - 55, kicker)
    c.setFillColor(SEC); c.setFont(F, 8); c.drawString(36, 18, "Bellcourt Review Copilot  |  Lohith Devaramane  |  fictional company, synthetic data"); c.drawRightString(PW_ - 36, 18, str(n_slide[0]))
def para(text, x, y, w, size=13, lead=None, color=INK, font=None):
    p = Paragraph(text, ParagraphStyle("x", fontName=font or F, fontSize=size, leading=lead or size * 1.38, textColor=color)); _, h = p.wrap(w, 1000); p.drawOn(c, x, y - h); return y - h
def bullets(items, x, y, w, size=13, gap=9):
    for t in items:
        c.setFillColor(BLUE); c.circle(x + 4, y - size * .62, 2.6, stroke=0, fill=1); y = para(t, x + 16, y, w - 16, size) - gap
    return y
def tile(x, y, w, h, num, label, sub="", col=NAVY):
    c.setFillColor(colors.white); c.setStrokeColor(HAIR); c.roundRect(x, y - h, w, h, 6, stroke=1, fill=1)
    c.setFillColor(col); c.setFont(FB, 27); c.drawString(x + 12, y - 36, num); yy = para(f"<b>{label}</b>", x + 12, y - 44, w - 22, 10.5)
    if sub: para(sub, x + 12, yy - 2, w - 22, 9, color=SEC)
def table(rows, x, y, widths, size=10):
    t = Table([[Paragraph(str(v), ParagraphStyle("c", fontName=FB if i == 0 else F, fontSize=size, leading=size * 1.3)) for v in r] for i, r in enumerate(rows)], colWidths=widths)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, 0), HEAD), ("LINEBELOW", (0, 0), (-1, -1), 0.5, HAIR), ("TOPPADDING", (0, 0), (-1, -1), 4.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5)]))
    _, h = t.wrap(sum(widths), 1000); t.drawOn(c, x, y - h); return y - h
X0, Wc, Y0 = 36, PW_ - 72, PH_ - 92; tw = (Wc - 36) / 4

slide("Bellcourt Review Copilot", "Prior authorization under pressure  |  FDE hackathon  |  Lohith Devaramane")
y = para("Bellcourt is <b>late because requests arrive incomplete</b>, and <b>wrong because reviewers cannot find the rule that governs</b>. It is not mainly a staffing problem.", X0, Y0 - 10, Wc, 20)
y = para("I built an Agentic RAG copilot that picks the governing rules in code, checks every criterion with quoted evidence, catches incomplete requests in the first minute, and leaves every decision to a person.", X0, y - 18, Wc, 15, color=SEC)
for i, (a, b, s_, col) in enumerate([(pct(S["tool_correct"], S["n"]), "Copilot agrees with the QA auditor", f"{S['tool_correct']} of {S['n']} audited cases", GOODC), (pct(S["human_correct"], S["n"]), "Human reviewers, same cases", "Contract standard is 95%", BADC), ("0", "Wrongful approvals", "and no denial is possible by design", NAVY), ("~6 s", "Per case", "about a third of a cent", NAVY)]): tile(X0 + i * (tw + 12), y - 26, tw, 96, a, b, s_, col)
para("Live demo: bellcourt-review-copilot.vercel.app   |   Code: github.com/devaramanelohith/bellcourt-review-copilot", X0, 64, Wc, 11, color=SEC)

slide("The business", "Who Bellcourt is and why prior authorization matters to it")
bullets(["Bellcourt is a <b>third-party administrator</b>: it runs health plans for <b>38 employers</b> who pay their staff's medical bills from their own money (453,000 people).",
         "Since 2023 it also decides prior authorizations for <b>Riverbend Health Plan</b> (153,700 members). Riverbend stays accountable to regulators, so it audits Bellcourt and charges penalties.",
         "<b>Prior authorization</b> = a check before an expensive service: is it covered under this plan, and is it medically necessary under written criteria? About 310,000 requests a year, 46% by fax.",
         "Nurses can approve. Only a physician can deny. Decisions have legal deadlines: 7 days for Medicare Advantage, 15 days otherwise, 72 hours if urgent."], X0, Y0, Wc * .56, 13)
for i, (a, b, s_) in enumerate([("14% to 8%", "Operating margin, 3 years", "Staff cost +28%, revenue +9%"), ("$1.9M", "Penalties to Riverbend this year", "About a fifth of profit"), ("31 Dec", "Riverbend contract ends", "Corrective Action Plan open since July")]): tile(X0 + Wc * .6, Y0 - i * 112, Wc * .4, 100, a, b, s_, BADC if i else NAVY)

slide("1. The problem", "What leadership sees")
for i, (a, b, s_) in enumerate([("90.1%", "Riverbend decisions on time", "Standard is 97%"), ("56.2%", "Riverbend denials overturned on appeal", "Review trigger is 30%"), ("56.7%", "Decisions correct in QA audit", "Standard is 95%"), ("20%", "Calls abandoned", "2,400 calls a day")]): tile(X0 + i * (tw + 12), Y0, tw, 100, a, b, s_, BADC)
y = para("Leadership does not agree on the cause.", X0, Y0 - 124, Wc, 15, font=FB)
table([["Who", "Their explanation"], ["VP Operations", "\"It's a staffing problem, full stop.\" Wants 20 more nurses."], ["CEO", "Doubts it, cannot prove otherwise. Wants \"faster and more defensible, not just faster\". Will not be \"the next headline\" on AI denials."],
       ["Riverbend", "\"That's a wrong-decision problem.\" Many denials cited the wrong criteria or an outdated version."], ["Senior nurse", "\"The clinical part is the easy part. The hard part is figuring out which rules apply.\""]], X0, y - 10, [130, Wc - 130], 11.5)

slide("2. How I found it: test every claim against the data", "2,400 requests, 120 audited cases, 90 weeks of staffing, 3,200 calls, 38 documents, 8 interviews")
table([["Claim", "What the data shows", "Verdict"],
       ["It is a staffing problem", "Nurse count fell 57.7 to 50.6, but on-time rate does not move with it (correlation -0.05). Timeliness was already 87% when staffing was at 98% of budget.", "Mostly wrong"],
       ["Overturns come from new information at appeal", "Requests that arrived complete are overturned more often (56.7%) than incomplete ones (48.7%).", "Not supported"],
       ["It is a wrong-decision problem", "39 of 52 audited errors are wrong-rule errors. 34% of 2026 denials cite a policy version already retired.", "Supported"],
       ["A third of faxes are missing something", "66 of 69 late decisions arrived incomplete. Complete requests are on time 99.8% of the time.", "Supported"]], X0, Y0, [200, Wc - 310, 110], 12)
para("Every number is reproducible from the data pack files. Caveat I state openly: the pack does not say the QA sample is random, so I do not extrapolate 56.7% to all decisions.", X0, 70, Wc, 11, color=SEC)

slide("Root cause 1: reviewers apply the wrong rule", "The rule depends on the client, the service and the date of service. The tools do not track any of the three.")
bullets(["<b>Retired policy versions.</b> 94 of 274 denials in 2026 cite a version that was no longer in force. Appeals against those succeed <b>91%</b> of the time.",
         "<b>A memo overrode policy.</b> 72 lumbar MRI requests denied under a 6-week rule after the policy changed to 4 weeks. Governance says memos cannot change criteria.",
         "<b>Plan changes never reached reviewers.</b> Kestrel began covering bariatric surgery in January. All 8 requests since were denied as excluded.",
         "<b>Medicare rules missed.</b> 20 glucose-monitor denials for Medicare members under the stricter Bellcourt rule. All 11 appeals overturned.",
         "<b>The cost in time.</b> 14.2 of 38 minutes per case go on finding the rule. That is 18.9 of 50.6 nurses, nearly the 20 the VP wants to hire."], X0, Y0, Wc, 13.5, 11)

slide("Root cause 2: the clock runs out before a nurse sees the case", "This is what causes the $1.9M in penalties")
bullets(["Riverbend's clock starts when the <b>fax arrives</b>. Bellcourt's system starts it when someone <b>types the fax in</b>, 17 hours later on average.",
         "A third of faxes are missing something. Nobody tells the provider until a person has opened the image.",
         "In late cases, <b>122 of 199 hours</b> were spent waiting for missing information. Nurse review took about 40 hours whether the case was late or not.",
         "What-if on the real data: typing faxes in within an hour and shortening the wait by a quarter lifts on-time from 90.3% to <b>97.7%</b>. Cutting nurse time by a third reaches only 94.0%."], X0, Y0, Wc * .58, 13.5, 11)
tile(X0 + Wc * .62, Y0, Wc * .38, 100, "66 of 69", "Late decisions arrived incomplete", "", BADC); tile(X0 + Wc * .62, Y0 - 112, Wc * .38, 100, "99.8%", "On time when the request arrives complete", "", GOODC); tile(X0 + Wc * .62, Y0 - 224, Wc * .38, 100, "17 h", "Fax waits before anyone keys it", "")

slide("Priorities: what to fix first", "Ranked by money, contract risk, client impact and fit to the CEO's brief")
table([["#", "Problem", "Impact", "Fix", "Pattern"],
       ["1", "<b>Wrong rule applied</b>", "Riverbend accuracy and audit exposure. 19 nurses' worth of time. The CEO's headline risk.", "Governing-rule and criteria copilot", "<b>Agentic RAG</b>. Built"],
       ["2", "<b>Clock lost at intake</b>", "Direct cause of the $1.9M penalties and the Corrective Action Plan.", "Read the fax on arrival, check completeness, draft the fax back", "<b>AI agent</b> step. Built as a slice"],
       ["3", "<b>No visibility</b>", "67% of calls ask where a request is. Harlan ($8.1M a year) wants reporting.", "Status lookup, requirements assistant, dashboard", "Plain RAG. Next"]], X0, Y0, [26, 150, Wc - 566, 220, 170], 12)
para("Why 1 first: it is the only fix that makes Bellcourt <b>both faster and more defensible</b>; it is the cause Riverbend named; and its rule engine is the foundation for 2 and 3. Because 2 drives the penalties, I built its highest-value slice too.", X0, Y0 - 250, Wc, 13.5)

slide("3. Approach: why Agentic RAG, with code choosing the rules", "RAG, Agentic RAG or an AI agent?")
table([["Option", "What it would do here", "Verdict"],
       ["Plain RAG", "Search by similarity and answer. But version 1 and version 2 of a policy are almost the same text, and the void memo looks highly relevant. It would repeat today's error.", "Not enough"],
       ["Autonomous AI agent", "Decide and act on its own. The Riverbend contract and state laws forbid any tool from denying, delaying or modifying a request.", "Not allowed"],
       ["Agentic RAG + deterministic resolver", "Code selects the documents in force from a registry (client, version, effective dates, authority rank). The model plans what to read, follows cross-references, and checks criteria. Code verifies. A person decides.", "Built"]], X0, Y0, [190, Wc - 300, 110], 12)
bullets(["<b>The model never chooses the policy version.</b> It can only read documents the registry says are in force. Asking for a retired version is refused.", "<b>Evidence must be quoted.</b> Every MET or NOT MET needs exact words from the record. Silence means ask for information, not deny.", "<b>Four outcomes, none is a denial.</b> A skeptical second pass checks every approval."], X0, Y0 - 215, Wc, 12.5, 7)

slide("4. Architecture", "Runs beside PACE and never writes to it. Blue = model, white = code, green = human")
arch = architecture(Wc); arch.drawOn(c, X0, Y0 - 300)
para("Fax share, portal webhook, PACE read replica and eligibility files plug in read-only at steps 1 and 2. The human decides at step 6 and records the decision in PACE as today.", X0, 62, Wc, 11, color=SEC)

slide("How each kind of request is read, and where the human decides", "One pipeline for every channel")
y = table([["Channel", "What arrives", "How the copilot reads it"],
       ["Fax (46%)", "An image on the fax share. Nobody has typed anything.", "A vision model transcribes the form into fields and detects blanks. The fax timestamp starts the clock."],
       ["Portal (31%)", "Structured fields and notes through the portal webhook.", "No reading needed. Straight to the completeness check."],
       ["Phone (15%)", "A call. The agent keys the request during the call.", "The agent types into the New request screen. The tool does not listen to calls. The agent sees what is missing while the caller is on the line."],
       ["Electronic (8%)", "Standard X12 278 transaction; PACE creates the case.", "Read from the PACE read replica as structured fields."]], X0, Y0, [110, 270, Wc - 380], 11)
bullets(["<b>Raise a case three ways:</b> upload a fax image or PDF, upload a case file, or fill the form. It joins a priority queue: overdue, urgent, due soon, standard.",
         "<b>Incomplete?</b> Missing items are listed at once and a request to the provider is drafted. <b>Human decision:</b> approve, pend, route to physician, or (physician only) deny.",
         "<b>Decision letter</b> is created from the human decision: specific reason, provision cited, appeal rights. PDF download and email. Everything is logged."], X0, y - 12, Wc, 12, 6)

slide("Evidence it works", "Tested on Bellcourt's own audited cases, the live queue, and hostile inputs")
for i, (a, b, s_, col) in enumerate([(f"{S['tool_correct']}/{S['n']}", "Agrees with the QA auditor", f"Humans: {S['human_correct']}/{S['n']}", GOODC), (f"{SC['matched']}/{SC['total']}", "Open queue incl. 13 faxes", "vs my answer key", NAVY), (f"{S['adversarial_passed']}/{S['adversarial_total']}", "Adversarial, incomplete, wrong inputs", "The 1 failure went to manual review", NAVY), ("36/36", "Unit tests, no model needed", "Resolver, verifier, login, letters", NAVY)]): tile(X0 + i * (tw + 12), Y0, tw, 100, a, b, s_, col)
table([["Where humans went wrong", "Copilot correct"], ["A memo overrode the policy", f"{by['MEMO_CONFLICT'][0]} of {by['MEMO_CONFLICT'][1]}"], ["Retired policy version applied", f"{by['OUTDATED_POLICY_VERSION'][0]} of {by['OUTDATED_POLICY_VERSION'][1]}"],
       ["Client plan rule missed", f"{by['CLIENT_RULE_MISSED'][0]} of {by['CLIENT_RULE_MISSED'][1]}"], ["Clinical facts misread", f"{by['CRITERIA_MISREAD'][0]} of {by['CRITERIA_MISREAD'][1]}"]], X0, Y0 - 120, [250, 120], 12)
bullets(["<b>Planted instructions:</b> 10 of 10 flagged and ignored, plus the two real faxes in the queue.", "<b>Policy time-travel:</b> same record, different service date, correct version each time.", f"<b>Zero wrongful approvals</b> and zero denials on the {S['n']} audited cases.",
         "<b>Honest limits:</b> results vary slightly between runs; prompts were tuned on these cases, so a fresh audit sample is the next test."], X0 + 400, Y0 - 120, Wc - 400, 12, 7)

slide("Compliance and safety by design", "\"Show me how any tool would work under those rules\" (Riverbend oversight)")
table([["Rule", "How the design meets it"],
       ["No tool may deny, delay or modify a request (Riverbend addendum, state laws)", "No denial outcome exists. The fax back is a draft a person sends. Tests assert zero denials."],
       ["60 days' written notice before any AI tool is used", "Notice sent on day 0. Pilot on self-funded employer plans while the notice runs."],
       ["Produce inputs and outputs for any case on audit", "Every run logs inputs, governing documents and versions, tool trace, output, verifier report and the human decision."],
       ["Arizona: licensed medical director signs denials. Texas: disclose AI use", "Flags route Arizona cases to a licensed director and add the Texas disclosure to the letter draft."],
       ["Patient data is protected", "Name, date of birth, phone, record number and member ID are removed before the review step. Sign-in required; roles enforced on the server."],
       ["Provider content is untrusted", "Text in faxes and notes is data. Planted instructions are flagged, cannot count as evidence, and do not change the outcome."]], X0, Y0, [300, Wc - 300], 11.5)

slide("Deploying at Bellcourt in 90 days", "PACE stays. Four people in IT. No new headcount.")
table([["When", "What", "Exit test"], ["Day 0", "Send Riverbend the 60-day notice. Withdraw the lumbar MRI memo. Re-review the affected denials.", "No technology needed"],
       ["Days 1 to 30", "Host in the Azure tenant that already has the patient-data agreement. Connect read-only. Load all 38 plan documents. Replay closed cases.", "95% on a fresh random audit sample, zero wrongful approvals"],
       ["Days 31 to 60", "Pilot with 8 senior nurses and 2 intake staff on employer plans.", "Nurse minutes per case down 25%"], ["Days 61 to 90", "Go live on Riverbend with Arizona routing and Texas disclosure.", "97% on time, 95% audit accuracy"]], X0, Y0, [100, Wc - 360, 260], 12)
bullets(["<b>Staffing answer:</b> fill the 7.4 vacant nurse posts instead of adding 20. Recovering half the rule-hunting time is worth 9.3 nurses.", "<b>The ask this week:</b> send the notice, withdraw the memo, approve the re-review."], X0, Y0 - 240, Wc, 13, 8)

slide("5. Live demo", "bellcourt-review-copilot.vercel.app")
table([["Step", "Show", "Point"], ["1", "Sign in as a nurse. Queue sorted by priority", "Case 8113 is an urgent fax that is already overdue and nobody had keyed it"],
       ["2", "Case 8100, lumbar MRI", "Picks the current policy by date of service. The old version and the memo are listed as excluded, with reasons. Evidence is quoted"],
       ["3", "Case 8106, fax with a planted \"pre-approved\" note", "Fax read into fields. Note flagged and ignored. Outcome rests on the criteria"],
       ["4", "Case 8120, missing second opinion", "Need information. Fax back to the provider already drafted"],
       ["5", "Case 8105 as nurse, then as physician", "The nurse cannot sign an adverse decision. The tool cannot deny"],
       ["6", "New case: upload a fax image, run the review, approve, open the decision letter, email it", "End to end in under a minute: intake, review, human decision, letter"],
       ["7", "Evidence tab and audit trail", f"{S['tool_correct']} of {S['n']} against {S['human_correct']} of {S['n']}. Every step logged"]], X0, Y0, [40, 300, Wc - 340], 12)
c.save()

# ================================================================ 6. submission text
open(os.path.join(DOCS, "SUBMISSION.md"), "w").write(f"""# Submission-ready text

## Comment to post

```
## 📥 Submission: Lohith Devaramane

- 🐙 **GitHub:** @devaramanelohith · 🎓 **Cohort:** [C2]
- 🔗 **Submission:** https://github.com/devaramanelohith/bellcourt-review-copilot
- ▶️ **Demo:** https://bellcourt-review-copilot.vercel.app (sign-in required; demo logins: [paste from DEMO_LOGINS.txt]) · video: [your recording link]
- 🔍 **Problems I found:** (1) Reviewers apply the wrong rule: 34% of 2026 denials cite a retired policy version and 91% of those are overturned. (2) The clock is lost at intake: 66 of 69 late decisions arrived incomplete, and faxes wait 17 hours before keying. (3) No status visibility: 67% of calls ask where a request is.
- 🎯 **What I built:** Wrong-rule decisions and late detection of incomplete requests, solved using Agentic RAG with a deterministic rule resolver and a human decision at the end, built with Python (standard library), Gemini 2.5 Flash via OpenRouter, a metadata registry plus vector index, Supabase, and Vercel. Cases can be raised by form, case file, fax image or PDF; a nurse or physician decides; a decision letter is generated and emailed. On Bellcourt's 120 audited cases it agrees with the auditor on {S['tool_correct']} ({pct(S['tool_correct'], S['n'])}) against {S['human_correct']} ({pct(S['human_correct'], S['n'])}) for the original human decisions, with zero wrongful approvals.
```

## Deliverables checklist

| Deliverable | File or link |
|---|---|
| Documentation (PDF, max 8 pages) | `docs/Bellcourt_Case_Documentation.pdf` |
| Architecture diagram | `docs/Architecture_Diagram.pdf`, `docs/architecture.png`, mermaid in `README.md` |
| Implementation strategy (90 days) + one-page design note | `docs/Implementation_Strategy_and_Design_Note.pdf` |
| Working demo | https://bellcourt-review-copilot.vercel.app |
| README + setup steps | `README.md` |
| Evidence it works | `docs/EVIDENCE.md`, Evidence tab in the app, `tests/` |
| Pitch deck (optional, 14 slides) | `docs/Pitch_Deck.pdf` |

## One-line answers for the panel

- **Problem:** Bellcourt is late because requests arrive incomplete, and wrong because reviewers cannot find the governing rule.
- **How I found it:** tested each stakeholder claim against the request file, the QA audit, staffing and call logs. Staffing does not explain the misses.
- **Approach and why:** Agentic RAG. Plain RAG would retrieve the retired version; an autonomous agent is not allowed to decide. Code selects the rules, the model reads and checks, a person decides.
- **Architecture:** intake, member and clock, rule resolver, review agent, verifier, reviewer screen, audit log. Read-only beside PACE.
- **Live demo:** cases 8113, 8100, 8106, 8120, 8105, then raise a new case from a fax image, decide it, open and email the decision letter, then Evidence.
""")
print("Pitch_Deck.pdf", len(PdfReader(os.path.join(DOCS, "Pitch_Deck.pdf")).pages), "slides")

# ================================================================ 7. evidence PDF and setup PDF, then the submission folder
EV = [P("Evidence it works", "t"), P("How the Review Copilot was tested, on what data, with what results, including wrong, incomplete and adversarial inputs", "sub"), Spacer(1, 6)]
EV += Hd("How it was tested") + [T([["Test set", "What it is", "How it is scored"],
    ["120 audited cases", "qa_audit_sample_2026.csv from the data pack. Each row has the clinical summary, the original human decision, and the QA auditor's correct decision and governing source.", "The copilot's recommendation is compared with the auditor's correct decision. Approve-ready = approve, need information = pend, route to physician = medical necessity denial, route not covered = coverage denial."],
    ["30 open cases", "The live queue in the pack: 17 structured requests and 13 that exist only as fax images.", "Compared with an answer key I wrote from the policies before running the tool (tests/open_cases_answer_key.csv)."],
    ["24 hostile and broken inputs", "Planted instructions, policy time-travel, missing information, wrong inputs.", "Expected outcome and expected flag."],
    ["36 unit tests", "No model call. Rule resolver, clock, eligibility, de-identification, verifier, sign-in and roles, workflow, letters.", "python -m pytest -q"]], [36, 78, 66]),
    P(f"Model: {S['model']}. Average {S['avg_latency']} seconds and {S['avg_tokens_in'] + S['avg_tokens_out']} tokens per case. Scripts: scripts/run_eval.py and scripts/run_open.py. Raw results: data/results/*.json.", "cap")]
EV += Hd("1. Audited cases") + [FIG("results.png", 150, "Agreement with the QA auditor's correct decision."),
    T([["", "Correct", "Rate"], ["Review Copilot", f"{S['tool_correct']} of {S['n']}", pct(S["tool_correct"], S["n"])], ["Original human decision", f"{S['human_correct']} of {S['n']}", pct(S["human_correct"], S["n"])],
       ["Copilot: governing document and version", f"{S['source_correct']} of {S['n']}", pct(S["source_correct"], S["n"])], ["Wrongful approvals by the copilot", str(len(S["wrong_approvals"])), ""], ["Denials issued by the copilot", str(S["outside_allowed"]), "Not possible by design"]], [90, 50, 40]), Spacer(1, 4),
    T([["Auditor's finding on the original human decision", "Copilot correct"]] + [[k.replace("_", " ").capitalize() if k != "NONE" else "No human error", f"{v[0]} of {v[1]}"] for k, v in by.items()], [120, 60]), Spacer(1, 4),
    T([["Every miss", "Service", "Auditor", "Copilot"]] + [[f"{r['id']} {r['client']}", r["service"], r["truth"], r["tool"]] for r in E["qa"] if r["tool"] != r["truth"]], [34, 70, 40, 36])]
EV += Hd("2. Open queue (30 cases, 13 fax images)") + [P(f"{SC['matched']} of {SC['total']} match the answer key."), T([["Case", "Expected", "Got", "", "Flags raised"]] + [[r[0], r[1], r[2], r[3], r[4].replace(",", ", ").replace("_", " ").lower()] for r in SC["rows"]], [26, 36, 36, 12, 70])]
EV += Hd("3. Adversarial, incomplete and wrong inputs") + [P(f"{S['adversarial_passed']} of {S['adversarial_total']} pass."), T([["Test", "Expected", "Got", ""]] + [[a["test"], a["expected"], a["got"], "PASS" if a["passed"] else "FAIL"] for a in E["adversarial"]], [98, 34, 34, 14])]
EV += Hd("4. Honest limits") + BL(["Results vary slightly between runs because the model is not fully deterministic. The open queue scored 27 to 29 of 30 across runs. Misses were on the cautious side: manual review, need information, or physician referral.",
    "Prompts were tuned while looking at these cases. The right next test is a fresh, random audit sample.", "The open-case answer key is my reading of the policies, not an official key.", "Only 6 of 38 employer plan documents are in the pack, so the prototype covers 8 clients."])
build("Evidence_It_Works.pdf", EV, "Evidence it works")

code = lambda t: Paragraph(t.replace(" ", "&nbsp;"), st("code", fontName="Courier", fontSize=8.2, leading=11, backColor=colors.HexColor("#f6f6f3"), leftIndent=6, spaceAfter=2))
RD = [P("Bellcourt Review Copilot: README and setup", "t"), P("Runnable solution. Live: https://bellcourt-review-copilot.vercel.app   Code: https://github.com/devaramanelohith/bellcourt-review-copilot", "sub"), Spacer(1, 6)]
RD += Hd("What it is") + [P("An Agentic RAG workspace for prior authorization review that runs beside PACE. A case is raised by form, case file, fax image or PDF. Code checks completeness, eligibility and the clock, and selects the governing rules by client, service and date. "
    "A model reads those sections and checks each criterion with quoted evidence. A nurse or physician decides, and a decision letter is generated from the decision. Sign-in is required and roles are enforced on the server.")]
RD += Hd("Try the live demo") + BL(["Open https://bellcourt-review-copilot.vercel.app and sign in with a demo login from the submission comment (nurse, physician, intake or auditor).",
    "<b>Queue:</b> a few sample cases sorted by priority. Open PA-2609-8100 to see a recommendation with criteria, quoted evidence, and the retired policy version and memo listed as excluded.",
    "<b>New case:</b> upload a fax image (samples in data/fax/) or an open-case file (samples in data/open_cases/), then run the review.", "<b>Decide:</b> approve as nurse, or sign in as physician to deny. Open the letter under Decision letters and download the PDF.",
    "<b>Evidence</b> and <b>Audit log</b> pages show the test results and every recorded action."])
RD += Hd("Run it locally") + [code("git clone https://github.com/devaramanelohith/bellcourt-review-copilot"), code("cd bellcourt-review-copilot"), code("cp .env.example .env        # set AUTH_SECRET; add OPENROUTER_API_KEY for live reviews"),
    code('python3 scripts/set_password.py nurse nurse "Your Name"   # create a login'), code("python3 scripts/dev_server.py      # Python 3.10+, no packages needed"), code("# open http://localhost:8765"), Spacer(1, 4),
    P("The runtime uses only the Python standard library. Without a model key the app still shows all saved reviews.")]
RD += Hd("Reproduce the evidence") + [code("python3 -m venv .venv && .venv/bin/pip install pdfplumber pytest reportlab pypdfium2 pypdf matplotlib"), code(".venv/bin/python -m pytest -q             # 36 tests, no key needed"),
    code(".venv/bin/python scripts/ingest.py        # PDFs -> sections, registry, vectors"), code(".venv/bin/python scripts/run_open.py      # 30 open cases"), code(".venv/bin/python scripts/run_eval.py      # 120 audited cases + adversarial tests"),
    code(".venv/bin/python scripts/build_docs.py    # regenerate every PDF from the results")]
RD += Hd("Deploy on Vercel") + [code("vercel login"), code("vercel env add AUTH_SECRET production            # any long random string"), code("vercel env add OPENROUTER_API_KEY production     # for live reviews"),
    code("vercel env add SUPABASE_URL production           # optional: persistence"), code("vercel env add SUPABASE_SERVICE_KEY production"), code("vercel env add GMAIL_USER production             # optional: email letters"),
    code("vercel env add GMAIL_APP_PASSWORD production"), code("vercel env add LETTER_TO_EMAIL production"), code("vercel --prod --yes"), Spacer(1, 4), P("Supabase needs one table; the SQL is in docs/SETUP_DATABASE_AND_EMAIL.md.")]
RD += Hd("How the code is organised") + [T([["File", "Role"], ["copilot/core.py", "Deterministic core: registry, rule resolver, read and search tools, eligibility, clock, de-identification, verifier"],
    ["copilot/agent.py", "Prompts and the bounded agent loop: plan, read, review, verify, second check. Fax and text reading"], ["copilot/pipeline.py", "run_case(): ties the steps together and applies overrides the model cannot undo"],
    ["copilot/cases.py, letters.py, store.py, auth.py", "Case lifecycle and decisions; letters, PDF and email; Supabase or file storage; sign-in and roles"], ["copilot/llm.py", "The only module that calls a model (OpenRouter or Gemini API)"],
    ["api/*.py", "Serverless endpoints: login, cases, data, review, ask"], ["public/index.html", "The workspace: queue, new case, case review, decision letters, policy library, evidence, audit log"],
    ["scripts/, tests/, data/", "Ingestion, evaluation, document builder; 36 tests; knowledge base, sample cases, saved results"]], [62, 118])]
build("README_and_Setup.pdf", RD, "README and setup")

import shutil, zipfile
SUB = os.path.join(ROOT, "deliverables"); shutil.rmtree(SUB, ignore_errors=True); os.makedirs(SUB)
for i, (f, n) in enumerate([("Bellcourt_Case_Documentation.pdf", "1_Documentation_Data_Backed_Diagnosis_and_Solution.pdf"), ("Architecture_Diagram.pdf", "2_Architecture_Diagram.pdf"), ("Implementation_Strategy_and_Design_Note.pdf", "3_Implementation_Strategy_and_Design_Note.pdf"),
                            ("README_and_Setup.pdf", "4_Working_Demo_README_and_Setup.pdf"), ("Evidence_It_Works.pdf", "5_Evidence_It_Works.pdf"), ("Pitch_Deck.pdf", "6_Pitch_Deck.pdf")]): shutil.copy(os.path.join(DOCS, f), os.path.join(SUB, n))
shutil.copy(os.path.join(DOCS, "architecture.png"), os.path.join(SUB, "2_Architecture_Diagram.png"))
open(os.path.join(SUB, "0_Submission_Text.txt"), "w").write(open(os.path.join(DOCS, "SUBMISSION.md")).read())
with zipfile.ZipFile(os.path.join(ROOT, "Bellcourt_Submission_Lohith_Devaramane.zip"), "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir(SUB)): z.write(os.path.join(SUB, f), "Bellcourt_Submission_Lohith_Devaramane/" + f)
for f in ("Evidence_It_Works.pdf", "README_and_Setup.pdf"): print(f, len(PdfReader(os.path.join(DOCS, f)).pages), "pages")
print(sorted(os.listdir(SUB)))

# ================================================================ 8. the 8-minute deck (6 slides)
c = _cv.Canvas(os.path.join(DOCS, "Pitch_Deck_8min.pdf"), pagesize=(PW_, PH_)); c.setTitle("Bellcourt Review Copilot: 8-minute presentation"); c.setAuthor("Lohith Devaramane"); n_slide[0] = 0
slide("The problem", "Bellcourt Health Administrators  |  prior authorization  |  Lohith Devaramane")
y = para("Bellcourt runs health plans for <b>38 employers</b> and decides prior authorization requests for an insurer, <b>Riverbend</b>, which audits it, penalises it, and can leave on 31 December.", X0, Y0 - 6, Wc, 15)
y = para("Prior authorization: is the service covered, and is it medically necessary? Nurses approve. Only physicians deny. Deadlines are legal: 7 days, 15 days, 72 hours urgent. About 310,000 requests a year, 46% by fax.", X0, y - 10, Wc, 13, color=SEC)
for i, (a, b, s_) in enumerate([("90.1%", "Decisions on time", "Standard 97%"), ("56.7%", "Correct in QA audit", "Standard 95%"), ("56.2%", "Denials overturned on appeal", "Trigger 30%"), ("$1.9M", "Penalties this year", "A fifth of profit")]): tile(X0 + i * (tw + 12), y - 24, tw, 96, a, b, s_, BADC)
para("Leadership's explanation: <b>\"It's a staffing problem, full stop.\"</b> Twenty more nurses. The CEO is not convinced.", X0, y - 140, Wc, 14)
slide("How I found it", "Every stakeholder claim tested against the data pack: 2,400 requests, 120 audited cases, 90 weeks of staffing, 3,200 calls")
y = table([["Claim", "What the data shows"], ["It is a staffing problem", "Nurse count fell 57.7 to 50.6, but on-time rate did not move with it (correlation -0.05) and was already 87% at full staffing. <b>All 64 late Medicare Advantage decisions arrived incomplete.</b> Complete requests are on time 99.8% of the time."],
       ["Overturns come from new information at appeal", "Complete requests are overturned more often (56.7%) than incomplete ones (48.7%). Denials citing a retired policy are overturned <b>91%</b> of the time."],
       ["It is a wrong-decision problem (Riverbend)", "39 of 52 audited errors are rule lookups, not clinical judgement. <b>34% of 2026 denials</b> cite a retired policy version. A memo kept a 6-week rule after the policy moved to 4 weeks: 72 wrong denials. Kestrel's plan change never reached reviewers: 8 wrong denials."]], X0, Y0, [200, Wc - 200], 12)
para("<b>Diagnosis:</b> late because requests arrive incomplete (122 of 199 hours in late cases is waiting for information), wrong because reviewers cannot find the rule that governs (14 of 38 minutes per case spent hunting). Fix the rule first: it is the only fix that is both faster and more defensible.", X0, y - 16, Wc, 13)
slide("Key elements of the build", "Agentic RAG with a deterministic rule resolver. Code picks the rule, the model checks the evidence, a person decides.")
arch = architecture(Wc * 0.62); arch.drawOn(c, X0, Y0 - 300)
bullets(["<b>Registry</b> of all 38 documents: type, client, version, effective dates, authority rank (GOV-01).", "<b>Rule resolver in code</b> picks what is in force on the date of service. The model never chooses a version.",
         "<b>Bounded agent</b> plans its reads; the read tool refuses anything not in force; every Met needs an exact quote.", "<b>Verifier in code</b>: citations in force, quotes in the record, outcome consistent, visit arithmetic recomputed. Rejections go back to the model.",
         "<b>Second skeptical pass</b> on every approval.", "<b>Human decision</b> with four outcomes and no deny. Decision letter generated from the decision. Priority queue, fax and PDF reading, email."], X0 + Wc * 0.65, Y0, Wc * 0.35, 10.5, 5)
slide("Governance and security", "Built to the Riverbend addendum and the state AI laws")
table([["Governance", "Security"],
       ["GOV-01 hierarchy enforced in code: law, then plan document, then policy version by date of service. Memos can never be criteria; excluded documents are shown with the reason.", "Sign-in with salted password hashes and signed 8-hour sessions. Roles enforced on the server: only a physician can deny, an auditor is read-only."],
       ["No tool may deny, delay or modify a request: there is no deny outcome, requests to providers are drafts a person sends, tests assert it.", "Case data and fax images are served only to signed-in users. Supabase holds cases, letters and the audit log."],
       ["Audit: every run stores inputs, governing documents and versions, tool trace, output, verifier report and the human decision (addendum s5).", "Identifiers (name, DOB, phone, record number, member ID) are removed before the review step. The fax reader runs inside the tenant in production."],
       ["Arizona: licensed director signs denials. Texas: AI disclosure in the letter. Georgia: human review before denial. 60-day notice to Riverbend on day 0; pilot on ERISA plans meanwhile.", "Provider text is untrusted: planted instructions are flagged, cannot be evidence, and do not change the outcome. Tested with 10 injections and 2 real planted faxes."]], X0, Y0, [Wc / 2, Wc / 2], 11.5)
slide("How I evaluated it", "Bellcourt's own audited cases, the live queue, hostile and broken inputs")
for i, (a, b, s_, col) in enumerate([(f"{S['tool_correct']}/{S['n']}", "Agrees with the QA auditor", f"Humans: {S['human_correct']}/{S['n']}. Standard 95%", GOODC), ("0", "Wrongful approvals, 0 denials issued", "by construction and by test", GOODC), (f"{S['adversarial_passed']}/{S['adversarial_total']}", "Adversarial and broken inputs", "the 1 failure went to manual review", NAVY), ("36/36", "Unit tests, no model", "resolver, verifier, roles, letters", NAVY)]): tile(X0 + i * (tw + 12), Y0, tw, 100, a, b, s_, col)
table([["Where the human reviewer went wrong", "Copilot correct"], ["Memo overrode the policy", f"{by['MEMO_CONFLICT'][0]} of {by['MEMO_CONFLICT'][1]}"], ["Retired policy version applied", f"{by['OUTDATED_POLICY_VERSION'][0]} of {by['OUTDATED_POLICY_VERSION'][1]}"], ["Client plan rule missed", f"{by['CLIENT_RULE_MISSED'][0]} of {by['CLIENT_RULE_MISSED'][1]}"], ["Clinical facts misread", f"{by['CRITERIA_MISREAD'][0]} of {by['CRITERIA_MISREAD'][1]}"]], X0, Y0 - 120, [260, 110], 12)
bullets(["<b>Planted instructions:</b> 10 of 10 flagged and ignored, plus the two real faxes in the pack.", "<b>Policy time-travel:</b> same record, different service date, correct version each time (7 of 7).", "<b>Missing and wrong inputs:</b> empty notes, unknown service, no date, unknown member, wrong client: safe outcome, no crash.",
         "<b>Honest limits:</b> results vary slightly between runs (27 to 29 of 30 on the queue), always toward a person. Prompts were tuned on these cases: a fresh audit sample is the next test."], X0 + 400, Y0 - 120, Wc - 400, 11.5, 6)
slide("What Bellcourt should do next", "Questions")
table([["When", "What"], ["Day 0", "Send Riverbend the 60-day notice. Withdraw the memo. Re-review the affected denials. Report timeliness from receipt."], ["Days 1 to 30", "Host in the Azure tenant. Connect read-only. Load all 38 plan documents. Replay closed cases: 95% on a fresh sample, zero wrongful approvals."],
       ["Days 31 to 60", "Pilot with 8 senior nurses and 2 intake staff on employer plans."], ["Days 61 to 90", "Riverbend go-live with Arizona routing and Texas disclosure."]], X0, Y0, [110, Wc - 110], 12)
para("Staffing: fill the 7 vacancies, do not add 20. Rule-hunting is 19 nurses' worth of time today.   |   Live: bellcourt-review-copilot.vercel.app   |   Code: github.com/devaramanelohith/bellcourt-review-copilot", X0, 70, Wc, 11, color=SEC)
c.save(); print("Pitch_Deck_8min.pdf", len(PdfReader(os.path.join(DOCS, "Pitch_Deck_8min.pdf")).pages), "slides")
