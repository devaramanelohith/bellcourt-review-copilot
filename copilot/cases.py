"""Case lifecycle: create (form, file, fax or PDF upload) -> review -> human decision -> decision letter. Every step is recorded.
Who may do what is decided here and checked on every request:
  provider  raises requests for its own patients and sees only their status;   intake  raises requests from the fax share and phone, runs the review, pends or routes;
  nurse     runs the review and approves, pends or routes (never raises a case: the person who decides does not create the record);
  physician decides every adverse determination;   agent  looks up status for callers after verifying identity;   auditor  reads everything, changes nothing."""
import os, json, time, base64, tempfile, glob
from . import core, store, pipeline, agent, letters, auth

NOW = lambda: time.strftime("%Y-%m-%d %H:%M:%S")
RECEIVED = core.DEMO_NOW.strftime("%Y-%m-%d %H:%M")          # demo clock is pinned, so new cases are stamped at the demo "now"
DECISIONS = {  # decision -> (roles allowed, resulting status, creates a letter)
    "APPROVED": ({"nurse", "physician"}, "DECIDED", True), "PENDED_INFO": ({"intake", "nurse", "physician"}, "PENDED", True),
    "ROUTED_PHYSICIAN": ({"nurse", "intake"}, "ROUTED", False), "DENIED_MEDICAL_NECESSITY": ({"physician"}, "DECIDED", True), "DENIED_NOT_COVERED": ({"physician"}, "DECIDED", True)}
CAN_CREATE = {"intake", "provider"}
# Only a handful of cases are preloaded, one per kind of outcome. Everything else is raised by a user (fax, file or form) and reviewed on demand.
SAMPLE_IDS = ("PA-2609-8113", "PA-2609-8106", "PA-2609-8100", "PA-2609-8105", "PA-2609-8118")
_seed = None
def seeds():
    """A few sample cases from the data pack, shown as if imported from PACE and the fax share, with their saved reviews."""
    global _seed
    if _seed is None:
        raws = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(core.D, "open_cases", "*.json"))}
        _seed = {}
        for rv in json.load(open(os.path.join(core.D, "results", "open_cases.json"))):
            cid = rv["case"]["case_id"]
            if cid not in SAMPLE_IDS: continue
            rv["case"]["patient_name"] = raws[cid].get("patient_name") or (rv["case"].get("fax") or {}).get("patient_name")
            _seed[cid] = dict(id=cid, status="REVIEWED", raw=raws[cid], review=rv, decision=None, letter_id=None, seeded=True,
                              created=dict(by="System import", user=None, ts=raws[cid]["received_ts"], source={"FAX": "Fax share", "PORTAL": "Portal webhook", "PHONE": "PACE (phone)", "ELECTRONIC": "PACE (X12 278)"}[raws[cid]["channel"]]))
    return _seed
def priority(c):
    rv = c.get("review"); clk = rv["clock"] if rv else core.clock(c["raw"]["client_id"], c["raw"]["received_ts"], c["raw"].get("urgency"), c["raw"].get("urgency_form"))
    h = clk["hours_remaining"]; p = "OVERDUE" if h < 0 else "URGENT" if (clk["effective_urgency"] == "URGENT" or h < 24) else "DUE_SOON" if h < 96 else "STANDARD"
    return dict(level=p, hours_remaining=h, due=clk["due"], rank={"OVERDUE": 0, "URGENT": 1, "DUE_SOON": 2, "STANDARD": 3}[p])
def all_cases():
    d = dict(seeds()); d.update(store.all("case"))
    out = []
    for c in d.values(): c = dict(c); c["priority"] = priority(c); out.append(c)
    return sorted(out, key=lambda c: (c["status"] in ("DECIDED",), c["priority"]["rank"], c["priority"]["hours_remaining"]))
def get(cid):
    c = store.get("case", cid) or seeds().get(cid)
    if c: c = dict(c); c["priority"] = priority(c)
    return c
def audit(sess, action, case_id, detail=""):
    store.put("audit", f"{time.time():.4f}", dict(ts=NOW(), user=sess["u"], name=sess["n"], role=sess["r"], action=action, case_id=case_id, detail=detail))

# ---------------------------------------------------------------- what a provider or a caller may be told
PUBLIC = {"NEW": ("RECEIVED", "Received. In the review queue."), "REVIEWED": ("IN_REVIEW", "Under clinical review."), "ROUTED": ("IN_REVIEW", "Under physician review."),
          "PENDED": ("INFO_NEEDED", "Waiting for information from the provider."), "DECIDED": ("DECIDED", "Decided. See the notice.")}
def public_view(c):
    """Status only: no recommendation, no rationale, no model output. Missing items and the decision notice are the provider's business; the review is not."""
    k = c["raw"]; rv = c.get("review"); d = c.get("decision"); st, label = PUBLIC[c["status"]]
    missing = list(c.get("intake_gaps") or (rv and rv.get("intake_gaps")) or [])
    if c["status"] == "PENDED" and rv: missing = list(dict.fromkeys(missing + list(rv["result"].get("missing_information") or [])))
    if d and d["type"].startswith("DENIED"): label = "Denied. The notice explains the reason and how to appeal."
    elif d and d["type"] == "APPROVED": label = "Approved."
    elif d and d["type"] == "PENDED_INFO": label = "Information requested. See the notice for the list."
    pre = c.get("precheck")
    return dict(id=c["id"], public=True, status=st, label=label, received_ts=k["received_ts"], channel=k["channel"], client_id=k.get("client_id"), service=k.get("service_requested") or (rv and rv["case"].get("service_requested")),
                date_of_service=k.get("date_of_service"), patient_name=k.get("patient_name"), member_id=k.get("member_id"), urgency=k.get("urgency"), due=c["priority"]["due"], hours_remaining=c["priority"]["hours_remaining"],
                missing=missing, decision=d and dict(type=d["type"], ts=d["ts"]), letter_id=c.get("letter_id") if d else None, created=c["created"],
                precheck=pre and dict(status=pre["verdict"]["status"], headline=pre["verdict"]["headline"], policy=pre.get("policy") and f"{pre['policy']['doc_id']} {pre['policy']['version']}", plan=pre.get("plan") and pre["plan"]["doc_id"],
                                      provisions=[f"{p['doc_id']} §{p['section']} ({p['kind'].lower()})" for p in pre.get("provisions") or []]))
def own(sess): return [public_view(c) for c in all_cases() if (c.get("created") or {}).get("user") == sess["u"]]
def lookup(sess, cid, dob):
    """Status desk: the caller must give the case number AND the patient's date of birth before anything is disclosed."""
    c = get((cid or "").strip().upper())
    if not c: raise ValueError("No request with that number.")
    rv = c.get("review") or {}; fx = (c["raw"].get("fax") or (rv.get("case") or {}).get("fax") or {})
    want = core.to_date(c["raw"].get("patient_dob") or (rv.get("case") or {}).get("patient_dob") or fx.get("date_of_birth")); got = core.to_date(dob)
    if not want: raise ValueError("This request has no date of birth on file, so identity cannot be verified by phone. Ask the provider to use the portal.")
    if not got or got != want: audit(sess, "STATUS_LOOKUP_FAILED", c["id"], "date of birth did not match"); raise PermissionError("Date of birth does not match. Nothing disclosed.")
    audit(sess, "STATUS_LOOKUP", c["id"], "identity verified by date of birth"); return public_view(c)

def create(sess, b):
    """source: form | json | text | fax (image as data URL; a PDF is rendered to an image in the browser first)."""
    if sess["r"] not in CAN_CREATE: raise PermissionError("Only intake coordinators and provider offices raise requests. Reviewers decide; they do not create the record.")
    src = b.get("source", "form"); existing = store.all("case"); n = len(existing) + 1; cid = f"PA-2610-{9000 + n}"; image = None
    base = dict(case_id=cid, received_ts=RECEIVED, urgency="STANDARD", requesting_provider="", client_id="", source=src)
    if src == "json":
        j = b.get("case") or {}; raw = {**base, **{k: j.get(k) for k in ("channel", "urgency", "client_id", "requesting_provider", "member_id", "patient_name", "patient_dob", "date_of_service", "service_code", "service_requested", "clinical_notes", "icd10") if j.get(k)}}
        raw.setdefault("channel", "PORTAL"); raw["imported_from"] = j.get("case_id")
        if j.get("received_ts"): raw["received_ts"] = j["received_ts"]                       # keep the original receipt time so the clock is right
        jid = str(j.get("case_id") or "")
        if jid.startswith("PA-") and jid not in existing and jid not in seeds(): cid = jid; raw["case_id"] = jid
        if j.get("fax_image") and not j.get("clinical_notes"): raw["fax_image"] = j["fax_image"]; raw["channel"] = "FAX"     # an un-keyed fax case from the pack
    elif src in ("fax", "text"):
        if src == "fax":
            image = b.get("image") or ""; data = base64.b64decode(image.split(",", 1)[-1]); tmp = tempfile.NamedTemporaryFile(suffix=".img", delete=False); tmp.write(data); tmp.close()
            fx, _ = agent.read_fax(tmp.name); os.unlink(tmp.name)
        else: fx, _ = agent.read_text(str(b.get("text", "")))
        raw = {**base, "channel": "FAX" if src == "fax" else str(b.get("channel") or "PORTAL"), "client_id": b.get("client_id") or "", "fax": fx, "planted": list(fx.get("embedded_instructions") or []),
               "urgency_form": (fx.get("review_type") or "").upper() or None, "urgency": (fx.get("review_type") or "STANDARD").upper(), "member_id": (fx.get("member_id") or "").strip() or None,
               "patient_name": fx.get("patient_name"), "patient_dob": fx.get("date_of_birth") or None, "requesting_provider": fx.get("requesting_provider") or "",
               "service_requested": fx.get("service_requested"), "service_code": core.service_code_for(fx.get("service_requested")), "icd10": (fx.get("icd10") or "").strip() or None,
               "clinical_notes": fx.get("clinical_text") or "", "date_of_service": str(core.to_date(fx.get("planned_date_of_service")) or "") or None}
    else:
        f = b.get("form") or {}; raw = {**base, **{k: (str(f.get(k)).strip() or None) if f.get(k) is not None else None for k in ("channel", "urgency", "client_id", "requesting_provider", "member_id", "patient_name", "patient_dob", "date_of_service", "service_code", "clinical_notes", "icd10")}}
        raw["channel"] = raw.get("channel") or "PORTAL"; raw["urgency"] = raw.get("urgency") or "STANDARD"
    if sess["r"] == "provider":
        raw["channel"] = "FAX" if src == "fax" else "PORTAL"; raw["requesting_provider"] = raw.get("requesting_provider") or sess["n"]
    if not raw.get("client_id") and raw.get("member_id") in core.ELIG: raw["client_id"] = core.ELIG[raw["member_id"]]["client_id"]     # client from the member ID
    if raw.get("service_code") and not raw.get("service_requested"): raw["service_requested"] = core.SERVICES.get(raw["service_code"])
    c = dict(id=cid, status="NEW", raw=raw, review=None, decision=None, letter_id=None, image=image, created=dict(by=sess["n"], user=sess["u"], role=sess["r"], ts=NOW(), source={"form": "Form", "json": "Case file upload", "fax": "Fax or PDF upload", "text": "Text document upload"}[src]),
             intake_gaps=core.intake_gaps(raw) + ([] if raw.get("client_id") else ["Health plan or employer (client)"]))
    try: c["precheck"] = core.coverage_check(raw.get("member_id"), raw.get("client_id"), raw.get("service_code"), raw.get("date_of_service"), raw.get("urgency")) if raw.get("client_id") else None
    except Exception: c["precheck"] = None
    store.put("case", cid, c); audit(sess, "CASE_CREATED", cid, c["created"]["source"] + (f"; intake check missing: {', '.join(c['intake_gaps'])}" if c["intake_gaps"] else "; complete on receipt")); return get(cid)

def review(sess, cid, client_id=None):
    if sess["r"] not in auth.CAN_RUN_LIVE: raise PermissionError("Your role cannot run a review.")
    c = get(cid)
    if not c: raise ValueError("unknown case")
    if client_id and not c["raw"].get("client_id") and client_id in core.PLAN_CLIENTS: c["raw"]["client_id"] = client_id
    if not c["raw"].get("client_id"): raise ValueError("Set the client (health plan or employer) before running a review.")
    rv = pipeline.run_case(c["raw"]); rv["case"]["patient_name"] = c["raw"].get("patient_name") or (rv["case"].get("fax") or {}).get("patient_name")
    c.update(review=rv, status="REVIEWED", decision=None, letter_id=None, reviewed=dict(by=sess["n"], ts=NOW())); c.pop("priority", None); c.pop("seeded", None)
    store.put("case", cid, c); audit(sess, "REVIEW_RUN", cid, rv["result"]["outcome"]); return get(cid)

def decide(sess, cid, decision, note="", dry=False):
    c = get(cid)
    if not c or not c.get("review"): raise ValueError("Run a review before recording a decision.")
    if decision not in DECISIONS: raise ValueError("unknown decision")
    roles, status, makes_letter = DECISIONS[decision]
    if sess["r"] not in roles: raise PermissionError(f"Your role cannot record this decision. Allowed: {', '.join(sorted(roles))}.")
    rec = c["review"]["result"]["outcome"]; expected = {"APPROVED": "APPROVE_READY", "PENDED_INFO": "NEED_INFO", "ROUTED_PHYSICIAN": "ROUTE_PHYSICIAN", "DENIED_MEDICAL_NECESSITY": "ROUTE_PHYSICIAN", "DENIED_NOT_COVERED": "ROUTE_NOT_COVERED"}[decision]
    override = rec != expected and not (decision == "ROUTED_PHYSICIAN" and rec == "ROUTE_NOT_COVERED")
    if override and not (note or "").strip(): raise ValueError("This differs from the recommendation. A reason is required.")
    if dry: return dict(ok=True, dry=True, decision=decision, override=override)
    c["decision"] = dict(type=decision, by=sess["n"], user=sess["u"], role=sess["r"], ts=NOW(), note=note, override=override, recommended=rec); c["status"] = status
    if makes_letter:
        L = letters.build(c, decision, sess["n"], auth.ROLES[sess["r"]]); L.update(id=f"L-{cid[3:]}-{int(time.time()) % 100000}", created_by=sess["n"], ts=NOW(), sent=None)
        store.put("letter", L["id"], L); c["letter_id"] = L["id"]
    c.pop("priority", None); c.pop("seeded", None); store.put("case", cid, c); audit(sess, "DECISION_" + decision, cid, ("OVERRIDE: " if override else "") + (note or "")); return get(cid)

def send_letter(sess, lid):
    L = store.get("letter", lid)
    if not L: raise ValueError("unknown letter")
    if sess["r"] not in auth.CAN_DECIDE: raise PermissionError("Your role cannot send letters.")
    to = letters.send(L); L["sent"] = dict(ts=NOW(), to=to, by=sess["n"]); store.put("letter", lid, L); audit(sess, "LETTER_SENT", L["case_id"], to); return L
