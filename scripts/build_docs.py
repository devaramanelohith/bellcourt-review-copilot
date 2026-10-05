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
E = json.load(open(os.path.join(ROOT, "public/data/eval.json"))); S = E["summary"]; SC = json.load(open(os.path.join(ROOT, "public/data/open_score.json")))
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
by = S["by_error_type"]; D = []
D += [P("Bellcourt Health Administrators: prior authorization under pressure", "t"), P("Case documentation. FDE hackathon, US healthcare. Lohith Devaramane, 6 October 2026.", "sub"), Spacer(1, 4),
      CALL("<b>In one paragraph.</b> Bellcourt is late because requests arrive incomplete, and wrong because reviewers cannot find the rule that governs. It is not mainly a staffing problem. "
           f"I built a Review Copilot (Agentic RAG) that selects the governing rules by client, service and date, checks each criterion with quoted evidence, and drafts the fax-back for missing information at intake. "
           f"On the 120 cases Bellcourt's own QA team audited, it agrees with the auditor on <b>{pct(S['tool_correct'], S['n'])}</b>. The original human decisions agreed on <b>{pct(S['human_correct'], S['n'])}</b>. It issued zero wrongful approvals and cannot deny.")]
D += Hd("1. The business and the prior authorization process")
D += [P("Bellcourt is a third-party administrator (TPA). It runs health plans for <b>38 self-funded employers</b> (about 453,000 people) who pay their staff's medical bills from their own money and pay Bellcourt a fee per employee per month. "
        "Since 2023 it also decides prior authorization requests on behalf of <b>Riverbend Health Plan</b> (about 153,700 members), which stays accountable to regulators and so audits Bellcourt and charges service credits when standards are missed. "
        "Prior authorization is a check before an expensive service: is it covered under this member's plan, and is it medically necessary under written criteria? Bellcourt handles about 310,000 requests a year."),
      T([["Step", "Today", "Where it breaks (from the data pack)"],
         ["1 Intake", "46% of requests arrive by fax. A coordinator retypes 14 fields into PACE.", "Faxes wait 16.9 hours on average before keying. PACE starts its clock at keying; the contract clock started at receipt."],
         ["2 Completeness", "Incomplete requests are pended and the provider is contacted.", "22.7% arrive incomplete (fax 32.3%). The wait for missing information averages about 3.5 days."],
         ["3 Nurse review", "Nurse works out which rules apply, reads the record, approves or refers. Nurses cannot deny.", "14.2 of 38 minutes per case go on finding the rules. PACE criteria screens are months out of date."],
         ["4 Physician review", "A physician decides proposed denials.", "Only 2 of 6 medical directors hold Arizona licenses; Arizona is 66% of Riverbend MA requests."],
         ["5 and 6 Letters, status, appeals", "Reasons copied by hand into Word templates. Providers phone for status.", "57% of calls are status checks. More than half of appeals are overturned."]], [30, 62, 88]),
      P("Money: revenue grew 9.3% in three years (to $112.4M) while clinical staff cost grew 27.7% and intake and call-center cost 23.7%. Operating margin fell from 14.0% to a forecast 8.0%. Riverbend service credits are $1.9M this year, about a fifth of forecast profit. Riverbend opened a Corrective Action Plan in July 2026 and its contract ends on 31 December 2026.", "b")]
D += Hd("2. Diagnosis, backed by the data pack")
D += [P("Leadership disagrees about the cause. I tested each claim against the files."),
      T([["Claim", "What the data shows", "Verdict"],
         ["VP Operations: it is a staffing problem.", "Nurse FTE fell from 57.7 to 50.6, but on-time rate does not move with it (weekly correlation -0.05). Riverbend MA standard decisions were 87.0% on time in Q1 2025 at 98% of budgeted staff. All 64 late MA standard decisions arrived incomplete.", "Mostly wrong"],
         ["VP Operations: overturns come from new information at appeal.", "Requests that arrived complete are overturned more often (56.7%) than incomplete ones (48.7%). Denials citing a retired policy version are overturned 91% of the time (30 of 33).", "Not supported"],
         ["Riverbend: it is a wrong-decision problem.", "QA audit: 68 of 120 decisions correct (56.7%) against a 95% standard. 39 of 52 errors are wrong-rule errors: a memo overriding policy (18), a retired version (14), a client plan rule missed (7).", "Supported"],
         ["Senior nurse: the hard part is which rules apply.", "34% of 2026 denials (94 of 274) cite a policy version already retired on the date of service. 72 lumbar MRI requests were denied under a void memo; 18 of 21 appeals were overturned.", "Supported"],
         ["Intake: a third of faxes are missing something.", "66 of 69 late decisions arrived incomplete. Requests that arrive complete are on time 99.8% of the time. Late cases spend 122 of 199 hours waiting for missing information.", "Supported"]], [44, 112, 24]),
      P("Sources: pa_requests_2025_2026.csv, qa_audit_sample_2026.csv, nurse_staffing_weekly.csv, call_center_log, GOV-01, UM-MEMO-2025-19, process documents. Caveat: the pack does not say the QA sample is random, so 56.7% is not extrapolated to all decisions; the request file independently shows the retired-version problem.", "cap")]
D += Hd("3. Priorities and business impact")
D += [T([["Rank", "Problem", "Evidence", "Impact", "Fix and pattern"],
         ["1", "<b>Wrong rule applied.</b> Reviewers cannot find which plan document, policy version or Medicare rule governs.", "QA accuracy 56.7% vs 95%. MA overturn rate 56.2% vs a 30% trigger. 14.2 of 38 minutes spent hunting rules.", "Contract risk with Riverbend and CMS audit exposure. Rule-hunting equals 18.9 of 50.6 nurse FTE.", "Governing-rule copilot. <b>Agentic RAG</b>. Built."],
         ["2", "<b>Clock lost at intake.</b> Fax, incomplete, days of waiting.", "66 of 69 late decisions arrived incomplete. MA timeliness 90.1% vs 97%.", "Direct cause of the $1.9M credits and the Corrective Action Plan.", "Completeness check and fax-back draft at receipt. <b>AI agent</b> step. Built as a slice."],
         ["3", "<b>No visibility.</b> Providers phone for status; employers get a quarterly PDF.", "67% of calls ask where a request is. 20% abandoned.", "Call-center cost, Harlan renewal ($8.1M a year).", "Status lookup, requirements assistant (plain RAG). Later."]], [10, 46, 46, 42, 36]),
      P("Problem 1 is first because it is the only fix that makes Bellcourt both faster and more defensible, which is the CEO's brief; it is the cause Riverbend named; and its rule engine is the foundation for the other two. Problem 2 drives the credits, so the build includes its highest-value slice: catching incompleteness in the first minute instead of after 17 hours.")]
D += Hd("4. The solution and where it fits")
D += [P("<b>Bellcourt Review Copilot</b> runs beside PACE and never writes to it. For each request it (1) reads the request, including un-keyed fax images; (2) checks completeness and drafts a fax-back listing exactly what is missing; "
        "(3) confirms eligibility and starts the clock from receipt; (4) selects the governing documents in code; (5) lets the model plan what to read and check each criterion with an exact quote; (6) verifies the answer; (7) hands a recommendation to a person."),
      architecture(CW), P("Architecture. Blue boxes call the model, white boxes are code, green is the human decision. Full-page version: docs/Architecture_Diagram.pdf.", "cap"),
      T([["Design decision", "Why"],
         ["Rule selection is code, not the model", "The failure at Bellcourt is choosing the wrong version. Versions 1 and 2 of a policy are near-identical text and the void memo looks highly relevant, so similarity search alone would repeat the error. A registry with effective dates and authority rank (GOV-01) decides; the model can only read documents that are in force."],
         ["Agentic, but bounded", "The model plans its own retrieval and follows cross-references (plan section to amendment, policy to MP-117). The loop is capped, a safety net always reads exclusions and amendments, and a verifier rejects bad citations, invented quotes and inconsistent outcomes."],
         ["Four outcomes, no denial", "Approve-ready, need information, route to physician, route as not covered. Required by the Riverbend addendum and state law. A second, skeptical model pass checks every approval because a wrong approval is the error no human would catch."],
         ["Provider text is untrusted", "Fax and note text is data. Planted instructions are flagged, cannot be used as evidence, and do not change the outcome."]], [48, 132])]
D += Hd("5. Evidence it works")
D += [T([["Test", "Data", "Result"],
         ["Agreement with the QA auditor", "120 audited cases with the auditor's correct decision", f"<b>{S['tool_correct']} of {S['n']} ({pct(S['tool_correct'], S['n'])})</b>. Original human decisions: {S['human_correct']} of {S['n']} ({pct(S['human_correct'], S['n'])})"],
         ["Cases humans got wrong for a wrong-rule reason", "Memo conflict, retired version, client rule missed", f"{by['MEMO_CONFLICT'][0]} of {by['MEMO_CONFLICT'][1]}, {by['OUTDATED_POLICY_VERSION'][0]} of {by['OUTDATED_POLICY_VERSION'][1]}, {by['CLIENT_RULE_MISSED'][0]} of {by['CLIENT_RULE_MISSED'][1]}"],
         ["Governing document and version", "Same 120 cases", f"{S['source_correct']} of {S['n']} correct"],
         ["Wrongful approvals / denials issued", "Same 120 cases", f"{len(S['wrong_approvals'])} wrongful approvals. {S['outside_allowed']} denials (not possible by design)"],
         ["Open queue", "30 live cases incl. 13 fax images, against my answer key", f"{SC['matched']} of {SC['total']}. Misses fall on the cautious side"],
         ["Adversarial, incomplete, wrong inputs", "Planted instructions (10), policy time-travel (7), missing data and bad inputs (7)", f"{S['adversarial_passed']} of {S['adversarial_total']} pass. The one failure ended in manual review, not a wrong answer"],
         ["Deterministic unit tests", "Resolver, clock, eligibility, de-identification, verifier", "27 of 27 pass"]], [52, 62, 66]),
      P(f"Model: {S['model']} through OpenRouter, about {S['avg_latency']} seconds and a third of a US cent per case. Limits: results vary slightly between runs (27 to 29 of 30 on the open queue across runs); prompts were tuned while looking at these cases, so a fresh audit sample is the right next test; only 6 of 38 employer plan documents were in the pack. Full tables: docs/EVIDENCE.md and the Evidence tab of the app.", "cap")]
D += Hd("6. Success metrics")
D += [T([["Measure", "Today", "Target", "How measured"],
         ["Riverbend audit accuracy", "72% on MA cases in the QA sample", "At least 95%", "Monthly QA audit"],
         ["MA appeal overturn rate", "56.2%", "Under 30%", "Appeals file"],
         ["MA standard decisions on time", "90.1% (Q2 2026)", "At least 97%", "Clock from receipt, not keying"],
         ["Denials citing a retired policy version", "34% of 2026 denials", "Zero", "Audit log"],
         ["Nurse minutes per case", "38.0, of which 14.2 finding rules", "About 25", "Repeat the time study"],
         ["Hours from fax receipt to missing-information request", "About 17 before keying", "Under 1", "Audit log timestamps"],
         ["Adverse decisions made by the tool", "n/a", "Zero, always", "Audit log and tests"]], [58, 48, 30, 44])]
D += Hd("7. Compliance and risk")
D += [T([["Rule", "Source", "How the design meets it"],
         ["No tool may deny, delay or modify a request; a qualified human makes every adverse decision", "Riverbend addendum s5; CEO brief", "No denial outcome exists. The fax-back is a draft a person sends. Tests assert zero denials."],
         ["60 days' written notice before any AI tool is used", "Riverbend addendum s5", "Send notice on day 0. Pilot on self-funded plans (ERISA; state AI laws do not bind them) while the notice runs."],
         ["Produce inputs and outputs for any case on audit", "Riverbend addendum s5", "Per-run audit record: inputs, sources and versions, tool trace, output, verifier report, human decision."],
         ["Arizona: licensed medical director signs denials. Texas: disclose AI use. Georgia: human review before denial", "Addendum s4; REG-02", "State flags route Arizona cases to a licensed director and add the Texas disclosure to the letter draft."],
         ["Patient data is PHI", "IT interview; HIPAA", "Name, DOB, phone, record number and member ID are removed before the review step. Production runs inside the Azure tenant under the existing agreement."],
         ["Provider content is outside Bellcourt's control", "Pack README; intake interview", "Treated as data; planted instructions flagged and ignored (10 of 10 in tests, plus faxes 8106 and 8120)."]], [62, 36, 82]),
      P("Main risks: model error (mitigated by code-selected rules, verifier, second check, human decision); stale registry (mitigated by making registry updates part of the Clinical Policy Committee release and the plan-amendment process); over-reliance (mitigated by showing evidence quotes and the excluded documents, and by monthly QA on tool-assisted cases).", "b")]
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
         ["Model", f"{S['model']} via OpenRouter", "Fast (about 6 seconds a case), cheap (about $0.004 a case), reads fax images. One environment variable swaps the model; I tested Claude models too.", "A model hosted in the Azure tenant under the existing agreement"],
         ["Agent loop", "Three to five calls: plan retrieval, review, verifier fixes, second check on approvals", "Bounded and fully logged. Every step is visible in the audit trail.", "Same"],
         ["Verifier", "Plain code", "Citations must be in force, quotes must exist in the record, outcome must match the checklist, arithmetic on visit limits is recomputed. The model cannot talk its way past code.", "Same"],
         ["Backend", "Python standard library only, two serverless functions", "Zero dependencies means nothing to break at deploy time and a tiny attack surface.", "Azure Functions or a container"],
         ["Screen", "One static HTML page", "Loads saved results with no key, so the public demo cannot spend credit; live mode when a key is set.", "Embedded next to PACE with single sign-on and role-based access"],
         ["Evidence", "Scripts that write JSON and the PDFs from the same run", "Numbers in the documents cannot drift from the numbers in the app.", "Monthly QA job"]], [26, 44, 70, 40]),
      Spacer(1, 6), P("<b>What I would change with more time:</b> a database-backed audit log instead of browser storage; a fresh held-out audit sample; a stronger model for the review step if the fresh sample shows drift; plan documents for the other 32 employers.")]
build("Implementation_Strategy_and_Design_Note.pdf", I, "Implementation strategy and design note")

# ================================================================ 4. EVIDENCE.md
L = ["# Evidence it works", "", f"Model `{S['model']}`. Generated by `scripts/run_open.py` and `scripts/run_eval.py`. Raw results: `public/data/*.json`.", "",
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
     "## 4. Deterministic tests", "", "`python -m pytest -q` runs 27 tests with no model call: version by date of service, excluded documents, read-tool refusal, eligibility, clock, de-identification, planted-text detection, every verifier check, and no denial in saved results.", "",
     "## Honest limits", "", "- Results vary slightly between runs because the model is not fully deterministic. Across runs the open queue scored 27 to 29 of 30. Misses were on the cautious side (manual review, need information or physician referral).",
     "- Prompts were tuned while looking at these cases. The right next test is a fresh, random audit sample.", "- The open-case answer key is my reading of the policies, not an official key.", "- Only 6 of 38 employer plan documents are in the pack."]
open(os.path.join(DOCS, "EVIDENCE.md"), "w").write("\n".join(L) + "\n")
from pypdf import PdfReader
for f in ("Bellcourt_Case_Documentation.pdf", "Implementation_Strategy_and_Design_Note.pdf", "Architecture_Diagram.pdf"): print(f, len(PdfReader(os.path.join(DOCS, f)).pages), "pages")
