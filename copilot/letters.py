"""Decision letters: text, a dependency-free PDF, and optional email through Gmail SMTP. A letter is only ever created by a human decision."""
import os, ssl, smtplib, textwrap, time
from email.message import EmailMessage
from . import core

TITLES = {"APPROVED": "Notice of Approval", "PENDED_INFO": "Request for Additional Information", "DENIED_MEDICAL_NECESSITY": "Notice of Adverse Benefit Determination",
          "DENIED_NOT_COVERED": "Notice of Adverse Benefit Determination (Not a Covered Benefit)"}
def _cite(s): return f"{s.get('doc_id', '')} {s.get('version') or ''}".strip() + (f", Section {s.get('section')}" if s.get("section") else "")
def _appeal(client):
    who = "Riverbend Health Plan" if client.startswith("RB-") else "your employer's health plan"
    return [f"YOUR RIGHT TO APPEAL. You or your provider may appeal this decision within 180 days of this notice by writing to Bellcourt Health Administrators, Appeals Department, "
            f"or by calling the number on your member ID card. An appeal of a medical necessity decision is reviewed by a physician who was not involved in this decision. "
            f"If the appeal is not decided in your favor, you may ask for an external review. This plan is {who}.",
            "You may request, free of charge, a copy of the criteria and documents relied on for this decision."]

def build(case, decision, by_name, by_role_label):
    """Returns the letter dict. decision is APPROVED | PENDED_INFO | DENIED_MEDICAL_NECESSITY | DENIED_NOT_COVERED."""
    rv = case["review"]; c = rv["case"]; r = rv["result"]; ps = r.get("primary_source") or {}; flags = {f["code"] for f in rv.get("flags", [])}
    member = c.get("patient_name") or (c.get("fax") or {}).get("patient_name") or "Member"
    head = [f"Date: {time.strftime('%B %d, %Y')}", f"Reference: {c['case_id']}", f"Member: {member}" + (f" (ID {c['member_id']})" if c.get("member_id") else ""),
            f"Requesting provider: {c.get('requesting_provider') or 'on file'}", f"Service requested: {c.get('service_requested')}" + (f" ({c['service_code']})" if c.get("service_code") else ""),
            f"Planned date of service: {c.get('date_of_service') or 'not provided'}", ""]
    met = [x for x in (r.get("criteria") or []) if x.get("status") == "MET"]; notmet = [x for x in (r.get("criteria") or []) + (r.get("coverage_checks") or []) if x.get("status") == "NOT_MET"]
    body = []
    if decision == "APPROVED":
        body += [f"Dear {member},", "", f"We are pleased to tell you that the service above has been APPROVED as covered and medically necessary.", "",
                 f"Basis for the decision: the request meets the coverage criteria in {_cite(ps)}."] + [f"  - {x['criterion'][:160]}" for x in met[:6]] + ["",
                 "This approval is valid for the planned date of service and 90 days after it, provided you remain eligible under the plan. Approval is not a guarantee of payment; plan deductibles and coinsurance apply."]
    elif decision == "PENDED_INFO":
        body += [f"To: {c.get('requesting_provider') or 'Requesting provider'}", "", "We have received this request and it is in review. It has NOT been denied. To complete the review we need:", ""]
        body += [f"  {i}. {m}" for i, m in enumerate(r.get("missing_information") or rv.get("intake_gaps") or ["Supporting clinical documentation"], 1)]
        body += ["", "Please fax the items to (615) 555-0142 and quote the reference above. The decision clock continues to run from the original receipt time."]
    else:
        kind = "it is not a covered benefit under your plan. This is a coverage decision, not a judgement about your medical care" if decision == "DENIED_NOT_COVERED" else "it does not meet the medical necessity criteria that apply to your plan"
        body += [f"Dear {member},", "", f"After review by a licensed physician, the service above has been DENIED because {kind}.", "", "SPECIFIC REASON. " + (r.get("letter_paragraph") or r.get("rationale") or ""), "",
                 f"CRITERIA OR PLAN PROVISION RELIED ON: {_cite(ps)}."] + [f"  - Not met: {x['criterion'][:170]} ({_cite(x.get('source') or {})})" for x in notmet[:5]] + [""] + _appeal(c["client_id"])
    foot = ["", f"Decision made by: {by_name}, {by_role_label}, Bellcourt Health Administrators, Utilization Management."]
    if "TX_AI_DISCLOSURE" in flags or decision != "PENDED_INFO":
        foot.append("Disclosure: an AI-assisted tool was used to help prepare the review of this request. The decision was made by the person named above.")
    if "AZ_MD_SIGNOFF_REQUIRED" in flags and decision.startswith("DENIED"): foot.append("This determination was personally reviewed and signed by a medical director licensed in Arizona.")
    foot.append("Bellcourt Health Administrators is a fictional company. This letter is a training prototype and contains synthetic data.")
    return dict(type=decision, title=TITLES[decision], case_id=c["case_id"], to_name=member if decision != "PENDED_INFO" else (c.get("requesting_provider") or "Provider"),
                subject=f"{TITLES[decision]}: request {c['case_id']}", body="\n".join(head + body + foot), source=_cite(ps))

def _esc(s): return s.encode("latin-1", "replace").decode("latin-1").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
def to_pdf(letter):
    """Minimal single-font PDF writer (Helvetica), no dependencies."""
    lines = [("B", "Bellcourt Health Administrators"), ("N", "Utilization Management  |  Nashville, Tennessee"), ("N", ""), ("B", letter["title"]), ("N", "")]
    for para in letter["body"].split("\n"): lines += [("N", l) for l in (textwrap.wrap(para, 96, subsequent_indent="    " if para.startswith("  ") else "") or [""])]
    pages = [lines[i:i + 52] for i in range(0, len(lines), 52)]; objs = []
    def add(b): objs.append(b); return len(objs)
    add(b""); add(b""); f1 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"); f2 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"); kids = []
    for pg in pages:
        y = 760; s = ["BT"]
        for i, (st, t) in enumerate(pg):
            size = 15 if (st == "B" and t == letter["title"]) else 10.5
            s.append(f"/F{2 if st == 'B' else 1} {size} Tf 1 0 0 1 54 {y} Tm ({_esc(t)}) Tj"); y -= 13.5 if size < 12 else 20
        s.append("ET"); data = "\n".join(s).encode("latin-1")
        cid = add(b"<< /Length %d >>\nstream\n" % len(data) + data + b"\nendstream")
        kids.append(add(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents %d 0 R /Resources << /Font << /F1 %d 0 R /F2 %d 0 R >> >> >>" % (cid, f1, f2)))
    objs[0] = b"<< /Type /Catalog /Pages 2 0 R >>"; objs[1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (b" ".join(b"%d 0 R" % k for k in kids), len(kids))
    out = b"%PDF-1.4\n"; offs = []
    for i, o in enumerate(objs, 1): offs.append(len(out)); out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    x = len(out); out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offs)
    return out + b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x)

def mail_ready(): return bool(os.environ.get("GMAIL_USER") and os.environ.get("GMAIL_APP_PASSWORD"))
def send(letter):
    """Emails the letter with the PDF attached. In this demo every letter goes to LETTER_TO_EMAIL (default: the sending account), never to a real patient."""
    if not mail_ready(): raise RuntimeError("Email is not configured on the server (GMAIL_USER and GMAIL_APP_PASSWORD).")
    user = os.environ["GMAIL_USER"]; to = os.environ.get("LETTER_TO_EMAIL") or user
    m = EmailMessage(); m["From"] = f"Bellcourt UM (demo) <{user}>"; m["To"] = to; m["Subject"] = "[DEMO] " + letter["subject"]
    m.set_content(f"Demo delivery for: {letter['to_name']}\n\n" + letter["body"]); m.add_attachment(to_pdf(letter), maintype="application", subtype="pdf", filename=f"{letter['case_id']}_{letter['type']}.pdf")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context(), timeout=25) as s: s.login(user, os.environ["GMAIL_APP_PASSWORD"].replace(" ", "")); s.send_message(m)
    return to
