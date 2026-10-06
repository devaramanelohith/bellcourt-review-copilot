"""Deterministic core. No model calls here. This is the part that decides WHICH rules govern a case."""
import os, re, json, csv, math, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
REGISTRY = json.load(open(os.path.join(D, "registry.json")))
SECTIONS = json.load(open(os.path.join(D, "sections.json")))
try: VECTORS = json.load(open(os.path.join(D, "vectors.json")))
except Exception: VECTORS = None
ELIG = {r["member_id"]: r for r in csv.DictReader(open(os.path.join(D, "member_eligibility_extract.csv")))}
DEMO_NOW = dt.datetime.fromisoformat(os.environ.get("DEMO_NOW", "2026-09-26T09:00:00"))
SERVICES = {d["service_code"]: d["title"] for d in REGISTRY if d["doc_type"] == "policy" and d["service_code"]}
PLAN_CLIENTS = {c for d in REGISTRY for c in d.get("clients", [])}

def to_date(x):
    if not x: return None
    if isinstance(x, dt.date): return x
    x = str(x).strip()
    for f in ("%Y-%m-%d", "%m/%d/%Y"):
        try: return dt.datetime.strptime(x, f).date()
        except ValueError: pass
    return None

# ------------------------------------------------------------------ rule resolver (GOV-01 hierarchy)
def product(client_id): return {"RB-MA": "MA", "RB-ACA": "ACA"}.get(client_id, "SELF_FUNDED")

def _toc(doc_id, version):
    return [f"{s['section']} {s['title']}" for s in SECTIONS if s["doc_id"] == doc_id and s["version"] == version and s["section"] != "0"]

def governing_set(client_id, service_code, dos):
    """Documents that govern this case on its date of service, plus the documents deliberately excluded and why."""
    dos = to_date(dos); gov, exc = [], []
    if client_id not in PLAN_CLIENTS:
        raise ValueError(f"No plan document on file for client {client_id}. The tool does not guess coverage.")
    prod = product(client_id)
    def add(d, why): gov.append(dict(doc_id=d["doc_id"], version=d["version"], doc_type=d["doc_type"], rank=d["rank"], title=d["title"],
                                     effective_from=d["effective_from"], effective_to=d["effective_to"], why=why, sections=_toc(d["doc_id"], d["version"])))
    for d in REGISTRY:
        if d["doc_type"] == "regulation" and prod in d.get("products", []): add(d, f"Law summary for {prod} business (rank 1)")
    plan = next(d for d in REGISTRY if client_id in d.get("clients", []))
    add(plan, f"{'Delegation agreement' if prod != 'SELF_FUNDED' else 'Plan document'} for client {client_id} (rank 2)")
    policy_ids = set()
    for d in REGISTRY:
        if d["doc_type"] != "policy": continue
        if d["service_code"] == service_code:
            policy_ids.add(d["doc_id"])
            lo, hi = to_date(d["effective_from"]), to_date(d["effective_to"])
            if dos and lo <= dos and (hi is None or dos <= hi): add(d, f"Policy version in force on date of service {dos} (rank 3)")
            elif dos and hi and dos > hi: exc.append(dict(doc_id=d["doc_id"], version=d["version"], reason=f"Retired on {hi}, before the date of service"))
            elif dos: exc.append(dict(doc_id=d["doc_id"], version=d["version"], reason=f"Not effective until {lo}, after the date of service"))
        elif d["doc_id"] == "MP-117": add(d, "Applies to every service: experimental and investigational rule (rank 3)")
    for d in REGISTRY:
        if d["rank"] == 4 and (set(d.get("relates_to", [])) & (policy_ids | {plan["doc_id"]})):
            exc.append(dict(doc_id=d["doc_id"], version=None, reason="Memos and emails cannot change criteria (GOV-01 Section 1, rank 4)"))
    return gov, exc

def read_sections(requests, gov):
    """Return section text. Refuses documents that are not in the governing set. A parent number returns its subsections."""
    allowed = {(g["doc_id"], g["version"]) for g in gov}; out = []; seen = set()
    for r in requests:
        key = (r.get("doc_id"), r.get("version") or None); sec = str(r.get("section", "")).strip().rstrip(".")
        if key not in allowed:
            alt = next((v for (d_, v) in allowed if d_ == key[0]), "none")
            out.append(dict(doc_id=key[0], version=key[1], section=sec, error=f"REFUSED: {key[0]} {key[1] or ''} does not govern this case (in-force version: {alt})")); continue
        for s in SECTIONS:
            if s["doc_id"] == key[0] and s["version"] == key[1] and (s["section"] == sec or s["section"].startswith(sec + ".")):
                k = (key[0], key[1], s["section"])
                if k not in seen: seen.add(k); out.append(dict(doc_id=key[0], version=key[1], section=s["section"], text=s["text"]))
    return out

def mandatory_reads(gov):
    """Safety net: sections that must always be read, whatever the model chooses."""
    req = []
    for g in gov:
        if g["doc_type"] == "plan_document": req += [dict(doc_id=g["doc_id"], version=None, section=s) for s in ("4.2", "5.3", "5.6", "6", "8")]
        if g["doc_type"] == "delegation_agreement": req += [dict(doc_id=g["doc_id"], version=None, section=s) for s in ("2", "4")]
        if g["doc_type"] == "policy": req += [dict(doc_id=g["doc_id"], version=g["version"], section=s) for s in (("3", "4") if g["doc_id"] == "MP-117" else ("3", "4", "5"))]
    return req

# ------------------------------------------------------------------ hybrid search (keyword + vector), filtered by the governing set
_TOK = lambda t: re.findall(r"[a-z0-9]+", t.lower())
_DF = {}
for _s in SECTIONS:
    for _w in set(_TOK(_s["text"])): _DF[_w] = _DF.get(_w, 0) + 1
def search(query, gov=None, k=5, qvec=None):
    allowed = {(g["doc_id"], g["version"]) for g in gov} if gov else None
    q = _TOK(query); scored = []
    for i, s in enumerate(SECTIONS):
        if s["section"] == "0": continue
        toks = _TOK(s["text"]); n = len(toks) or 1
        kw = sum((toks.count(w) / n) * math.log(1 + len(SECTIONS) / _DF.get(w, 1)) for w in set(q))
        vec = 0.0
        if qvec and VECTORS:
            v = VECTORS[i]; vec = sum(a * b for a, b in zip(qvec, v)) / ((math.sqrt(sum(a * a for a in qvec)) * math.sqrt(sum(b * b for b in v))) or 1)
        scored.append((i, kw, vec))
    def ranks(idx): return {i: r for r, (i, *_ ) in enumerate(sorted(scored, key=lambda t: -t[idx]))}
    rk, rv = ranks(1), ranks(2)
    fused = sorted(scored, key=lambda t: -(1 / (60 + rk[t[0]]) + (1 / (60 + rv[t[0]]) if qvec and VECTORS else 0)))
    out = []
    for i, *_ in fused:
        s = SECTIONS[i]; governing = allowed is None or (s["doc_id"], s["version"]) in allowed
        out.append(dict(doc_id=s["doc_id"], version=s["version"], section=s["section"], title=s["title"], text=s["text"][:700],
                        status="GOVERNING" if governing else "NOT_GOVERNING"))
        if len(out) >= k: break
    return out

# ------------------------------------------------------------------ member, clock, state rules
def eligibility(member_id, client_id, dos, assume=False):
    if assume: return dict(status="ELIGIBLE", reason="Not in the audit file; assumed eligible", member_state=None)
    if not member_id: return dict(status="UNVERIFIED", reason="No member ID on the request", member_state=None)
    m = ELIG.get(member_id)
    if not m: return dict(status="UNVERIFIED", reason=f"Member ID {member_id} not found in the eligibility file", member_state=None)
    if m["client_id"] != client_id: return dict(status="UNVERIFIED", reason=f"Member belongs to {m['client_id']}, request says {client_id}", member_state=m["member_state"])
    dos = to_date(dos); lo, hi = to_date(m["coverage_start"]), to_date(m["coverage_end"])
    if dos and (dos < lo or (hi and dos > hi)):
        return dict(status="NOT_ELIGIBLE", reason=f"Coverage runs {lo} to {hi or 'open'}; date of service is {dos}", member_state=m["member_state"])
    return dict(status="ELIGIBLE", reason=f"Covered from {lo}" + (f" to {hi}" if hi else ""), member_state=m["member_state"])

def clock(client_id, received_ts, urgency_header, urgency_form=None):
    urgent = "URGENT" in (str(urgency_header).upper(), str(urgency_form).upper())
    hours = 72 if urgent else (168 if client_id == "RB-MA" else 360)
    due = dt.datetime.strptime(received_ts, "%Y-%m-%d %H:%M") + dt.timedelta(hours=hours)
    left = round((due - DEMO_NOW).total_seconds() / 3600, 1)
    return dict(sla_hours=hours, due=due.strftime("%Y-%m-%d %H:%M"), effective_urgency="URGENT" if urgent else "STANDARD", hours_remaining=left,
                conflict=bool(urgency_form) and str(urgency_form).upper() != str(urgency_header).upper())

def state_flags(client_id, state, outcome):
    f = []; adverse = outcome in ("ROUTE_PHYSICIAN", "ROUTE_NOT_COVERED")
    if client_id == "RB-MA" and state == "AZ" and outcome == "ROUTE_PHYSICIAN":
        f.append(dict(code="AZ_MD_SIGNOFF_REQUIRED", detail="Arizona: an Arizona-licensed medical director must personally review and sign any medical necessity denial (Addendum Section 4)."))
    if client_id == "RB-MA" and state == "TX":
        f.append(dict(code="TX_AI_DISCLOSURE", detail="Texas: the notice must disclose that an AI-assisted tool was used in the review (Addendum Section 4)."))
    if client_id == "RB-ACA" and adverse:
        f.append(dict(code="GA_HUMAN_REVIEW", detail="Georgia: human clinical review is required before any denial (REG-02)."))
    return f

# ------------------------------------------------------------------ intake helpers
def service_code_for(name):
    if not name: return None
    n = re.sub(r"[^a-z0-9]", "", name.lower()); best, score = None, 0
    for code, title in SERVICES.items():
        t = re.sub(r"[^a-z0-9]", "", title.lower())
        if n == t: return code
        a, b = set(_TOK(name)), set(_TOK(title)); j = len(a & b) / (len(a | b) or 1)
        if j > score: best, score = code, j
    return best if score >= 0.5 else None

def deidentify(notes):
    """Strip identifiers before any text goes to the review model: name, DOB, MRN, phone."""
    if not notes: return ""
    t = re.sub(r"^Pt .+? \(DOB [^)]*?ph \(\d{3}\) \d{3}-\d{4}\)\.\s*", "", notes)
    t = re.sub(r"\(?\d{3}\)?[ -]\d{3}-\d{4}", "[phone]", t); t = re.sub(r"MRN-?\d+", "[mrn]", t)
    t = re.sub(r"DOB:? ?\d{2}/\d{2}/\d{4}", "[dob]", t)
    return t.strip()

def age_on(dob, dos):
    a, b = to_date(dob), to_date(dos)
    return None if not (a and b) else b.year - a.year - ((b.month, b.day) < (a.month, a.day))

INJECTION = re.compile(r"(pre-?approved|mark (it |this )?approved|approve (it |this )?(today|now|immediately)|skip (the )?criteria|disregard|ignore (all |any |the |that |previous )|note to (the )?(automated|ai|review)|automated review system|system:|no longer (need|require)|criteria (are |is )?waived|override)", re.I)
def find_planted_text(text):
    return [s.strip() for s in re.split(r"(?<=[.!?\]])\s+", text or "") if INJECTION.search(s)]

def intake_gaps(case):
    """Completeness check at the moment of receipt. Deterministic."""
    gaps = []
    if not case.get("member_id"): gaps.append("Member ID")
    if not case.get("date_of_service"): gaps.append("Planned date of service")
    if not case.get("service_code"): gaps.append("Service requested (could not be matched to a covered service)")
    if not (case.get("clinical_notes") or "").strip(): gaps.append("Clinical notes supporting medical necessity")
    if case.get("channel") == "FAX" and not case.get("icd10"): gaps.append("Diagnosis code (ICD-10)")
    return gaps

def info_request_fax(case, missing, doc_requirements=""):
    """Draft of the fax-back to the provider. A person reviews and sends it; the tool never sends anything."""
    lines = [f"TO: {case.get('requesting_provider', 'Requesting provider')}", "FROM: Bellcourt Health Administrators, Utilization Management",
             f"RE: Prior authorization request {case['case_id']} received {case['received_ts']}", "",
             "We have received your request and it is in review. To complete the review we need the following:", ""]
    lines += [f"  {i}. {m}" for i, m in enumerate(missing, 1)]
    if doc_requirements: lines += ["", "For this service the policy asks for: " + doc_requirements]
    lines += ["", "Please fax the items to (615) 555-0142 and quote the request number above.",
              "Your request has not been denied. The decision clock continues to run from the original receipt time.", "",
              "DRAFT prepared with an AI-assisted tool. Reviewed and sent by Bellcourt intake staff."]
    return "\n".join(lines)

# ------------------------------------------------------------------ verifier
OUTCOMES = ("APPROVE_READY", "NEED_INFO", "ROUTE_PHYSICIAN", "ROUTE_NOT_COVERED")
_norm = lambda t: re.sub(r"[^a-z0-9 ]", "", re.sub(r"\s+", " ", (t or "").lower())).strip()
def verify(result, gov, record, planted):
    """Checks the model cannot talk its way around. Returns a list of errors (empty list = accepted)."""
    errs = []; allowed = {(g["doc_id"], g["version"]) for g in gov}; rec = _norm(record); bad = [_norm(p) for p in planted]
    if result.get("outcome") not in OUTCOMES: errs.append(f"V1 outcome must be one of {OUTCOMES}. A denial is not an available outcome.")
    checks = (result.get("coverage_checks") or []) + (result.get("criteria") or [])
    refs = [result.get("primary_source") or {}] + [c.get("source") or {} for c in checks]
    for r in refs:
        if (r.get("doc_id"), r.get("version") or None) not in allowed:
            errs.append(f"V2 {r.get('doc_id')} {r.get('version') or ''} is not in the governing list for this case. Cite only governing documents.")
    for c in checks:
        q = _norm(c.get("evidence_quote"))
        if c.get("status") in ("MET", "NOT_MET") and q and c.get("evidence_from", "record") == "record":
            parts = [p for p in (_norm(x) for x in re.split(r"\.\.\.|(?<=[.;!?])\s+", c.get("evidence_quote"))) if len(p) > 3]
            if q not in rec and not (parts and all(p in rec for p in parts)): errs.append(f"V3 quote not found in the clinical record: \"{c.get('evidence_quote')[:80]}\". Quote exactly or mark NOT_DOCUMENTED.")
            elif any(q in b or b in q for b in bad if b): errs.append("V3 evidence quote comes from text flagged as a planted instruction. It is not evidence.")
    o = result.get("outcome"); st = [c.get("status") for c in result.get("criteria") or []]
    cov_fail = any(c.get("status") == "NOT_MET" for c in result.get("coverage_checks") or [])
    if o == "APPROVE_READY" and (not result.get("criteria_logic_satisfied") or cov_fail): errs.append("V4 APPROVE_READY needs criteria_logic_satisfied true and no failed coverage check.")
    if o == "ROUTE_PHYSICIAN" and "NOT_MET" not in st: errs.append("V4 ROUTE_PHYSICIAN needs at least one criterion with status NOT_MET.")
    if o == "NEED_INFO" and not result.get("missing_information"): errs.append("V4 NEED_INFO needs missing_information listing what to request.")
    if o == "ROUTE_NOT_COVERED" and not cov_fail: errs.append("V4 ROUTE_NOT_COVERED needs a coverage check with status NOT_MET.")
    p = result.get("plan_limit_check")
    if p and all(isinstance(p.get(k), int) for k in ("used", "requested", "annual_limit")) and p["used"] + p["requested"] > p["annual_limit"] and o != "ROUTE_NOT_COVERED":
        errs.append(f"V6 {p['used']} used + {p['requested']} requested exceeds the plan limit of {p['annual_limit']}: outcome must be ROUTE_NOT_COVERED.")
    ps = result.get("primary_source") or {}   # V7: code guarantees the letter names its source
    cite = f"{ps.get('doc_id')} {ps.get('version') or ''}".strip() + f", Section {ps.get('section')}"
    if ps.get("doc_id") and str(ps.get("doc_id")) not in (result.get("letter_paragraph") or ""):
        result["letter_paragraph"] = (result.get("letter_paragraph") or "").rstrip() + f" (Source: {cite}.)"
    return errs

# ------------------------------------------------------------------ coverage pre-check (deterministic, no model)
SERVICE_KEYWORDS = {"BHA-IMG-0721": ["lumbar", "mri", "advanced imaging"], "BHA-SURG-4310": ["bariatric", "weight-loss", "obesity"], "BHA-DME-2103": ["glucose monitor", "cgm"],
                    "BHA-DX-9581": ["sleep study", "polysomnograph"], "BHA-SURG-2988": ["arthroscop"], "BHA-SURG-2744": ["knee replacement", "arthroplasty"], "BHA-LAB-8162": ["brca", "genetic test"],
                    "BHA-SURG-1582": ["eyelid", "blepharoplasty"], "BHA-SURG-3052": ["septoplasty", "rhinoplasty"], "BHA-SURG-6350": ["spinal cord stimulat", "spinal procedure", "neurostimulat"],
                    "BHA-VASC-3647": ["varicose", "vein ablation"], "BHA-THER-1830": ["hyperbaric"], "BHA-RAD-5205": ["proton beam"], "BHA-REH-9711": ["outpatient rehabilitation", "physical therapy", "therapy are limited"],
                    "BHA-IMG-7519": ["coronary", "angiograph"], "BHA-HH-0550": ["home health"], "BHA-DME-0601": ["cpap", "positive airway"]}
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
def _kind(section, text, dos=None):
    t = text.lower()
    if section.startswith("8") and "amendment" in t:
        m = re.search(rf"({MONTHS}) (\d{{1,2}}), (\d{{4}})", text); eff = dt.datetime.strptime(m.group(0), "%B %d, %Y").date() if m else None
        return "AMENDMENT" if (not eff or not dos or dos >= eff) else "AMENDMENT_NOT_YET"
    if re.search(r"covered only|covered subject to|must be documented|must be pended|requirement applies|take precedence|criteria to apply|must be applied", t): return "CONDITION"
    if re.search(r"limited to|per plan year|annual limit", t): return "LIMIT"
    if re.search(r"\bexcluded\b|is not covered|are not covered|not a covered", t): return "EXCLUSION_EXCEPT" if "except" in t else "EXCLUSION"
    return "MENTION"
def _short_title(t):
    w = re.sub(r"^\d+(\.\d+)?\s*", "", t).split()
    for i in range(1, len(w)):
        if w[i][:1].isupper() and w[i - 1].lower() not in ("of", "and", "the", "for", "to"): return " ".join(w[:i])
    return " ".join(w[:6])
def coverage_check(member_id, client_id, service_code, dos, urgency="STANDARD"):
    """What a provider office or a member-services agent can be told before a request is even filed: eligibility, whether the plan covers the
    service on that date, the policy version whose criteria will apply, the documents to send, and the decision clock. Rules only, no model."""
    out = dict(member_id=member_id or None, client_id=client_id or None, service_code=service_code, service=SERVICES.get(service_code), date_of_service=str(to_date(dos) or ""))
    m = ELIG.get((member_id or "").strip())
    if m and not client_id: client_id = out["client_id"] = m["client_id"]
    out["eligibility"] = eligibility((member_id or "").strip() or None, client_id, dos) if client_id else dict(status="UNVERIFIED", reason="No client and no known member ID", member_state=None)
    if not client_id or client_id not in PLAN_CLIENTS:
        out.update(verdict=dict(status="UNKNOWN", headline="No plan document on file", detail="The tool does not guess coverage. Set the health plan or employer."), plan=None, policy=None, excluded=[], provisions=[]); return out
    if not service_code or not to_date(dos):
        out.update(verdict=dict(status="UNKNOWN", headline="Service and date of service are needed", detail="Coverage and the policy version depend on both."), plan=None, policy=None, excluded=[], provisions=[]); return out
    gov, exc = governing_set(client_id, service_code, dos)
    plan = next(g for g in gov if g["doc_type"] in ("plan_document", "delegation_agreement")); pol = next((g for g in gov if g["doc_type"] == "policy" and g["doc_id"] != "MP-117"), None)
    keys = SERVICE_KEYWORDS.get(service_code, []); d_ = to_date(dos)
    prov = []
    for s in SECTIONS:
        if s["doc_id"] != plan["doc_id"] or s["section"] == "0" or s["section"] in ("1", "2", "3", "4", "4.1", "5", "5.1", "5.2", "5.4", "5.5", "6", "7"): continue
        tl = s["text"].lower()
        if any(k in tl for k in keys): prov.append(dict(doc_id=plan["doc_id"], section=s["section"], title=_short_title(s["title"]), kind=_kind(s["section"], s["text"], d_), excerpt=re.sub(r"\s+", " ", s["text"])[:420]))
    kinds = {p["kind"] for p in prov}
    if "AMENDMENT" in kinds: v = dict(status="COVERED_WITH_CONDITIONS", headline="Covered under a plan amendment", detail="A plan amendment deletes or changes the original wording and governs on this date of service. The original exclusion is shown for reference only.")
    elif "EXCLUSION" in kinds: v = dict(status="NOT_COVERED", headline="Not a covered benefit under this plan", detail="The plan document excludes this service" + (" (an amendment lifts it, but only for later dates of service)" if "AMENDMENT_NOT_YET" in kinds else "") + ". A request would go to a physician for a not-covered determination; medical necessity is not reached.")
    elif "EXCLUSION_EXCEPT" in kinds: v = dict(status="COVERED_WITH_CONDITIONS", headline="Excluded unless the plan's stated exception applies", detail="Read the cited section: the exclusion has an exception (for example an age limit) that decides coverage.")
    elif "CONDITION" in kinds or "LIMIT" in kinds: v = dict(status="COVERED_WITH_CONDITIONS", headline="Covered only if the plan's conditions are met", detail="The plan adds a condition or limit on top of the clinical criteria. Read the cited section before filing.")
    else: v = dict(status="COVERED_SUBJECT_TO_CRITERIA", headline="Covered, subject to the clinical criteria below", detail="No plan exclusion or limit mentions this service. The decision turns on the medical policy criteria in force on the date of service.")
    if out["eligibility"]["status"] == "NOT_ELIGIBLE": v = dict(status="NOT_ELIGIBLE", headline="Member not covered on that date", detail=out["eligibility"]["reason"])
    sec = lambda n: next((re.sub(r"\s+", " ", x["text"]) for x in SECTIONS if pol and x["doc_id"] == pol["doc_id"] and x["version"] == pol["version"] and x["section"] == n), "")
    docs = sec("5").split("If required documentation")[0]
    docs = re.sub(r"^5\.?\s*Documentation requirements\s*", "", docs).strip()
    out.update(verdict=v, plan=dict(doc_id=plan["doc_id"], title=plan["title"], rank=plan["rank"]), provisions=prov, excluded=exc,
               policy=pol and dict(doc_id=pol["doc_id"], version=pol["version"], title=pol["title"], effective_from=pol["effective_from"], effective_to=pol["effective_to"],
                                   criteria=re.sub(r"^3\.?\s*Coverage criteria\s*", "", sec("3"))[:900], limitations=re.sub(r"^4\.?\s*Not medically necessary / limitations\s*", "", sec("4"))[:500], documentation=docs[:500]),
               clock=dict(product=product(client_id), sla_hours=72 if str(urgency).upper() == "URGENT" else (168 if client_id == "RB-MA" else 360), starts="at receipt, on any channel"),
               checklist=["Member ID exactly as on the card", "Planned date of service", "Diagnosis code (ICD-10)", "Clinical notes that address each criterion"] + ([f"Policy documentation: {docs[:160]}"] if docs else []) +
                         [f"Plan condition ({p['doc_id']} §{p['section']}): {p['excerpt'][:140]}" for p in prov if p["kind"] in ("CONDITION", "LIMIT", "EXCLUSION_EXCEPT")])
    return out
